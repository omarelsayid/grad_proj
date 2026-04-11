from fastapi import APIRouter, HTTPException

from app.schemas.turnover import TurnoverRequest, TurnoverResponse
from app.services.turnover_service import predict_turnover

router = APIRouter(prefix="/predict", tags=["Turnover"])


@router.post("/turnover", response_model=TurnoverResponse, summary="Predict employee turnover risk")
def turnover_prediction(request: TurnoverRequest) -> TurnoverResponse:
    """
    Accepts 9 employee-level features and returns a risk score (0–100),
    risk level, and the top contributing factors.
    """
    try:
        return predict_turnover(request)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Turnover model not trained. Run training/train_turnover_model.py first.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
