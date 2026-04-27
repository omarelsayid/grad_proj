"""HTTP clients for Node.js backend and ML service."""
import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

ML_URL  = os.getenv("ML_SERVICE_URL", "http://localhost:8000")
API_URL = os.getenv("API_URL",        "http://localhost:3000/api/v1")


def login_user(email: str, password: str) -> dict:
    resp = requests.post(
        f"{API_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_skill_gaps_ml() -> dict:
    resp = requests.get(f"{ML_URL}/analysis/skill-gaps", timeout=60)
    resp.raise_for_status()
    return resp.json()


def predict_turnover_ml(payload: dict) -> dict:
    resp = requests.post(f"{ML_URL}/predict/turnover", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def predict_role_fit_ml(payload: dict) -> dict:
    resp = requests.post(f"{ML_URL}/predict/role-fit", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()
