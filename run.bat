@echo off
echo Starting Nebulator...
echo Open http://localhost:8000 in your browser
venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

