from fastapi import APIRouter, HTTPException

from app.schemas.skill_gaps import SkillGapsResponse
from app.services.skill_gaps_service import analyze_skill_gaps

router = APIRouter(prefix="/analysis", tags=["Skill Gaps"])


@router.get(
    "/skill-gaps",
    response_model=SkillGapsResponse,
    summary="Org-wide skill demand vs. supply analysis",
)
def skill_gaps_analysis() -> SkillGapsResponse:
    """
    Queries live PostgreSQL data (with fallback to the precomputed baseline)
    and returns demand/supply ratios per skill, sorted by criticality.
    """
    try:
        return analyze_skill_gaps()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
