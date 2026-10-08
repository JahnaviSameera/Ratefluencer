@echo off
echo Starting Ratefluencer AI - Both Tracks
echo =======================================
echo.

start "Track 1 - Influencer Intelligence (port 8001)" cmd /k "cd /d C:\Users\soura\OneDrive\Desktop\Ai_hackathon\track1\backened && set PYTHONUTF8=1 && python -m uvicorn main:app --port 8001"

timeout /t 3 /nobreak > nul

start "Track 2 - Content Creator (port 8000)" cmd /k "cd /d C:\Users\soura\OneDrive\Desktop\Ai_hackathon\track2\backend && set PYTHONUTF8=1 && python api_server.py"

echo.
echo Both servers starting...
echo Track 1: http://localhost:8001  (Influencer Intelligence)
echo Track 2: http://localhost:8000  (Content Creator)
echo.
timeout /t 5 /nobreak > nul

start http://localhost:8001
