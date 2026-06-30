"""
StudyOS Schemas — Study Plan.

Responsibility: Defines the Pydantic models for Study Plans and Tasks.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ── Task Schemas ──────────────────────────────────────────────────────────────

class StudyTaskUpdate(BaseModel):
    """
    Request payload to update a specific task (usually to mark it completed).
    """
    completed: bool | None = None
    scheduled_date: datetime | None = None


class StudyTaskResponse(BaseModel):
    """
    Response schema for a single task within a study plan.
    """
    id: int
    plan_id: int
    title: str
    description: str | None
    scheduled_date: datetime
    completed: bool

    model_config = ConfigDict(from_attributes=True)


# ── Plan Schemas ──────────────────────────────────────────────────────────────

class StudyPlanCreate(BaseModel):
    """
    Request payload to generate a new study plan.
    """
    topic: str = Field(..., description="The overarching subject of the study plan.")
    target_date: datetime = Field(..., description="The date of the exam or goal deadline.")
    hours_per_day: float = Field(2.0, gt=0, description="Target study hours per day.")


class StudyPlanResponse(BaseModel):
    """
    Response schema for a Study Plan, including its nested tasks.
    """
    id: int
    user_id: int
    title: str
    status: str
    created_at: datetime
    tasks: list[StudyTaskResponse] = Field(
        default_factory=list, description="Nested sequence of study tasks."
    )

    model_config = ConfigDict(from_attributes=True)
