"""
Ratefluencer AI — Single startup script
Runs both Track 1 and Track 2 in one command.

Usage:
    python run.py

Track 1 (Influencer Intelligence) → http://localhost:8001
Track 2 (Content Creator Agent)   → http://localhost:8000
"""
import sys, os, threading, time, webbrowser
sys.stdout.reconfigure(encoding="utf-8")

# Add both backends to Python path
TRACK1 = os.path.join(os.path.dirname(__file__), "track1", "backened")
TRACK2 = os.path.join(os.path.dirname(__file__), "track2", "backend")
sys.path.insert(0, TRACK1)
sys.path.insert(0, TRACK2)

import uvicorn

def run_track1():
    print("[Track 1] Starting Influencer Intelligence → http://localhost:8001")
    uvicorn.run("main:app", host="127.0.0.1", port=8001,
                log_level="warning", app_dir=TRACK1)

def run_track2():
    time.sleep(2)   # slight delay so Track 1 starts first
    print("[Track 2] Starting Content Creator Agent → http://localhost:8000")
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000,
                log_level="warning", app_dir=TRACK2)

def open_browser():
    time.sleep(8)   # wait for both to start
    print("\n✓ Both servers ready!")
    print("  Track 1: http://localhost:8001")
    print("  Track 2: http://localhost:8000")
    print("\nOpening browser...")
    webbrowser.open("http://localhost:8001")

if __name__ == "__main__":
    print("=" * 50)
    print("   RATEFLUENCER AI — Starting Both Tracks")
    print("=" * 50)

    t1 = threading.Thread(target=run_track1, daemon=True)
    t2 = threading.Thread(target=run_track2, daemon=True)
    tb = threading.Thread(target=open_browser, daemon=True)

    t1.start()
    t2.start()
    tb.start()

    try:
        t1.join()
    except KeyboardInterrupt:
        print("\nShutting down both servers...")
