@echo off

echo Starting StudyOS Backend (FastAPI)...
start cmd /k "cd backend && if not exist venv (echo Creating Virtual Environment... && python -m venv venv && echo Installing Dependencies... && venv\Scripts\pip install -r requirements.txt) && echo Starting FastAPI... && venv\Scripts\uvicorn app.main:app --reload"

echo Starting StudyOS Frontend (Next.js)...
start cmd /k "cd frontend && npm run dev"

echo StudyOS is now starting up in two separate windows!
echo It may take a minute or two on the very first run to install the Python dependencies.
echo Backend will be at: http://localhost:8000
echo Frontend will be at: http://localhost:3000
