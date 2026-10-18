"""Wait for real connectivity after boot; retry only transient Git failures."""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime

from source_transport import BASE, SourceError, atomic_write, request

TRANSIENT = ("could not resolve host", "could not resolve hostname", "temporary failure",
             "failed to connect", "connection timed out", "connection reset", "connection refused",
             "network is unreachable", "remote end hung up", "http 429", "error: 429",
             "error: 500", "error: 502", "error: 503", "error: 504", "tls connection")


def wait_for_network(timeout: float = 120) -> None:
    deadline = time.monotonic() + timeout
    attempts = 0
    while True:
        attempts += 1
        error = None
        try:
            request("https://github.com/", attempts=1)
        except SourceError as exc:
            error = exc
        report = {"checked_at": datetime.now().astimezone().isoformat(), "attempts": attempts,
                  "status": "ready" if error is None else "waiting", "error": str(error) if error else None}
        remaining = deadline - time.monotonic()
        if error and (remaining <= 0 or not error.retryable):
            report["status"] = "failed"
        atomic_write(BASE / ".locks/network-readiness.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        if error is None:
            print(f"Network ready (attempts={attempts})", flush=True)
            return
        if report["status"] == "failed":
            raise error
        print("Waiting for GitHub connectivity before collection/publication", flush=True)
        time.sleep(min(10, remaining))


def retry_output(command: list[str], **kwargs) -> str:
    """Only for idempotent git fetch/push, never commit or workflow dispatch."""
    for attempt in range(3):
        try:
            return subprocess.check_output(command, stderr=subprocess.PIPE, **kwargs)
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr or ""
            if isinstance(detail, bytes):
                detail = detail.decode("utf-8", "replace")
            if attempt == 2 or not any(marker in detail.lower() for marker in TRANSIENT):
                raise RuntimeError(f"Git network operation failed: {detail.strip() or exc}") from exc
            print(f"Transient Git network failure; retry {attempt + 2}/3", flush=True)
            time.sleep(2 ** (attempt + 1))
        except subprocess.TimeoutExpired:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))
    raise AssertionError("unreachable")
