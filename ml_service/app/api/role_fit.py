from fastapi import APIRouter, HTTPException

from app.schemas.role_fit import RoleFitRequest, RoleFitResponse
from app.services.role_fit_service import compute_role_fit

router = APIRouter(prefix="/predict", tags=["Role Fit"])


@router.post("/role-fit", response_model=RoleFitResponse, summary="Compute employee role-fit score")
def role_fit_prediction(request: RoleFitRequest) -> RoleFitResponse:
    """
    Compares the employee's current skill proficiencies against the target role's
    minimum requirements and returns a fit score (0–100) with per-skill breakdown.

    Works without a trained model (algorithmic fallback). When role_fit_model.pkl
    exists the GBR refines the score.
    """
    try:
        return compute_role_fit(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
