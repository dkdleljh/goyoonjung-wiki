#!/usr/bin/env python3
"""Domain grading policy (S/A/B/BLOCK) with allowlist compatibility."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import yaml

BASE = Path(__file__).resolve().parent.parent
ALLOWLIST_PATH = BASE / "config" / "allowlist-domains.txt"
GRADES_PATH = BASE / "config" / "domain-grades.yml"

GRADE_ORDER = {"BLOCK": 0, "B": 1, "A": 2, "S": 3}
LANE_BY_GRADE = {"S": "landed", "A": "queue", "B": "pool", "BLOCK": "discard"}


def normalize_host(value: str) -> str:
    text = (value or "").strip().lower()
    if not text:
        return ""
    if "://" not in text:
        text = "https://" + text
    sp = urlsplit(text)
    host = sp.netloc.lower().split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]
    if host.startswith("m."):
        host = host[2:]
    if host.startswith("mobile."):
        host = host[7:]
    if host.startswith("amp."):
        host = host[4:]
    return host


def _grade_value(raw: str) -> str:
    v = (raw or "").strip().upper()
    return v if v in GRADE_ORDER else "A"


def _iter_legacy_allowlist() -> Iterable[tuple[str, str]]:
    if not ALLOWLIST_PATH.exists():
        return []
    out: list[tuple[str, str]] = []
    for raw in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("#"):
            continue
        if ":" in ln and ln.split(":", 1)[0].upper() in GRADE_ORDER:
            pref, rest = ln.split(":", 1)
            host = normalize_host(rest.strip())
            if host:
                out.append((_grade_value(pref), host))
            continue
        host = normalize_host(ln)
        if host:
            out.append(("A", host))
    return out


def _iter_yaml_grades() -> Iterable[tuple[str, str]]:
    if not GRADES_PATH.exists():
        return []
    obj = yaml.safe_load(GRADES_PATH.read_text(encoding="utf-8")) or {}
    if not isinstance(obj, dict):
        return []

    # Form 1: domain: grade
    if all(isinstance(v, str) for v in obj.values()):
        out: list[tuple[str, str]] = []
        for dom, grade in obj.items():
            host = normalize_host(str(dom))
            if host:
                out.append((_grade_value(str(grade)), host))
        return out

    # Form 2:
    # S: [domain1, domain2]
    # A: [...]
    out = []
    for grade, vals in obj.items():
        g = _grade_value(str(grade))
        if isinstance(vals, list):
            for dom in vals:
                host = normalize_host(str(dom))
                if host:
                    out.append((g, host))
    return out


@dataclass(frozen=True)
class DomainPolicy:
    grades: dict[str, str]

    @classmethod
    def load(cls) -> DomainPolicy:
        mapping: dict[str, str] = {}
        for grade, host in _iter_legacy_allowlist():
            mapping[host] = grade
        for grade, host in _iter_yaml_grades():
            mapping[host] = grade
        return cls(grades=mapping)

    def grade_for_host(self, host: str) -> str:
        h = normalize_host(host)
        if not h:
            return "BLOCK"
        if h in self.grades:
            return self.grades[h]
        parts = h.split(".")
        for i in range(1, len(parts) - 1):
            suffix = ".".join(parts[i:])
            if suffix in self.grades:
                return self.grades[suffix]
        return "BLOCK"

    def grade_for_url(self, url: str) -> str:
        try:
            host = urlsplit(url).netloc
        except Exception:
            return "BLOCK"
        return self.grade_for_host(host)

    def lane_for_url(self, url: str) -> str:
        return LANE_BY_GRADE.get(self.grade_for_url(url), "discard")

    def allow_hosts_for_min_grade(self, min_grade: str = "A") -> set[str]:
        need = GRADE_ORDER.get(min_grade, GRADE_ORDER["A"])
        return {h for h, g in self.grades.items() if GRADE_ORDER.get(g, 0) >= need}


def load_policy() -> DomainPolicy:
    return DomainPolicy.load()
