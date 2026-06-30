"""
StudyOS API — Study Plan Routes.

Responsibility: Endpoints for AI-generated study schedules.
Delegates logic to StudyPlanService.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db_session
from app.schemas.study_plan import StudyPlanCreate, StudyPlanResponse, StudyTaskResponse, StudyTaskUpdate

router = APIRouter()


@router.post("/generate", response_model=StudyPlanResponse, status_code=status.HTTP_201_CREATED)
def generate_study_plan(
    user_id: int,
    plan_in: StudyPlanCreate,
    db: Session = Depends(get_db_session)
) -> StudyPlanResponse:
    """
    Generate a new study plan and tasks based on a topic and target date.
    """
    # TODO: Delegate to study_plan_service.generate(db, user_id, plan_in)
    raise HTTPException(status_code=501, detail="StudyPlanService not yet implemented")


@router.get("/{plan_id}", response_model=StudyPlanResponse)
def get_study_plan(
    plan_id: int,
    db: Session = Depends(get_db_session)
) -> StudyPlanResponse:
    """
    Fetch an existing study plan and its tasks.
    """
    # TODO: Delegate to study_plan_service.get(db, plan_id)
    raise HTTPException(status_code=501, detail="StudyPlanService not yet implemented")


@router.patch("/tasks/{task_id}", response_model=StudyTaskResponse)
def update_study_task(
    task_id: int,
    task_in: StudyTaskUpdate,
    db: Session = Depends(get_db_session)
) -> StudyTaskResponse:
    """
    Update a study task (e.g., mark it as completed).
    """
    # TODO: Delegate to study_plan_service.update_task(db, task_id, task_in)
    raise HTTPException(status_code=501, detail="StudyPlanService not yet implemented")
