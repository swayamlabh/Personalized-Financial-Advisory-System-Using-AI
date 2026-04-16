@echo off
echo ======================================
echo  Starting AI Financial Advisor Backend
echo  Server will run at: http://localhost:8000
echo  API docs at:        http://localhost:8000/docs
echo ======================================
echo.
cd /d "%~dp0backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
