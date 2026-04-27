@echo off
cd /d "%~dp0"
echo Starting Manager Dashboard on http://localhost:8502
streamlit run dashboard_manager.py --server.port 8502 --server.headless false
pause
