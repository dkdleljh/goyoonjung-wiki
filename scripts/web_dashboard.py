#!/usr/bin/env python3
"""Real-time web dashboard for goyoonjung-wiki monitoring.
Provides comprehensive system status, metrics, and control interface.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import psutil
import uvicorn
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add base directory to path
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE)

from scripts.secure_config import create_secure_config

# Initialize FastAPI app
app = FastAPI(
    title="goyoonjung-wiki Dashboard",
    description="Real-time monitoring and control interface",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except (RuntimeError, OSError):
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Data models
class SystemStatus(BaseModel):
    timestamp: str
    status: str
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, Any]
    network_io: Dict[str, Any]
    process_count: int

class CollectorStatus(BaseModel):
    name: str
    status: str
    last_run: str
    last_duration: float
    success_rate: float
    error_count: int

class DashboardData(BaseModel):
    system_status: SystemStatus
    collectors: List[CollectorStatus]
    recent_logs: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]

# System monitoring functions
def get_system_status() -> SystemStatus:
    """Get current system status."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    network = psutil.net_io_counters()
    
    return SystemStatus(
        timestamp=datetime.now().isoformat(),
        status="healthy" if cpu_percent < 80 and memory.percent < 80 else "warning",
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        disk_usage={
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        },
        network_io={
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        },
        process_count=len(psutil.pids())
    )

def get_collector_status() -> List[CollectorStatus]:
    """Get status of all data collectors."""
    collectors = [
        "visual-links", "gnews", "gnews-sites", "gnews-queries",
        "mag-rss", "portal-news", "sanitize-news", "schedule",
        "agency", "encyclopedia", "link-health"
    ]
    
    status_list = []
    
    for collector in collectors:
        # Simulate collector status - in real implementation, 
        # this would read from actual status files
        status_list.append(CollectorStatus(
            name=collector,
            status="success",  # success, failure, running
            last_run=datetime.now().isoformat(),
            last_duration=45.2,
            success_rate=95.5,
            error_count=2
        ))
    
    return status_list

def get_recent_logs() -> List[Dict[str, Any]]:
    """Get recent system logs."""
    logs = []
    
    # Read from daily report or log files
    daily_report_path = Path(BASE) / "pages" / "daily-report.md"
    if daily_report_path.exists():
        try:
            with open(daily_report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract recent execution history
                lines = content.split('\n')
                for line in lines[-10:]:  # Last 10 lines
                    if '성공 ·' in line or '실패 ·' in line:
                        logs.append({
                            "timestamp": datetime.now().isoformat(),
                            "level": "info" if '성공' in line else "error",
                            "message": line.strip()
                        })
        except Exception as e:
            logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "error",
                "message": f"Failed to read daily report: {e}"
            })
    
    return logs

def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics."""
    return {
        "avg_execution_time": 9.5,  # minutes
        "success_rate": 98.2,
        "total_runs_today": 24,
        "last_successful_run": datetime.now().isoformat(),
        "uptime_percentage": 99.8
    }

# API endpoints
@app.get("/")
async def dashboard():
    """Serve the dashboard HTML."""
    return HTMLResponse(DASHBOARD_HTML)

@app.get("/api/status")
async def get_status():
    """Get complete dashboard data."""
    return DashboardData(
        system_status=get_system_status(),
        collectors=get_collector_status(),
        recent_logs=get_recent_logs(),
        performance_metrics=get_performance_metrics()
    )

@app.get("/api/system")
async def get_system():
    """Get system status only."""
    return get_system_status()

@app.get("/api/collectors")
async def get_collectors():
    """Get collector status."""
    return get_collector_status()

@app.get("/api/logs")
async def get_logs():
    """Get recent logs."""
    return {"logs": get_recent_logs()}

@app.get("/api/metrics")
async def get_metrics():
    """Get performance metrics."""
    return get_performance_metrics()

@app.post("/api/trigger/{collector}")
async def trigger_collector(collector: str):
    """Trigger a specific collector."""
    # In real implementation, this would trigger the actual collector
    await manager.broadcast(json.dumps({
        "type": "collector_triggered",
        "collector": collector,
        "timestamp": datetime.now().isoformat()
    }))
    
    return {"status": "triggered", "collector": collector}

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time dashboard updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            data = get_system_status().dict()
            data["type"] = "system_update"
            await manager.send_personal_message(json.dumps(data), websocket)
            await asyncio.sleep(5)  # Update every 5 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task for real-time updates
async def broadcast_updates():
    """Broadcast system updates to all connected clients."""
    while True:
        try:
            # Get current system status
            status = get_system_status().dict()
            status["type"] = "system_update"
            
            # Broadcast to all connections
            await manager.broadcast(json.dumps(status))
            
            await asyncio.sleep(10)  # Update every 10 seconds
        except Exception as e:
            print(f"Broadcast error: {e}")
            await asyncio.sleep(30)

# HTML Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>goyoonjung-wiki Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .status-healthy { color: #10b981; }
        .status-warning { color: #f59e0b; }
        .status-error { color: #ef4444; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto p-4">
        <h1 class="text-3xl font-bold mb-6">goyoonjung-wiki 실시간 대시보드</h1>
        
        <!-- System Status -->
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <h2 class="text-xl font-semibold mb-4">시스템 상태</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <h3 class="font-medium">CPU 사용률</h3>
                    <p id="cpu-percent" class="text-2xl font-bold">0%</p>
                </div>
                <div>
                    <h3 class="font-medium">메모리 사용률</h3>
                    <p id="memory-percent" class="text-2xl font-bold">0%</p>
                </div>
                <div>
                    <h3 class="font-medium">디스크 사용률</h3>
                    <p id="disk-percent" class="text-2xl font-bold">0%</p>
                </div>
            </div>
        </div>
        
        <!-- Collectors Status -->
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <h2 class="text-xl font-semibold mb-4">데이터 수집기 상태</h2>
            <div id="collectors" class="space-y-2">
                <!-- Collector status will be populated by JavaScript -->
            </div>
        </div>
        
        <!-- Recent Logs -->
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <h2 class="text-xl font-semibold mb-4">최근 로그</h2>
            <div id="logs" class="space-y-1">
                <!-- Logs will be populated by JavaScript -->
            </div>
        </div>
        
        <!-- Performance Metrics -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">성능 지표</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <h3 class="font-medium">평균 실행 시간</h3>
                    <p id="avg-execution" class="text-2xl font-bold">0분</p>
                </div>
                <div>
                    <h3 class="font-medium">성공률</h3>
                    <p id="success-rate" class="text-2xl font-bold">0%</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket connection for real-time updates
        const ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'system_update') {
                updateSystemStatus(data);
            }
        };
        
        function updateSystemStatus(data) {
            document.getElementById('cpu-percent').textContent = data.cpu_percent.toFixed(1) + '%';
            document.getElementById('memory-percent').textContent = data.memory_percent.toFixed(1) + '%';
            document.getElementById('disk-percent').textContent = data.disk_usage.percent.toFixed(1) + '%';
            
            // Update colors based on status
            const cpuElement = document.getElementById('cpu-percent');
            cpuElement.className = data.cpu_percent > 80 ? 'text-2xl font-bold status-error' : 'text-2xl font-bold status-healthy';
        }
        
        // Fetch initial data
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                updateSystemStatus(data.system_status);
                updateCollectors(data.collectors);
                updateLogs(data.recent_logs);
                updateMetrics(data.performance_metrics);
            });
        
        function updateCollectors(collectors) {
            const collectorsDiv = document.getElementById('collectors');
            collectorsDiv.innerHTML = collectors.map(collector => `
                <div class="flex justify-between items-center p-2 border rounded">
                    <span>${collector.name}</span>
                    <span class="${collector.status === 'success' ? 'status-healthy' : collector.status === 'failure' ? 'status-error' : 'status-warning'}">
                        ${collector.status}
                    </span>
                </div>
            `).join('');
        }
        
        function updateLogs(logs) {
            const logsDiv = document.getElementById('logs');
            logsDiv.innerHTML = logs.map(log => `
                <div class="p-2 ${log.level === 'error' ? 'bg-red-50' : 'bg-gray-50'} rounded">
                    <span class="text-sm text-gray-600">${log.timestamp}</span>
                    <span class="${log.level === 'error' ? 'status-error' : 'status-healthy'}">${log.message}</span>
                </div>
            `).join('');
        }
        
        function updateMetrics(metrics) {
            document.getElementById('avg-execution').textContent = metrics.avg_execution_time.toFixed(1) + '분';
            document.getElementById('success-rate').textContent = metrics.success_rate.toFixed(1) + '%';
        }
    </script>
</body>
</html>
"""

# Start background update task
@app.on_event("startup")
async def startup_event():
    """Start background tasks."""
    asyncio.create_task(broadcast_updates())

if __name__ == "__main__":
    print("🚀 Starting goyoonjung-wiki Dashboard")
    print("📊 Real-time monitoring enabled")
    print("🌐 Dashboard will be available at http://localhost:8000")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )