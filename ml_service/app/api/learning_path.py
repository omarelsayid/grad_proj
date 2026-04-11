from fastapi import APIRouter, HTTPException

from app.schemas.learning_path import LearningPathRequest, LearningPathResponse
from app.services.learning_path_service import recommend_learning_path

router = APIRouter(prefix="/recommend", tags=["Learning Path"])


@router.post(
    "/learning-path",
    response_model=LearningPathResponse,
    summary="Recommend a personalised learning path",
)
def learning_path_recommendation(request: LearningPathRequest) -> LearningPathResponse:
    """
    Given an employee's missing skills and the available learning resources,
    ranks resources by predicted completion score and returns an ordered
    learning path with estimated completion time.

    Falls back to heuristic ranking when the GBDT model isn't trained yet.
    """
    try:
        return recommend_learning_path(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
