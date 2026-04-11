from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import learning_path, role_fit, skill_gaps, turnover
from app.db.connection import close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing to pre-load (services use lazy loading)
    yield
    # Shutdown: close DB connection pool cleanly
    close_pool()


app = FastAPI(
    title="SkillSync ML Service",
    description=(
        "AI-powered HR predictions — turnover risk, role fit, "
        "org-level skill gaps, and personalised learning paths."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],   # Node.js backend
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(turnover.router)
app.include_router(role_fit.router)
app.include_router(skill_gaps.router)
app.include_router(learning_path.router)


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    return {"status": "ok", "service": "skillsync-ml"}
