#!/usr/bin/env python3
"""Read-only dashboard backed by recorded runs; unknown measurements stay null."""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

import psutil
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from scripts import operational_status as ops

BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title="goyoonjung-wiki Dashboard", version="2.0.0")


def get_system_status() -> dict:
    disk = psutil.disk_usage(str(BASE))
    return {"timestamp": datetime.now(ops.SEOUL).isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": {"percent": disk.percent}}


def get_collector_status() -> list[dict]:
    return ops.collectors(Path(BASE))


def get_recent_logs() -> list[dict]:
    return [{"timestamp": r["timestamp"], "level": r["status"], "message": r["message"]}
            for r in reversed(ops.news_runs(Path(BASE))[-10:])]


def get_performance_metrics() -> dict:
    return ops.metrics(Path(BASE))


def snapshot() -> dict:
    return {"system_status": get_system_status(), "automation": ops.health(Path(BASE)),
            "collectors": get_collector_status(), "recent_logs": get_recent_logs(),
            "performance_metrics": get_performance_metrics()}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


@app.get("/healthz")
def liveness():
    return {"status": "ok"}


@app.get("/api/status")
def get_status():
    return snapshot()


@app.get("/api/system")
def get_system():
    return get_system_status()


@app.get("/api/collectors")
def get_collectors():
    return get_collector_status()


@app.get("/api/logs")
def get_logs():
    return {"logs": get_recent_logs()}


@app.get("/api/metrics")
def get_metrics():
    return get_performance_metrics()


@app.post("/api/trigger/{collector}")
def trigger_collector(collector: str):
    raise HTTPException(501, "읽기 전용 대시보드입니다. 수집은 운영 스케줄러에서 실행하세요.")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(await asyncio.to_thread(snapshot))
            await asyncio.sleep(5)
    except (WebSocketDisconnect, RuntimeError, OSError):
        return


DASHBOARD_HTML = """<!doctype html>
<html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>고윤정 위키 운영 현황</title>
<style>body{max-width:1000px;margin:40px auto;padding:0 20px;font-family:system-ui;background:#f7f8fb;color:#182030}
section{padding:20px;margin:16px 0;background:white;border:1px solid #ddd;border-radius:12px}li{margin:12px 0;overflow-wrap:anywhere}pre{white-space:pre-wrap}h1{font-size:28px}</style>
<h1>고윤정 위키 운영 현황</h1><p id="connection">연결 중…</p>
<section><h2>자동화</h2><p id="automation"></p><p id="metrics"></p>
<p>실행 시간·가동률은 측정 기록이 없어 표시하지 않습니다. 성공률 표본은 날짜별 마지막 실행입니다.</p></section>
<section><h2>호스트</h2><p id="system"></p></section>
<section><h2>수집기 마지막 기록</h2><ul id="collectors"></ul></section>
<section><h2>최근 실행 기록</h2><ul id="logs"></ul></section>
<script>
const show = (id, text) => document.getElementById(id).textContent = text;
function list(id, rows) {
  document.getElementById(id).replaceChildren(...rows.map(text => {
    const li = document.createElement('li'); li.textContent = text; return li;
  }));
}
function render(d) {
  show('connection', '연결됨 · 화면 갱신: ' + new Date().toLocaleTimeString());
  show('automation', d.automation.status + ' · 마지막 실행: ' + (d.automation.last_run ?? '기록 없음'));
  const m=d.performance_metrics;
  show('metrics', '기록상 성공률: ' + (m.success_rate ?? '미측정') + '% · 표본 ' + m.sample_count + '개 · 오늘 기록 ' + m.total_runs_today + '개');
  const s=d.system_status;
  show('system', `CPU ${s.cpu_percent}% · 메모리 ${s.memory_percent}% · 디스크 ${s.disk_usage.percent}%`);
  list('collectors', d.collectors.map(c => `${c.name}: ${c.status} · 최신성 ${c.freshness} · ${c.last_run ?? '기록 없음'}`));
  list('logs', d.recent_logs.map(l => `${l.timestamp} · ${l.level} · ${l.message}`));
}
async function refresh() {
  try { const response=await fetch('/api/status'); if (!response.ok) throw new Error(); render(await response.json()); }
  catch { show('connection','연결 실패 · 표시된 기록은 최신 상태가 아닐 수 있습니다.'); }
}
function connect() {
  const ws = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`);
  ws.onmessage = event => render(JSON.parse(event.data));
  ws.onclose = () => { show('connection','연결 끊김 · 재연결 중'); setTimeout(connect,5000); };
  ws.onerror = () => ws.close();
}
refresh(); connect();
</script></html>"""
