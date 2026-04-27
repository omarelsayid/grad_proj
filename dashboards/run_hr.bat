@echo off
cd /d "%~dp0"
echo Starting HR Admin Dashboard on http://localhost:8501
streamlit run dashboard_hr.py --server.port 8501 --server.headless false
pause
