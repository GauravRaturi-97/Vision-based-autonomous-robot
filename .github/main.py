"""
main.py - AURA-Fleet Cloud Production Entrypoint for Render
Exposes the FastAPI operations terminal and WebSocket telemetry bridge.
"""
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CONTROLLER_DIR = os.path.join(HERE, "controllers", "vision_bot_olama")
if CONTROLLER_DIR not in sys.path:
    sys.path.insert(0, CONTROLLER_DIR)

from core_web_app import web_app  # noqa: E402
import uvicorn  # noqa: E402

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:web_app", host="0.0.0.0", port=port)
