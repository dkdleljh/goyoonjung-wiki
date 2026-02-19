#!/usr/bin/env python3
"""Tests for domain grading policy."""

from __future__ import annotations

import scripts.domain_policy as dp


def test_legacy_allowlist_prefixes(monkeypatch, tmp_path):
    allow = tmp_path / "allow.txt"
    allow.write_text("S:news.kbs.co.kr\nexample.com\nBLOCK:bad.example\n", encoding="utf-8")
    grades = tmp_path / "grades.yml"
    grades.write_text("", encoding="utf-8")

    monkeypatch.setattr(dp, "ALLOWLIST_PATH", allow)
    monkeypatch.setattr(dp, "GRADES_PATH", grades)

    policy = dp.load_policy()
    assert policy.grade_for_host("news.kbs.co.kr") == "S"
    assert policy.grade_for_host("example.com") == "A"
    assert policy.grade_for_host("bad.example") == "BLOCK"


def test_yaml_overrides_allowlist(monkeypatch, tmp_path):
    allow = tmp_path / "allow.txt"
    allow.write_text("example.com\n", encoding="utf-8")
    grades = tmp_path / "grades.yml"
    grades.write_text("example.com: B\n", encoding="utf-8")

    monkeypatch.setattr(dp, "ALLOWLIST_PATH", allow)
    monkeypatch.setattr(dp, "GRADES_PATH", grades)

    policy = dp.load_policy()
    assert policy.grade_for_host("example.com") == "B"


def test_unknown_is_block():
    policy = dp.DomainPolicy(grades={})
    assert policy.grade_for_host("unknown.example") == "BLOCK"

