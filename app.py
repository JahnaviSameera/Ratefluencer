"""
Ratefluencer AI — Unified Single App
ONE server · ONE port · ONE command

Run:  python app.py

  http://localhost:8000          → Track 1: Influencer Intelligence
  http://localhost:8000/creator  → Track 2: Content Creator Agent
  http://localhost:8000/docs     → API Documentation
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")

TRACK1_BE = os.path.join(os.path.dirname(__file__), "track1", "backened")
TRACK2_BE = os.path.join(os.path.dirname(__file__), "track2", "backend")
sys.path.insert(0, TRACK1_BE)
sys.path.insert(0, TRACK2_BE)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRouter
from pathlib import Path

app = FastAPI(title="Ratefluencer AI — Complete Platform", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── Track 1: import app and include its router ─────────────────────────
import main as t1_module
app.on_event("startup")(t1_module.startup)

# Include all Track 1 API routes (skip static/root routes)
t1_router = APIRouter()
for route in t1_module.app.routes:
    path = getattr(route, "path", "")
    if path in ("/", "") or not hasattr(route, "endpoint"):
        continue
    # Skip catch-all path routes from Track 1 — they would intercept /creator
    if ":path}" in path:
        continue
    if hasattr(route, "methods"):
        t1_router.routes.append(route)
app.include_router(t1_router)

# ── Track 2: import and include its router ─────────────────────────────
import api_server as t2_module

t2_router = APIRouter()
for route in t2_module.app.routes:
    path = getattr(route, "path", "")
    # Only include API routes, not static mounts or root
    if path.startswith("/api") and hasattr(route, "endpoint") and hasattr(route, "methods"):
        t2_router.routes.append(route)
app.include_router(t2_router)

# ── Static files ────────────────────────────────────────────────────────
T1_FE   = Path(TRACK1_BE).parent / "FRONTEND"
T2_FE   = Path(os.path.dirname(__file__)) / "track2" / "frontend"

# Track 1 JS
if (T1_FE / "js").exists():
    app.mount("/js", StaticFiles(directory=str(T1_FE / "js")), name="t1_js")

# Reels output files
reels = Path(TRACK1_BE) / "reels_output"
reels.mkdir(exist_ok=True)
app.mount("/files", StaticFiles(directory=str(reels)), name="files")

# ── Track 2 frontend — redirect /creator → /creator/ then serve static files
from fastapi.responses import RedirectResponse

@app.get("/creator", include_in_schema=False)
def creator_redirect():
    return RedirectResponse(url="/creator/", status_code=301)

if T2_FE.exists():
    app.mount("/creator", StaticFiles(directory=str(T2_FE), html=True), name="creator")

# ── Track 1 frontend at root (MUST be last) ─────────────────────────────
@app.get("/", include_in_schema=False)
@app.get("/{catchall:path}", include_in_schema=False)
def track1_home(catchall: str = ""):
    html = T1_FE / "Ratefluencer AI.html"
    if html.exists():
        return FileResponse(str(html), media_type="text/html")
    return {"error": "Frontend not found"}


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*55)
    print("   RATEFLUENCER AI — Unified Platform v2.0")
    print("="*55)
    print("  Influencer Hub:  http://localhost:8000")
    print("  Content Studio:  http://localhost:8000/creator")
    print("  API Docs:        http://localhost:8000/docs")
    print("="*55 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
