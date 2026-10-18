"""Bounded retries for public sources, with actionable persistent diagnostics."""
from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


class SourceError(RuntimeError):
    def __init__(self, message: str, kind: str = "parse", retryable: bool = False):
        super().__init__(message)
        self.kind = kind
        self.retryable = retryable


def request(url: str, *, method: str = "GET", attempts: int = 2, **kwargs) -> bytes:
    """Retry only connection failures, timeouts, 429 and server errors.

    POST is used only for the magazines' public, read-only search endpoints.
    """
    for attempt in range(attempts):
        try:
            with requests.request(method, url, headers={"User-Agent": UA},
                                  timeout=(5, 15), **kwargs) as response:
                if response.status_code >= 400:
                    raise SourceError(f"HTTP {response.status_code}", "http",
                                      response.status_code == 429 or response.status_code >= 500)
                if not response.content:
                    raise SourceError("Empty response", "empty")
                return response.content
        except requests.exceptions.SSLError as exc:
            error = SourceError(str(exc)[:300], "tls", False)
        except requests.ConnectTimeout:
            error = SourceError("Connection timeout (5 seconds)", "network", True)
        except requests.ReadTimeout:
            error = SourceError("Response timeout (15 seconds)", "network", True)
        except (requests.ConnectionError, requests.Timeout) as exc:
            detail = str(exc)
            if any(word in detail.lower() for word in ("name resolution", "nameresolutionerror", "getaddrinfo")):
                detail = "DNS resolution failed"
            error = SourceError(detail[:300], "network", True)
        except requests.RequestException as exc:
            error = SourceError(str(exc)[:300], "request")
        except SourceError as exc:
            error = exc
        print(json.dumps({"url": url, "attempt": attempt + 1, "error": str(error),
                          "kind": error.kind, "retryable": error.retryable}, ensure_ascii=False), flush=True)
        if not error.retryable or attempt + 1 == attempts:
            raise error
        time.sleep(2 ** (attempt + 1))
    raise AssertionError("attempts must be positive")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
        temporary = Path(file.name)
        try:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def save_report(collector: str, sources: list[dict]) -> None:
    target = BASE / "data/reports/collectors" / f"{collector}.json"
    try:
        previous = {row["name"]: row for row in json.loads(target.read_text())["sources"]}
    except (OSError, ValueError, KeyError):
        previous = {}
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    for row in sources:
        old = previous.get(row["name"], {})
        success = row["status"] == "success"
        retired = row["status"] == "retired"
        failures = 0 if success else (old.get('consecutive_failures') or 0) + 1
        row.update(checked_at=now,
                   last_success=now if success else old.get("last_success"),
                   consecutive_failures=None if retired else failures)
        if retired:
            row['failures_before_retirement'] = old.get('failures_before_retirement', old.get('consecutive_failures', 0))
        print(json.dumps(row, ensure_ascii=False), flush=True)
    # Batches retain prior observations with their original timestamps.
    sources = list({**previous, **{row['name']: row for row in sources}}.values())
    active = [row for row in sources if row['status'] != 'retired']
    status = 'retired' if sources and not active else ('success' if active and all(
        row['status'] == 'success' for row in active) else 'failed')
    report = {"checked_at": now, "status": status, "sources": sources}
    atomic_write(target, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    render_reports()


def render_reports() -> None:
    lines = ["# 수집 출처 상태", "", "출처별 마지막 실제 확인 결과입니다. 새 자료 0건은 정상일 수 있지만, 접속·해석 실패는 성공으로 처리하지 않습니다.", "",
             "전체 피드는 최근 기사 범위만 확인합니다. 과거 자료 전체를 검색했다는 뜻이 아닙니다.", "",
             "retired는 근거를 확인해 정기 수집을 종료한 과거 출처입니다. 실제 수집 성공이 아니며 활성 출처의 성공·실패 집계에서 제외합니다. 확인 시각은 종료 정책 점검 시각입니다.", ""]
    def cell(value) -> str:
        return str(value or "없음").replace("|", "\\|").replace("\n", " ")
    for path in sorted((BASE / "data/reports/collectors").glob("*.json")):
        report = json.loads(path.read_text())
        lines += [f"## {path.stem}", "", f"- 확인: {report['checked_at']}", "",
                  "| 출처 | 상태 | 범위 | 마지막 성공 | 연속 실패 | 상세 |",
                  "|---|---|---|---|---|---|"]
        for row in report["sources"]:
            detail = row.get("error") or f"확인 {row.get('fetched', 0)}건 · 관련 {row.get('matched', 0)}건"
            if row.get("warnings"):
                detail += " · " + "; ".join(row["warnings"])
            if row['status'] == 'retired':
                detail = row['reason'] + f" · 수집 종료: {row['retired_at']}"
                detail += ''.join(f" · [근거 {i}]({url})" for i, url in enumerate(row['evidence'], 1))
            failures = '해당 없음' if row['consecutive_failures'] is None else row['consecutive_failures']
            lines.append(f"| [{cell(row['name'])}]({row['url']}) | {row['status']} | {cell(row.get('scope'))} | {cell(row.get('last_success'))} | {failures} | {cell(detail)} |")
        lines += [""]
    atomic_write(BASE / "pages/source-collection-status.md", "\n".join(lines))
