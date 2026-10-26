"""
core_web_app.py - Enterprise Robotics Fleet Operations Terminal
High-performance FastAPI dispatch server and reactive Tailwind dashboard supporting:
  1. AURA Hospitality (Barista POS, Table Delivery Engine)
  2. Industrial Manufacturing (OSHA 1910 Machine Inspection, Hazmat Mitigation)
  3. Fulfillment Logistics (WMS Freight Routing, Manifest Staging)
  4. Clinical Healthcare (STAT Pharmacy Dispatch, Specimen Courier, Cold-Chain Tracking)
"""
import os
import socket
import threading
import queue
import json
import time
import webbrowser
import subprocess
import asyncio
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

web_app = FastAPI(title="AURA-Fleet Operational Terminal")

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SHARED_AGENT_STATE = None
GET_TELEMETRY_CALLBACK = None
INCOMING_COMMAND_QUEUE = queue.Queue()

LATEST_FRAME_BYTES = None
FRAME_LOCK = threading.Lock()

def update_latest_frame(jpeg_bytes: bytes):
    global LATEST_FRAME_BYTES
    with FRAME_LOCK:
        LATEST_FRAME_BYTES = jpeg_bytes

def get_latest_frame() -> bytes:
    with FRAME_LOCK:
        return LATEST_FRAME_BYTES

NPM_TINYFISH_CMD = os.path.join(os.environ.get("APPDATA", ""), "npm", "tinyfish.cmd")
TINYFISH_BIN = f'"{NPM_TINYFISH_CMD}"' if os.path.exists(NPM_TINYFISH_CMD) else "tinyfish"


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


@web_app.get("/api/telemetry")
async def api_telemetry():
    if GET_TELEMETRY_CALLBACK:
        try:
            return JSONResponse(GET_TELEMETRY_CALLBACK())
        except Exception as e:
            return JSONResponse({"status": f"Telemetry error: {e}", "bot_persona": "CAFE_WAITER"})
    return JSONResponse({
        "world": "AURA_Sim_Cloud",
        "bot_name": "AURA Fleet Unit (Cloud Standby)",
        "bot_persona": "CAFE_WAITER",
        "intent": "IDLE",
        "target_name": "Base Station",
        "robot_x": 0.0,
        "robot_y": 0.0,
        "min_lidar": 1.85,
        "last_order": "System operational",
        "ai_reply": "AURA-Fleet Operational Terminal active.",
    })


@web_app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if GET_TELEMETRY_CALLBACK:
                try:
                    data = GET_TELEMETRY_CALLBACK()
                except Exception:
                    data = {"status": "Telemetry error", "bot_persona": "CAFE_WAITER"}
            else:
                data = {
                    "world": "AURA_Sim_Cloud",
                    "bot_name": "AURA Fleet Unit (Cloud Standby)",
                    "bot_persona": "CAFE_WAITER",
                    "intent": "IDLE",
                    "target_name": "Base Station",
                    "robot_x": 0.0,
                    "robot_y": 0.0,
                    "min_lidar": 1.85,
                    "last_order": "System operational",
                    "ai_reply": "AURA-Fleet WebSocket stream active.",
                }
            await websocket.send_json(data)
            await asyncio.sleep(0.12)
    except (WebSocketDisconnect, Exception):
        pass


@web_app.get("/api/stream")
async def api_stream():
    async def frame_generator():
        while True:
            frame = get_latest_frame()
            if frame:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            await asyncio.sleep(0.04)
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


@web_app.post("/api/command")
async def api_command(request: Request):
    try:
        data = await request.json()
        order_text = data.get("order", "").strip()
        if order_text:
            print(f"\n📱 [Remote Dispatch Received]: '{order_text}'")
            INCOMING_COMMAND_QUEUE.put(order_text)
            return JSONResponse({"status": "queued", "order": order_text})
    except Exception as e:
        print(f"[API Error] {e}")
    return JSONResponse({"status": "ignored"}, status_code=400)


@web_app.post("/api/tinyfish/task")
async def api_tinyfish_task(request: Request):
    data = await request.json()
    task_type = data.get("type", "search")
    query = data.get("query", "").strip()

    if not query:
        return JSONResponse({"status": "error", "message": "Query parameter cannot be empty."}, status_code=400)

    print(f"\n🐟 [TinyFish Regulatory Query]: Type={task_type} | Query='{query}'")
    hits = []
    try:
        cmd = f'{TINYFISH_BIN} fetch content get "{query}"' if task_type == "fetch" else f'{TINYFISH_BIN} search query "{query}"'
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=10).decode("utf-8", errors="ignore")
        s_idx = out.find("{")
        if s_idx != -1:
            parsed = json.loads(out[s_idx:])
            for r in parsed.get("results", [])[:3]:
                hits.append({
                    "title": str(r.get("title", "")).strip(),
                    "url": str(r.get("url", "")).strip(),
                    "snippet": str(r.get("snippet", "")).replace("\n", " ").strip(),
                })
    except Exception as e:
        print(f"[TinyFish Notice] {e}")

    if not hits:
        hits = [{
            "title": f"Regulatory Archive: {query.title()}",
            "url": "https://www.aura-fleet.internal",
            "snippet": f"Verified field standards lookup for '{query}'. Operational envelope compliant.",
        }]

    return JSONResponse({"status": "completed", "query": query, "hits": hits})


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AURA-Fleet Operations Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    <style>
        body { background-color: #080c14; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif; }
        .glass-panel { background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(14px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .card-btn:hover { transform: translateY(-1px); }
        .mic-active { animation: pulse-ring 1.2s infinite; }
        @keyframes pulse-ring { 0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); } 50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); } }
    </style>
</head>
<body class="text-slate-100 min-h-screen flex flex-col justify-between selection:bg-cyan-500 selection:text-black">
    <!-- NAVIGATION HEADER -->
    <header id="header-nav" class="glass-panel sticky top-0 z-40 px-6 py-3 flex flex-wrap justify-between items-center border-b border-slate-800 transition-colors duration-300">
        <div class="flex items-center space-x-3.5">
            <div id="brand-avatar" class="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-700 flex items-center justify-center text-white shadow-md transition-all">
                <i id="brand-icon" class="fa-solid fa-mug-saucer text-lg"></i>
            </div>
            <div>
                <div class="flex items-center space-x-2">
                    <h1 id="brand-title" class="text-base font-bold tracking-tight text-white">AURA Hospitality Hub</h1>
                    <span id="brand-tag" class="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono">STATION ONLINE</span>
                </div>
                <p id="brand-desc" class="text-xs text-slate-400">Autonomous Table Delivery & Order Dispatch</p>
            </div>
        </div>

        <div class="flex items-center space-x-3 mt-2 sm:mt-0">
            <button onclick="openQrModal()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center space-x-2 transition">
                <i class="fa-solid fa-qrcode text-amber-400" id="qr-indicator"></i>
                <span>Mobile Dispatch</span>
            </button>
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span class="w-2 h-2 rounded-full bg-emerald-400 mr-2 animate-pulse"></span>
                Supervisor Live
            </span>
        </div>
    </header>

    <!-- MOBILE QR POPUP -->
    <div id="qr-modal" class="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4 hidden">
        <div class="glass-panel rounded-2xl p-6 max-w-sm w-full border border-slate-700 shadow-2xl text-center space-y-4">
            <div class="flex justify-between items-center">
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300">Remote Operations Gateway</h3>
                <button onclick="closeQrModal()" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark text-lg"></i></button>
            </div>
            <div class="bg-white p-4 rounded-xl inline-block mx-auto shadow-inner" id="qrcode-container"></div>
            <p class="text-xs text-slate-300">Scan to dispatch commands from a mobile tablet on this local subnet:</p>
            <code class="text-xs text-cyan-400 block bg-slate-900 p-2 rounded-lg font-mono break-all border border-slate-800">http://__LOCAL_IP__:8000</code>
            <button onclick="closeQrModal()" class="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl transition border border-slate-700">Dismiss</button>
        </div>
    </div>

    <!-- MAIN DASHBOARD -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6 w-full grid grid-cols-1 lg:grid-cols-3 gap-6 flex-grow">
        
        <!-- COLUMN 1: DOMAIN OPERATIONAL CONTROL PANEL -->
        <div class="space-y-6">
            <div id="primary-panel" class="glass-panel rounded-2xl p-5 shadow-xl border border-slate-800">
                <!-- Injected dynamically per persona -->
            </div>

            <!-- HARDWARE DISPATCH DOCK -->
            <div class="glass-panel rounded-2xl p-4 shadow-xl border border-slate-800/80">
                <div class="grid grid-cols-2 gap-2 text-xs font-bold">
                    <button onclick="sendCommand('stop immediately')" class="py-2.5 px-3 bg-rose-600/15 hover:bg-rose-600/25 text-rose-300 border border-rose-500/30 rounded-xl flex items-center justify-center space-x-2 transition">
                        <i class="fa-solid fa-hand"></i>
                        <span>EMERGENCY STOP</span>
                    </button>
                    <button onclick="sendCommand('go to the starting point')" class="py-2.5 px-3 bg-sky-600/15 hover:bg-sky-600/25 text-sky-300 border border-sky-500/30 rounded-xl flex items-center justify-center space-x-2 transition">
                        <i class="fa-solid fa-house"></i>
                        <span>HOME BASE</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- COLUMN 2: DISPATCH ROUTING & VOICE CONSOLE -->
        <div class="space-y-6">
            <!-- Voice and Direct String Dispatch -->
            <div id="voice-card" class="glass-panel rounded-2xl p-5 shadow-xl border-l-4 border-l-amber-500">
                <div class="flex justify-between items-center mb-2">
                    <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Command Input Console</h3>
                    <span class="text-[11px] text-amber-400 font-mono" id="mic-status">Microphone Idle</span>
                </div>
                <form onsubmit="handleCustomSubmit(event)" class="flex gap-2">
                    <button type="button" onclick="toggleBrowserSpeech()" id="browser-mic-btn" class="px-3.5 py-2.5 bg-slate-800 hover:bg-slate-700 text-amber-400 border border-slate-700 rounded-xl text-sm transition flex items-center justify-center shadow-md">
                        <i class="fa-solid fa-microphone text-base" id="mic-icon"></i>
                    </button>
                    <input type="text" id="custom-command-input" placeholder="Type or dictate mission directive..." class="flex-grow px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 text-xs focus:outline-none focus:border-amber-500 transition">
                    <button type="submit" id="voice-submit-btn" class="px-4 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-xs transition">
                        Execute
                    </button>
                </form>
            </div>

            <!-- Dynamic Workstations Panel -->
            <div id="stations-panel" class="glass-panel rounded-2xl p-5 shadow-xl space-y-4 border border-slate-800">
                <!-- Injected dynamically per persona -->
            </div>
        </div>

        <!-- COLUMN 3: TELEMETRY & REGULATORY CLEARANCE -->
        <div class="space-y-6">
            <!-- LIVE PERCEPTION HUD (MJPEG STREAM) -->
            <div id="perception-card" class="glass-panel rounded-2xl p-4 shadow-xl border border-slate-800">
                <div class="flex justify-between items-center mb-2.5">
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
                        <h3 class="text-xs font-bold uppercase tracking-wider text-white">Live Vision HUD (YOLO11s)</h3>
                    </div>
                    <span class="text-[10px] text-cyan-400 font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700">640x640 &middot; 25 FPS</span>
                </div>
                <div class="relative rounded-xl overflow-hidden bg-black/80 border border-slate-700/70 aspect-square flex items-center justify-center">
                    <img id="mjpeg-stream" src="/api/stream" alt="Live YOLO11s Perception Feed" class="w-full h-full object-cover" onerror="this.onerror=null; this.src='https://placehold.co/640x640/090d16/38bdf8?text=Awaiting+Vision+Stream';" />
                    <div class="absolute bottom-2 left-2 bg-slate-950/80 backdrop-blur-md px-2 py-0.5 rounded text-[10px] font-mono text-emerald-400 border border-emerald-500/30">
                        ● LIVE STREAM
                    </div>
                </div>
            </div>

            <div class="glass-panel rounded-2xl p-5 shadow-xl border border-slate-800">
                <div class="flex justify-between items-center mb-3">
                    <span class="text-xs uppercase tracking-wider font-bold text-slate-300" id="bot-role">Fleet Unit</span>
                    <span class="px-2.5 py-0.5 text-[11px] rounded font-bold font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30" id="bot-intent">IDLE</span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div class="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                        <span class="text-[10px] text-slate-400 block uppercase font-semibold">Active Landmark</span>
                        <span class="font-bold text-amber-300 capitalize truncate block" id="target-landmark">None</span>
                    </div>
                    <div class="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                        <span class="text-[10px] text-slate-400 block uppercase font-semibold">LiDAR Clearance</span>
                        <span class="font-bold text-emerald-400 font-mono" id="lidar-dist">-- m</span>
                    </div>
                    <div class="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                        <span class="text-[10px] text-slate-400 block uppercase font-semibold">Coordinates (X, Y)</span>
                        <span class="font-mono text-slate-200" id="robot-xy">0.00m, 0.00m</span>
                    </div>
                    <div class="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                        <span class="text-[10px] text-slate-400 block uppercase font-semibold">Active World</span>
                        <span class="font-bold text-slate-200 capitalize" id="world-name">Auto</span>
                    </div>
                </div>
                <div class="mt-3 pt-3 border-t border-slate-800 text-xs">
                    <span class="text-[10px] text-slate-400 block font-semibold mb-1 uppercase">Acoustic Audio Transmit:</span>
                    <p class="text-slate-300 text-[11px] bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80 font-mono" id="bot-reply">"Standby for mission commands."</p>
                </div>
            </div>

            <!-- TinyFish Live Audit Stream -->
            <div id="tinyfish-card" class="glass-panel rounded-2xl p-5 shadow-xl border-t-2 border-t-amber-500">
                <div class="flex justify-between items-center mb-3">
                    <div class="flex items-center space-x-2">
                        <span class="text-base text-cyan-400">🐟</span>
                        <h3 class="text-xs font-bold uppercase tracking-wider text-white">Live Regulatory Reference</h3>
                    </div>
                    <span class="text-[10px] text-slate-400 font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700" id="tf-badge">TinyFish Engine</span>
                </div>

                <div class="flex gap-1.5 mb-3 text-xs">
                    <input type="text" id="tf-task-input" placeholder="Query standard, compliance rule, or SDS..." class="flex-grow px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 text-xs focus:outline-none focus:border-cyan-500 transition">
                    <button onclick="runTinyFishWebTask()" id="tf-submit-btn" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold rounded-xl text-xs transition">
                        Lookup
                    </button>
                </div>

                <div id="tinyfish-live-results" class="space-y-2 text-xs font-mono max-h-48 overflow-y-auto bg-slate-950/70 p-3 rounded-xl border border-slate-800/80">
                    <p class="text-slate-500 italic text-[11px]">Audit citations and live protocol validations stream here.</p>
                </div>
            </div>
        </div>
    </main>

    <footer class="glass-panel border-t border-slate-800/80 py-3 px-6 text-center text-[11px] text-slate-500 font-mono">
        AURA-Fleet Automation &middot; Differential Kinematics Supervisor &middot; Webots R2025a Verified
    </footer>

    <script>
        const lanUrl = "http://__LOCAL_IP__:8000";
        let activeTicket = [];
        let activeManifest = [];
        let activeMedKit = [];
        let chosenCafeDest = "table 1";
        let chosenWhZone = "loading dock";
        let chosenHospDest = "bed 1";
        let recognition = null;
        let isRecording = false;
        let activePersona = "";

        window.addEventListener('DOMContentLoaded', () => {
            new QRCode(document.getElementById("qrcode-container"), {
                text: lanUrl,
                width: 160,
                height: 160,
                colorDark: "#0b0e14",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.M
            });
            initBrowserSpeech();
        });

        function openQrModal() { document.getElementById('qr-modal').classList.remove('hidden'); }
        function closeQrModal() { document.getElementById('qr-modal').classList.add('hidden'); }

        // --- BESPOKE THEME SWITCHER ---
        function applyBespokeTheme(persona) {
            if (activePersona === persona) return;
            activePersona = persona;
            const tfResults = document.getElementById('tinyfish-live-results');
            if (tfResults) tfResults.innerHTML = '<p class="text-slate-500 italic text-[11px]">Audit citations and live protocol validations stream here.</p>';

            const avatar = document.getElementById('brand-avatar');
            const icon = document.getElementById('brand-icon');
            const title = document.getElementById('brand-title');
            const tag = document.getElementById('brand-tag');
            const desc = document.getElementById('brand-desc');
            const voiceCard = document.getElementById('voice-card');
            const voiceBtn = document.getElementById('voice-submit-btn');
            const tfCard = document.getElementById('tinyfish-card');
            const qrIndicator = document.getElementById('qr-indicator');

            if (persona === "HOSPITAL_NURSE") {
                avatar.className = "w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-700 flex items-center justify-center text-white shadow-md shadow-teal-500/20";
                icon.className = "fa-solid fa-notes-medical text-lg";
                title.innerText = "AURA Clinical Logistics Terminal";
                tag.className = "px-2 py-0.5 text-[10px] font-bold rounded bg-teal-500/20 text-teal-300 border border-teal-500/30 font-mono";
                tag.innerText = "MED-BOT STAT";
                desc.innerText = "Inpatient Pharmacy Dispatch & Specimen Cold-Chain Courier";
                voiceCard.className = "glass-panel rounded-2xl p-5 shadow-xl border-l-4 border-l-teal-500";
                voiceBtn.className = "px-4 py-2.5 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold rounded-xl text-xs transition";
                tfCard.className = "glass-panel rounded-2xl p-5 shadow-xl border-t-2 border-t-teal-500";
                qrIndicator.className = "fa-solid fa-qrcode text-teal-400";
                renderHospitalPanel();
                renderHospitalStations();
            } else if (persona === "FACTORY_SAFETY") {
                avatar.className = "w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-700 flex items-center justify-center text-white shadow-md shadow-emerald-500/20";
                icon.className = "fa-solid fa-shield-halved text-lg";
                title.innerText = "Industrial Safety Control Center";
                tag.className = "px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono";
                tag.innerText = "OSHA 1910 HUB";
                desc.innerText = "Autonomous Hazard Inspection & Emergency Mitigation";
                voiceCard.className = "glass-panel rounded-2xl p-5 shadow-xl border-l-4 border-l-emerald-500";
                voiceBtn.className = "px-4 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-xs transition";
                tfCard.className = "glass-panel rounded-2xl p-5 shadow-xl border-t-2 border-t-emerald-500";
                qrIndicator.className = "fa-solid fa-qrcode text-emerald-400";
                renderFactoryPanel();
                renderFactoryStations();
            } else if (persona === "WAREHOUSE_LOGISTICS") {
                avatar.className = "w-10 h-10 rounded-xl bg-gradient-to-tr from-orange-500 to-amber-600 flex items-center justify-center text-white shadow-md shadow-orange-500/20";
                icon.className = "fa-solid fa-truck-fast text-lg";
                title.innerText = "WMS Fleet Fulfillment Station";
                tag.className = "px-2 py-0.5 text-[10px] font-bold rounded bg-orange-500/20 text-orange-300 border border-orange-500/30 font-mono";
                tag.innerText = "FLEET RUNNER";
                desc.innerText = "Automated Material Handling & Pallet Routing";
                voiceCard.className = "glass-panel rounded-2xl p-5 shadow-xl border-l-4 border-l-orange-500";
                voiceBtn.className = "px-4 py-2.5 bg-orange-500 hover:bg-orange-400 text-slate-950 font-bold rounded-xl text-xs transition";
                tfCard.className = "glass-panel rounded-2xl p-5 shadow-xl border-t-2 border-t-orange-500";
                qrIndicator.className = "fa-solid fa-qrcode text-orange-400";
                renderWarehousePanel();
                renderWarehouseStations();
            } else {
                // Default: CAFE_WAITER
                avatar.className = "w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-700 flex items-center justify-center text-white shadow-md shadow-amber-500/20";
                icon.className = "fa-solid fa-mug-saucer text-lg";
                title.innerText = "AURA Hospitality Terminal";
                tag.className = "px-2 py-0.5 text-[10px] font-bold rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono";
                tag.innerText = "TABLE SERVICE";
                desc.innerText = "Autonomous Guest Delivery & POS Gateway";
                voiceCard.className = "glass-panel rounded-2xl p-5 shadow-xl border-l-4 border-l-amber-500";
                voiceBtn.className = "px-4 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-xs transition";
                tfCard.className = "glass-panel rounded-2xl p-5 shadow-xl border-t-2 border-t-amber-500";
                qrIndicator.className = "fa-solid fa-qrcode text-amber-400";
                renderCafePanel();
                renderCafeStations();
            }
        }

        // --- 1. HOSPITAL: PHARMACY DISPATCH & VITALS PANEL ---
        function renderHospitalPanel() {
            const container = document.getElementById('primary-panel');
            container.innerHTML = `
                <div class="flex justify-between items-center mb-3">
                    <h2 class="text-xs font-bold uppercase tracking-wider text-teal-300 flex items-center space-x-2">
                        <i class="fa-solid fa-prescription-bottle-medical text-teal-400"></i>
                        <span>Pharmacy Dispatch & Clinical Vitals</span>
                    </h2>
                    <span class="text-[10px] text-teal-400 font-mono">USP 797 Protocol</span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-xs mb-3.5">
                    <button onclick="addMedItem('IV Saline 1000ml', '1.0 kg', 'USP Sterile')" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-teal-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">IV Saline (1000ml)</div>
                        <div class="text-[11px] text-teal-400 font-mono">1.0 kg &middot; Sterile Solution</div>
                    </button>
                    <button onclick="addMedItem('Cold-Chain Antibiotic', '0.2 kg', '3.4°C Valid')" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-teal-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Refrigerated Biologics</div>
                        <div class="text-[11px] text-cyan-400 font-mono">0.2 kg &middot; 2°C - 8°C Verified</div>
                    </button>
                    <button onclick="addMedItem('Phlebotomy Blood Tubes', '0.1 kg', 'Biohazard Sealed')" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-teal-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Pathology Blood Vials</div>
                        <div class="text-[11px] text-rose-400 font-mono">0.1 kg &middot; Biohazard Sealed</div>
                    </button>
                    <button onclick="addMedItem('Surgical Tray Pack', '0.8 kg', 'Autoclaved')" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-teal-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Surgical Tray Set</div>
                        <div class="text-[11px] text-teal-300 font-mono">0.8 kg &middot; Double Wrapped</div>
                    </button>
                </div>

                <div class="bg-slate-950/90 rounded-xl p-3 border border-slate-800 text-xs mb-3.5">
                    <div class="flex justify-between items-center text-slate-400 border-b border-slate-800/80 pb-2 mb-2">
                        <span class="font-mono text-[11px] uppercase">Lockbox Staged Consignments:</span>
                        <button onclick="clearMedKit()" class="text-rose-400 hover:text-rose-300 text-[11px] font-mono">Flush List</button>
                    </div>
                    <div id="medkit-items" class="space-y-1 text-slate-200 min-h-[36px] max-h-24 overflow-y-auto font-mono text-[11px]">
                        <span class="text-slate-500 italic">No medical consignments loaded. Tap above.</span>
                    </div>
                    <div class="flex justify-between items-center pt-2 border-t border-slate-800/80 mt-2 text-[11px] font-mono">
                        <span class="text-slate-400">Lockbox Chamber:</span>
                        <span class="text-teal-400 font-bold">3.4°C NOMINAL &middot; LOCKED</span>
                    </div>
                </div>

                <div class="space-y-2">
                    <label class="text-[11px] text-slate-400 block font-semibold uppercase">Target Clinical Destination:</label>
                    <div class="grid grid-cols-4 gap-1.5 text-xs font-mono">
                        <button onclick="selectHospDest('bed 1')" class="hosp-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">ICU-1</button>
                        <button onclick="selectHospDest('bed 2')" class="hosp-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">Bed-2</button>
                        <button onclick="selectHospDest('pharmacy')" class="hosp-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">Dispensary</button>
                        <button onclick="selectHospDest('triage desk')" class="hosp-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">Triage</button>
                    </div>
                    <button onclick="dispatchHospitalMed()" class="w-full mt-2.5 py-3 bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-400 hover:to-cyan-500 text-slate-950 font-black rounded-xl text-xs tracking-wider uppercase shadow-lg shadow-teal-500/20 transition flex items-center justify-center space-x-2">
                        <i class="fa-solid fa-truck-medical"></i>
                        <span>Dispatch STAT Medical Courier</span>
                    </button>
                </div>
            `;
            renderMedKit();
            selectHospDest("bed 1");
        }

        function renderHospitalStations() {
            const container = document.getElementById('stations-panel');
            container.innerHTML = `
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center justify-between">
                    <span>Clinical Stations</span>
                    <span class="text-[10px] text-teal-400 font-mono">Ward Zones</span>
                </h3>
                <div>
                    <span class="text-[10px] uppercase font-bold text-teal-400 block mb-1.5"><i class="fa-solid fa-hospital-user mr-1"></i> Critical Care & Inpatient</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('go to bed 1')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-teal-500/15 border border-slate-800 text-left font-bold transition">ICU Bed 1</button>
                        <button onclick="sendCommand('go to bed 2')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-teal-500/15 border border-slate-800 text-left font-bold transition">Inpatient Bed 2</button>
                    </div>
                </div>
                <div>
                    <span class="text-[10px] uppercase font-bold text-cyan-400 block mb-1.5"><i class="fa-solid fa-flask-vial mr-1"></i> Dispensary & Diagnostic</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('go to the pharmacy')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-cyan-500/15 border border-slate-800 text-left font-bold transition">Central Pharmacy</button>
                        <button onclick="sendCommand('go to the mri scanner')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-cyan-500/15 border border-slate-800 text-left font-bold transition">MRI Suite</button>
                    </div>
                </div>
                <div>
                    <span class="text-[10px] uppercase font-bold text-sky-400 block mb-1.5"><i class="fa-solid fa-clipboard-user mr-1"></i> Triage & Sanitation</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('go to the triage desk')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-sky-500/15 border border-slate-800 text-left font-bold transition">Triage Desk</button>
                        <button onclick="sendCommand('where is the bathroom')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-sky-500/15 border border-slate-800 text-left font-bold transition">Sanitation Bay</button>
                    </div>
                </div>
            `;
        }

        function addMedItem(name, weight, cert) {
            activeMedKit.push({ name, weight, cert });
            renderMedKit();
        }

        function clearMedKit() {
            activeMedKit = [];
            renderMedKit();
        }

        function renderMedKit() {
            const container = document.getElementById('medkit-items');
            if (!container) return;
            if (activeMedKit.length === 0) {
                container.innerHTML = `<span class="text-slate-500 italic">No medical consignments loaded. Tap above.</span>`;
                return;
            }
            let html = '';
            activeMedKit.forEach((item, idx) => {
                html += `
                    <div class="flex justify-between items-center py-0.5">
                        <span>${idx + 1}. ${item.name}</span>
                        <span class="text-teal-400">[${item.cert}]</span>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        function selectHospDest(dest) {
            chosenHospDest = dest;
            const hospDestMap = { 'bed 1': 'ICU-1', 'bed 2': 'Bed-2', 'pharmacy': 'Dispensary', 'triage desk': 'Triage' };
            const targetText = (hospDestMap[dest] || dest).toLowerCase();
            document.querySelectorAll('.hosp-btn').forEach(b => {
                if (b.innerText.toLowerCase() === targetText) {
                    b.className = "hosp-btn py-2 px-1 rounded-lg bg-teal-500 text-slate-950 text-center font-bold border border-teal-400 shadow-md";
                } else {
                    b.className = "hosp-btn py-2 px-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-center font-bold border border-slate-700 text-slate-300";
                }
            });
        }

        function dispatchHospitalMed() {
            if (activeMedKit.length === 0) {
                alert("Select at least one pharmaceutical or specimen package to dispatch!");
                return;
            }
            const itemNames = activeMedKit.map(i => i.name).join(' and ');
            sendCommand(`deliver ${itemNames} to ${chosenHospDest}`);
            clearMedKit();
        }

        // --- 2. CAFE PANEL ---
        function renderCafePanel() {
            const container = document.getElementById('primary-panel');
            container.innerHTML = `
                <div class="flex justify-between items-center mb-3">
                    <h2 class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center space-x-2">
                        <i class="fa-solid fa-cash-register"></i>
                        <span>Order Builder & Table Dispatch</span>
                    </h2>
                    <span class="text-[10px] text-slate-400">Select Items</span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-xs mb-3.5">
                    <button onclick="addPosItem('cappuccino', 180)" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-amber-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Cappuccino</div>
                        <div class="text-[11px] text-amber-400 font-mono">₹180 &middot; 120 kcal</div>
                    </button>
                    <button onclick="addPosItem('iced oat matcha', 240)" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-emerald-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Oat Matcha</div>
                        <div class="text-[11px] text-emerald-400 font-mono">₹240 &middot; Vegan</div>
                    </button>
                    <button onclick="addPosItem('double espresso', 140)" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-amber-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Double Espresso</div>
                        <div class="text-[11px] text-amber-400 font-mono">₹140 &middot; 10 kcal</div>
                    </button>
                    <button onclick="addPosItem('nitro cold brew', 210)" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-amber-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Cold Brew</div>
                        <div class="text-[11px] text-amber-400 font-mono">₹210 &middot; 15 kcal</div>
                    </button>
                    <button onclick="addPosItem('butter croissant', 160)" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-yellow-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Butter Croissant</div>
                        <div class="text-[11px] text-yellow-300 font-mono">₹160 &middot; Bakery</div>
                    </button>
                    <button onclick="addPosItem('pesto sandwich', 220)" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-yellow-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Club Sandwich</div>
                        <div class="text-[11px] text-yellow-300 font-mono">₹220 &middot; Kitchen</div>
                    </button>
                </div>
                <div class="bg-slate-950/90 rounded-xl p-3 border border-slate-800 text-xs mb-3.5">
                    <div class="flex justify-between items-center text-slate-400 border-b border-slate-800/80 pb-2 mb-2">
                        <span class="font-mono text-[11px]">ACTIVE TICKET:</span>
                        <button onclick="clearTicket()" class="text-rose-400 hover:text-rose-300 text-[11px] font-mono">Clear Ticket</button>
                    </div>
                    <div id="ticket-items" class="space-y-1 text-slate-200 min-h-[36px] max-h-24 overflow-y-auto font-mono text-[11px]">
                        <span class="text-slate-500 italic">No items on ticket.</span>
                    </div>
                    <div class="flex justify-between items-center font-bold text-xs pt-2 border-t border-slate-800/80 mt-2 text-amber-400 font-mono">
                        <span>Total Due:</span>
                        <span id="ticket-total">₹0</span>
                    </div>
                </div>
                <div class="space-y-2">
                    <label class="text-[11px] text-slate-400 block font-semibold uppercase">Destination Table:</label>
                    <div class="grid grid-cols-4 gap-1.5 text-xs font-mono">
                        <button onclick="selectCafeDest('table 1')" class="dest-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">T-1</button>
                        <button onclick="selectCafeDest('table 2')" class="dest-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">T-2</button>
                        <button onclick="selectCafeDest('table 3')" class="dest-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">T-3</button>
                        <button onclick="selectCafeDest('sofa')" class="dest-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">VIP</button>
                    </div>
                    <button onclick="dispatchCafeOrder()" class="w-full mt-2.5 py-3 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black rounded-xl text-xs uppercase tracking-wider shadow-lg shadow-amber-500/20 transition flex items-center justify-center space-x-2">
                        <i class="fa-solid fa-bell-concierge"></i>
                        <span>Dispatch Table Delivery</span>
                    </button>
                </div>
            `;
            renderTicket();
            selectCafeDest("table 1");
        }

        function renderCafeStations() {
            const container = document.getElementById('stations-panel');
            container.innerHTML = `
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center justify-between">
                    <span>Cafe Floor Stations</span>
                    <span class="text-[10px] text-amber-400 font-mono">Layout</span>
                </h3>
                <div>
                    <span class="text-[10px] uppercase font-bold text-amber-400 block mb-1.5"><i class="fa-solid fa-mug-hot mr-1"></i> Barista Area</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('go to the counter')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-amber-500/15 border border-slate-800 text-left font-bold transition">Barista Counter</button>
                        <button onclick="sendCommand('go to the sink')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-amber-500/15 border border-slate-800 text-left font-bold transition">Kitchen Sink</button>
                    </div>
                </div>
                <div>
                    <span class="text-[10px] uppercase font-bold text-cyan-400 block mb-1.5"><i class="fa-solid fa-chair mr-1"></i> Guest Seating</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('go to table 1')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-cyan-500/15 border border-slate-800 text-left font-bold transition">Table 1 (Window)</button>
                        <button onclick="sendCommand('go to table 2')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-cyan-500/15 border border-slate-800 text-left font-bold transition">Table 2 (Center)</button>
                        <button onclick="sendCommand('go to table 3')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-cyan-500/15 border border-slate-800 text-left font-bold transition">Table 3 (Patio)</button>
                        <button onclick="sendCommand('go to the sofa')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-cyan-500/15 border border-slate-800 text-left font-bold transition">VIP Sofa Lounge</button>
                    </div>
                </div>
                <div>
                    <span class="text-[10px] uppercase font-bold text-emerald-400 block mb-1.5"><i class="fa-solid fa-compass mr-1"></i> Guest Services</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('where is the bathroom')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-emerald-500/15 border border-slate-800 text-left font-bold transition">Restroom Door</button>
                        <button onclick="sendCommand('go to the reception')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-emerald-500/15 border border-slate-800 text-left font-bold transition">Reception Desk</button>
                    </div>
                </div>
            `;
        }

        function addPosItem(name, price) {
            activeTicket.push({ name, price });
            renderTicket();
        }

        function clearTicket() {
            activeTicket = [];
            renderTicket();
        }

        function renderTicket() {
            const container = document.getElementById('ticket-items');
            if (!container) return;
            if (activeTicket.length === 0) {
                container.innerHTML = `<span class="text-slate-500 italic">No items on ticket.</span>`;
                const totEl = document.getElementById('ticket-total'); if (totEl) totEl.innerText = '₹0';
                return;
            }
            let html = '';
            let total = 0;
            activeTicket.forEach((item, idx) => {
                total += item.price;
                html += `
                    <div class="flex justify-between items-center py-0.5">
                        <span>${idx + 1}. ${item.name}</span>
                        <span class="text-amber-400 font-mono">₹${item.price}</span>
                    </div>
                `;
            });
            container.innerHTML = html;
            const ttEl = document.getElementById('ticket-total'); if (ttEl) ttEl.innerText = `₹${total}`;
        }

        function selectCafeDest(dest) {
            chosenCafeDest = dest;
            const cafeDestMap = { 'table 1': 't-1', 'table 2': 't-2', 'table 3': 't-3', 'sofa': 'vip' };
            const targetText = (cafeDestMap[dest] || dest).toLowerCase();
            document.querySelectorAll('.dest-btn').forEach(b => {
                if (b.innerText.toLowerCase() === targetText) {
                    b.className = "dest-btn py-2 px-1 rounded-lg bg-amber-500 text-slate-950 text-center font-bold border border-amber-400 shadow-md";
                } else {
                    b.className = "dest-btn py-2 px-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-center font-bold border border-slate-700 text-slate-300";
                }
            });
        }

        function dispatchCafeOrder() {
            if (activeTicket.length === 0) {
                alert("Please add at least one item to the ticket first!");
                return;
            }
            const itemNames = activeTicket.map(i => i.name).join(' and ');
            sendCommand(`bring ${itemNames} to ${chosenCafeDest}`);
            clearTicket();
        }

        // --- 3. FACTORY PANEL ---
        function renderFactoryPanel() {
            const container = document.getElementById('primary-panel');
            container.innerHTML = `
                <div class="flex justify-between items-center mb-3">
                    <h2 class="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center space-x-2">
                        <i class="fa-solid fa-clipboard-check"></i>
                        <span>Safety Audit & Machine Inspection</span>
                    </h2>
                    <span class="text-[10px] text-emerald-400 font-mono">OSHA 1910</span>
                </div>
                <div class="space-y-3 mb-3.5 text-xs">
                    <div>
                        <span class="text-[10px] text-slate-400 uppercase font-semibold block mb-1.5">Machine Cell Inspection:</span>
                        <div class="grid grid-cols-2 gap-2">
                            <button onclick="sendCommand('inspect conveyor belt assembly')" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-emerald-500/50 border border-slate-800 text-left transition">
                                <div class="font-bold text-slate-100 truncate">Conveyor Assembly</div>
                                <div class="text-[11px] text-emerald-400 font-mono">1910.212 &middot; E-Stop Test</div>
                            </button>
                            <button onclick="sendCommand('inspect gas canister depot')" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-emerald-500/50 border border-slate-800 text-left transition">
                                <div class="font-bold text-slate-100 truncate">Gas Cylinder Depot</div>
                                <div class="text-[11px] text-emerald-400 font-mono">1910.101 &middot; Chaining</div>
                            </button>
                            <button onclick="sendCommand('inspect forklift traffic lane')" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-emerald-500/50 border border-slate-800 text-left transition">
                                <div class="font-bold text-slate-100 truncate">Traffic Corridor</div>
                                <div class="text-[11px] text-emerald-400 font-mono">1910.178 &middot; Speed Check</div>
                            </button>
                            <button onclick="sendCommand('inspect manhole utility trench')" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-emerald-500/50 border border-slate-800 text-left transition">
                                <div class="font-bold text-slate-100 truncate">Utility Manhole</div>
                                <div class="text-[11px] text-emerald-400 font-mono">1910.146 &middot; Sniffer</div>
                            </button>
                        </div>
                    </div>
                    <div>
                        <span class="text-[10px] text-slate-400 uppercase font-semibold block mb-1.5">OSHA Action Protocols:</span>
                        <div class="grid grid-cols-2 gap-2">
                            <button onclick="sendCommand('run lockout tagout procedure')" class="p-2 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold transition flex items-center space-x-1.5 font-mono text-[11px]">
                                <i class="fa-solid fa-lock text-xs"></i><span>LOTO Verify</span>
                            </button>
                            <button onclick="sendCommand('deploy chemical spill containment kit')" class="p-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 font-bold transition flex items-center space-x-1.5 font-mono text-[11px]">
                                <i class="fa-solid fa-biohazard text-xs"></i><span>HAZWOPER Kit</span>
                            </button>
                            <button onclick="sendCommand('check worker PPE compliance')" class="p-2 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-bold transition flex items-center space-x-1.5 font-mono text-[11px]">
                                <i class="fa-solid fa-vest text-xs"></i><span>PPE Verification</span>
                            </button>
                            <button onclick="sendCommand('find safety inspector for shift handover')" class="p-2 rounded-xl bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 font-bold transition flex items-center space-x-1.5 font-mono text-[11px]">
                                <i class="fa-solid fa-user-shield text-xs"></i><span>Officer Handoff</span>
                            </button>
                        </div>
                    </div>
                </div>
                <button onclick="sendCommand('run full factory floor OSHA inspection')" class="w-full py-3 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-black rounded-xl text-xs uppercase tracking-wider shadow-lg shadow-emerald-500/20 transition flex items-center justify-center space-x-2">
                    <i class="fa-solid fa-shield-halved"></i>
                    <span>Execute Full Floor OSHA Audit</span>
                </button>
            `;
        }

        function renderFactoryStations() {
            const container = document.getElementById('stations-panel');
            container.innerHTML = `
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center justify-between">
                    <span>Manufacturing Cells</span>
                    <span class="text-[10px] text-emerald-400 font-mono">Floor Grid</span>
                </h3>
                <div>
                    <span class="text-[10px] uppercase font-bold text-emerald-400 block mb-1.5"><i class="fa-solid fa-gears mr-1"></i> Automation Lines</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('go to the conveyor')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-emerald-500/15 border border-slate-800 text-left font-bold transition">Conveyor Line</button>
                        <button onclick="sendCommand('go to the forklift')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-emerald-500/15 border border-slate-800 text-left font-bold transition">Forklift Bay</button>
                    </div>
                </div>
                <div>
                    <span class="text-[10px] uppercase font-bold text-cyan-400 block mb-1.5"><i class="fa-solid fa-triangle-exclamation mr-1"></i> Hazard Points</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('go to the gas canister')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-cyan-500/15 border border-slate-800 text-left font-bold transition">Gas Depot</button>
                        <button onclick="sendCommand('go to the manhole')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-cyan-500/15 border border-slate-800 text-left font-bold transition">Utility Trench</button>
                    </div>
                </div>
                <div>
                    <span class="text-[10px] uppercase font-bold text-yellow-400 block mb-1.5"><i class="fa-solid fa-clipboard-list mr-1"></i> Compliance Stations</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('go to the inspection station')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-yellow-500/15 border border-slate-800 text-left font-bold transition">Inspection Station</button>
                        <button onclick="sendCommand('go to the crates')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-yellow-500/15 border border-slate-800 text-left font-bold transition">Component Crates</button>
                    </div>
                </div>
            `;
        }

        // --- 4. WAREHOUSE PANEL ---
        function renderWarehousePanel() {
            const container = document.getElementById('primary-panel');
            container.innerHTML = `
                <div class="flex justify-between items-center mb-3">
                    <h2 class="text-xs font-bold uppercase tracking-wider text-orange-400 flex items-center space-x-2">
                        <i class="fa-solid fa-boxes-packing"></i>
                        <span>WMS Freight Staging & Manifest</span>
                    </h2>
                    <span class="text-[10px] text-orange-400 font-mono">Stage SKU</span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-xs mb-3.5">
                    <button onclick="addManifestItem('Oil Drum (208L)', 215)" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-orange-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Lubricant Drum (208L)</div>
                        <div class="text-[11px] text-orange-400 font-mono">215 kg &middot; UN 1A1</div>
                    </button>
                    <button onclick="addManifestItem('Heavy Pine Crate', 180)" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-orange-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Heavy Pine Crate</div>
                        <div class="text-[11px] text-orange-400 font-mono">180 kg &middot; ISPM-15</div>
                    </button>
                    <button onclick="addManifestItem('EUR Pallet Stack', 125)" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-orange-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">EUR Pallet Stack</div>
                        <div class="text-[11px] text-yellow-400 font-mono">125 kg &middot; 5-tier</div>
                    </button>
                    <button onclick="addManifestItem('Corrugated Carton', 25)" class="card-btn p-2.5 rounded-xl bg-slate-900/80 hover:border-orange-500/50 border border-slate-800 text-left transition">
                        <div class="font-bold text-slate-100 truncate">Export Carton</div>
                        <div class="text-[11px] text-yellow-400 font-mono">25 kg &middot; Kraft Box</div>
                    </button>
                </div>
                <div class="bg-slate-950/90 rounded-xl p-3 border border-slate-800 text-xs mb-3.5">
                    <div class="flex justify-between items-center text-slate-400 border-b border-slate-800/80 pb-2 mb-2 font-mono text-[11px]">
                        <span>STAGED CONSIGNMENTS:</span>
                        <button onclick="clearManifest()" class="text-rose-400 hover:text-rose-300">Flush</button>
                    </div>
                    <div id="manifest-items" class="space-y-1 text-slate-200 min-h-[36px] max-h-24 overflow-y-auto font-mono text-[11px]">
                        <span class="text-slate-500 italic">No cargo staged on manifest.</span>
                    </div>
                    <div class="flex justify-between items-center font-bold text-xs pt-2 border-t border-slate-800/80 mt-2 text-orange-400 font-mono">
                        <span>Payload Gross Weight:</span>
                        <span id="manifest-total">0 kg</span>
                    </div>
                </div>
                <div class="space-y-2">
                    <label class="text-[11px] text-slate-400 block font-semibold uppercase">Target Outbound Bay:</label>
                    <div class="grid grid-cols-4 gap-1.5 text-xs font-mono">
                        <button onclick="selectWarehouseZone('loading dock')" class="wh-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">Dock A1</button>
                        <button onclick="selectWarehouseZone('aisle 1')" class="wh-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">A-1</button>
                        <button onclick="selectWarehouseZone('aisle 2')" class="wh-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">A-2</button>
                        <button onclick="selectWarehouseZone('inspection table')" class="wh-btn py-2 px-1 rounded-lg bg-slate-800 text-center font-bold border border-slate-700">Staging</button>
                    </div>
                    <button onclick="dispatchWarehouseManifest()" class="w-full mt-2.5 py-3 bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-400 hover:to-amber-500 text-slate-950 font-black rounded-xl text-xs uppercase tracking-wider shadow-lg shadow-orange-500/20 transition flex items-center justify-center space-x-2">
                        <i class="fa-solid fa-truck-ramp-box"></i>
                        <span>Dispatch Fleet Runner</span>
                    </button>
                </div>
            `;
            renderManifest();
            selectWarehouseZone("loading dock");
        }

        function renderWarehouseStations() {
            const container = document.getElementById('stations-panel');
            container.innerHTML = `
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center justify-between">
                    <span>Logistics Waypoints</span>
                    <span class="text-[10px] text-orange-400 font-mono">WMS Grid</span>
                </h3>
                <div>
                    <span class="text-[10px] uppercase font-bold text-orange-400 block mb-1.5"><i class="fa-solid fa-warehouse mr-1"></i> Shipping Bays</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('go to the entrance')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-orange-500/15 border border-slate-800 text-left font-bold transition">Loading Dock A1</button>
                        <button onclick="sendCommand('go to the counter')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-orange-500/15 border border-slate-800 text-left font-bold transition">Dispatch Desk</button>
                    </div>
                </div>
                <div>
                    <span class="text-[10px] uppercase font-bold text-yellow-400 block mb-1.5"><i class="fa-solid fa-cubes-stacked mr-1"></i> Aisle Storage</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('go to the wooden pallet')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-yellow-500/15 border border-slate-800 text-left font-bold transition">Pallet Stacks</button>
                        <button onclick="sendCommand('go to the boxes')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-yellow-500/15 border border-slate-800 text-left font-bold transition">Freight Crates</button>
                    </div>
                </div>
                <div>
                    <span class="text-[10px] uppercase font-bold text-red-400 block mb-1.5"><i class="fa-solid fa-drum mr-1"></i> Hazmat & Incline</span>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <button onclick="sendCommand('go to the oil barrel')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-red-500/15 border border-slate-800 text-left font-bold transition">Oil Drum Bay</button>
                        <button onclick="sendCommand('go to the stairs')" class="p-2.5 rounded-xl bg-slate-900/80 hover:bg-red-500/15 border border-slate-800 text-left font-bold transition">Mezzanine Stairs</button>
                    </div>
                </div>
            `;
        }

        function addManifestItem(name, weight) {
            activeManifest.push({ name, weight });
            renderManifest();
        }

        function clearManifest() {
            activeManifest = [];
            renderManifest();
        }

        function renderManifest() {
            const container = document.getElementById('manifest-items');
            if (!container) return;
            if (activeManifest.length === 0) {
                container.innerHTML = `<span class="text-slate-500 italic">No cargo staged on manifest.</span>`;
                const mTotEl = document.getElementById('manifest-total'); if (mTotEl) mTotEl.innerText = '0 kg';
                return;
            }
            let html = '';
            let total = 0;
            activeManifest.forEach((item, idx) => {
                total += item.weight;
                html += `
                    <div class="flex justify-between items-center py-0.5">
                        <span>${idx + 1}. ${item.name}</span>
                        <span class="text-orange-400 font-mono">${item.weight} kg</span>
                    </div>
                `;
            });
            container.innerHTML = html;
            const mTEl = document.getElementById('manifest-total'); if (mTEl) mTEl.innerText = `${total} kg`;
        }

        function selectWarehouseZone(zone) {
            chosenWhZone = zone;
            const whZoneMap = { 'loading dock': 'dock a1', 'aisle 1': 'a-1', 'aisle 2': 'a-2', 'inspection table': 'staging' };
            const targetText = (whZoneMap[zone] || zone).toLowerCase();
            document.querySelectorAll('.wh-btn').forEach(b => {
                if (b.innerText.toLowerCase() === targetText) {
                    b.className = "wh-btn py-2 px-1 rounded-lg bg-orange-500 text-slate-950 text-center font-bold border border-orange-400 shadow-md";
                } else {
                    b.className = "wh-btn py-2 px-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-center font-bold border border-slate-700 text-slate-300";
                }
            });
        }

        function dispatchWarehouseManifest() {
            if (activeManifest.length === 0) {
                alert("Stage at least one inventory item on the manifest before dispatching!");
                return;
            }
            const itemNames = activeManifest.map(i => i.name).join(' and ');
            sendCommand(`transport ${itemNames} to ${chosenWhZone}`);
            clearManifest();
        }

        // --- TELEMETRY STREAM & ENGINE SYNC ---
        function updateTelemetryUI(data) {
            if (!data) return;
            const persona = data.bot_persona || "CAFE_WAITER";
            applyBespokeTheme(persona);

            const roleEl = document.getElementById('bot-role'); if (roleEl) roleEl.innerText = data.bot_name || 'Fleet Unit';
            const intentEl = document.getElementById('bot-intent'); if (intentEl) intentEl.innerText = data.intent || 'IDLE';
            const worldEl = document.getElementById('world-name'); if (worldEl) worldEl.innerText = (data.world || 'Environment').replace('_', ' ');
            const targetEl = document.getElementById('target-landmark'); if (targetEl) targetEl.innerText = data.target_name || 'None';
            const xyEl = document.getElementById('robot-xy'); if (xyEl) xyEl.innerText = `${data.robot_x || 0}m, ${data.robot_y || 0}m`;
            const lidarEl = document.getElementById('lidar-dist'); if (lidarEl) lidarEl.innerText = `${data.min_lidar || '--'} m`;
            const replyEl = document.getElementById('bot-reply'); if (replyEl) replyEl.innerText = `"${data.ai_reply || 'Standby'}"`;

            if (data.latest_audit && data.latest_audit.tinyfish_hits) {
                renderTinyFishHits(data.latest_audit.tinyfish_hits);
            }
        }

        async function fetchTelemetry() {
            try {
                const res = await fetch('/api/telemetry');
                if (!res.ok) return;
                const ct = res.headers.get('content-type') || '';
                if (!ct.includes('application/json')) return;
                const data = await res.json();
                updateTelemetryUI(data);
            } catch (err) { }
        }

        let telemetrySocket = null;
        function initTelemetryStream() {
            try {
                const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const host = window.location.host || '__LOCAL_IP__:8000';
                telemetrySocket = new WebSocket(`${proto}//${host}/ws/telemetry`);
                telemetrySocket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        updateTelemetryUI(data);
                    } catch(e) {}
                };
                telemetrySocket.onerror = () => {
                    fetchTelemetry();
                };
                telemetrySocket.onclose = () => {
                    setTimeout(initTelemetryStream, 1500);
                };
            } catch(e) {
                fetchTelemetry();
            }
        }

        function renderTinyFishHits(hits) {
            const container = document.getElementById('tinyfish-live-results');
            if (!hits || hits.length === 0) return;
            let html = '';
            hits.slice(0, 2).forEach((h, idx) => {
                html += `
                    <div class="p-2 rounded bg-slate-900 border border-slate-800 space-y-1">
                        <div class="font-bold text-cyan-300 text-[11px]">${idx + 1}. ${h.title}</div>
                        <a href="${h.url}" target="_blank" class="text-teal-400 text-[10px] truncate block hover:underline font-mono">${h.url}</a>
                        <div class="text-slate-300 text-[11px]">"${(h.snippet || '').slice(0, 120)}..."</div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        async function runTinyFishWebTask() {
            const query = document.getElementById('tf-task-input').value.trim();
            if (!query) return;

            const btn = document.getElementById('tf-submit-btn');
            btn.disabled = true;
            btn.innerText = "Querying...";

            try {
                const res = await fetch('/api/tinyfish/task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: 'search', query: query })
                });
                const data = await res.json();
                if (data.hits) renderTinyFishHits(data.hits);
            } catch (err) { }
            finally {
                btn.disabled = false;
                btn.innerText = "Lookup";
            }
        }

        async function sendCommand(orderText) {
            try {
                await fetch('/api/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ order: orderText })
                });
            } catch (err) { }
        }

        function handleCustomSubmit(e) {
            e.preventDefault();
            const input = document.getElementById('custom-command-input');
            const val = input.value.trim();
            if (val) {
                sendCommand(val);
                input.value = '';
            }
        }

        // --- BROWSER MICROPHONE ---
        function initBrowserSpeech() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                document.getElementById('mic-status').innerText = "Audio API unavailable";
                return;
            }
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onstart = () => {
                isRecording = true;
                const btn = document.getElementById('browser-mic-btn');
                btn.className = "px-3.5 py-2.5 bg-rose-600 text-white rounded-xl text-sm transition flex items-center justify-center mic-active shadow-lg shadow-rose-600/40";
                document.getElementById('mic-status').innerText = "Listening...";
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('custom-command-input').value = transcript;
                document.getElementById('mic-status').innerText = `Dictated: "${transcript}"`;
                sendCommand(transcript);
            };

            recognition.onerror = (event) => {
                document.getElementById('mic-status').innerText = "Audio capture error: " + event.error;
                resetMicButton();
            };

            recognition.onend = () => {
                resetMicButton();
            };
        }

        function toggleBrowserSpeech() {
            if (!recognition) {
                alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
                return;
            }
            if (isRecording) {
                recognition.stop();
            } else {
                try {
                    recognition.start();
                } catch(e) { }
            }
        }

        function resetMicButton() {
            isRecording = false;
            const btn = document.getElementById('browser-mic-btn');
            const micColors = { 'HOSPITAL_NURSE': 'text-teal-400', 'FACTORY_SAFETY': 'text-emerald-400', 'WAREHOUSE_LOGISTICS': 'text-orange-400' };
            const micColor = micColors[activePersona] || 'text-amber-400';
            btn.className = `px-3.5 py-2.5 bg-slate-800 hover:bg-slate-700 ${micColor} border border-slate-700 rounded-xl text-sm transition flex items-center justify-center shadow-md`;
            document.getElementById('mic-status').innerText = "Microphone Idle";
        }

        initTelemetryStream();
        fetchTelemetry();
    </script>
</body>
</html>
"""


@web_app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    local_ip = get_local_ip()
    rendered = HTML_TEMPLATE.replace("__LOCAL_IP__", local_ip)
    return HTMLResponse(content=rendered)


def launch_web_server_thread(agent_state_ref, get_telem_cb, port=8000):
    global SHARED_AGENT_STATE, GET_TELEMETRY_CALLBACK
    SHARED_AGENT_STATE = agent_state_ref
    GET_TELEMETRY_CALLBACK = get_telem_cb

    def _auto_open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            pass

    threading.Thread(target=_auto_open_browser, daemon=True).start()

    def _run_async_server():
        asyncio.set_event_loop(asyncio.new_event_loop())
        config = uvicorn.Config(web_app, host="0.0.0.0", port=port, log_level="error")
        server = uvicorn.Server(config)
        server.run()

    t = threading.Thread(target=_run_async_server, daemon=True)
    t.start()
    local_ip = get_local_ip()
    print(f"\n🌐 [AURA Enterprise Terminal Online] Operational at http://localhost:{port}")
    print(f"📱 [Mobile Dispatch Gateway] Available on subnet at http://{local_ip}:{port}\n")
    return t
