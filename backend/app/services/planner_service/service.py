"""
StudyOS Planner Service — Main Service.

Responsibility: Orchestrates study plan creation and task management.
Uses AIService to extract topic names from notes, then feeds them into
the deterministic scheduler. Persists results to SQLite.
"""

from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import DocumentNotFoundError, StudyOSException
from app.core.logging_config import get_logger
from app.db.models.study_plan import StudyPlan, StudyTask
from app.schemas.study_plan import StudyPlanCreate, StudyTaskUpdate
from app.services.ai_service import AIService
from app.services.planner_service.scheduler import build_schedule

logger = get_logger(__name__)


class PlannerService:
    """
    Public API for study plan operations.
    """

    def __init__(self, ai_service: AIService | None = None):
        self.ai = ai_service or AIService()

    def generate(
        self, db: Session, user_id: int, plan_in: StudyPlanCreate
    ) -> StudyPlan:
        """
        Generate a study plan from the student's notes.

        Flow:
        1. Use AIService to extract topic names from notes (the only AI step).
        2. Feed topics into the deterministic scheduler algorithm.
        3. Persist the StudyPlan and StudyTask rows.

        Args:
            db: Database session.
            user_id: The student's ID.
            plan_in: Request payload with topic, target_date, hours_per_day.

        Returns:
            The persisted StudyPlan ORM object with tasks loaded.
        """
        # 1. Extract topics via AI (or fall back to a single topic)
        topics = self._extract_topics(db, user_id, plan_in.topic)

        if not topics:
            topics = [plan_in.topic]

        # 2. Run the deterministic scheduler
        now = datetime.now(timezone.utc)
        scheduled_tasks = build_schedule(
            topics=topics,
            start_date=now,
            target_date=plan_in.target_date,
            hours_per_day=plan_in.hours_per_day,
        )

        # 3. Persist the plan
        db_plan = StudyPlan(
            user_id=user_id,
            title=f"Study Plan: {plan_in.topic}",
            status="active",
        )
        db.add(db_plan)
        db.flush()

        for task in scheduled_tasks:
            db_task = StudyTask(
                plan_id=db_plan.id,
                title=task.title,
                description=task.description,
                scheduled_date=task.scheduled_date,
                completed=False,
            )
            db.add(db_task)

        db.commit()
        db.refresh(db_plan)

        logger.info(
            "Study plan %d created for user %d with %d tasks.",
            db_plan.id, user_id, len(scheduled_tasks)
        )
        return db_plan

    def _extract_topics(
        self, db: Session, user_id: int, topic: str
    ) -> List[str]:
        """
        Use the AI study plan generator to extract topic names from notes.
        Falls back gracefully if AI fails — returns the raw topic as a single item.
        """
        try:
            raw_tasks = self.ai.generate_study_plan(
                db=db,
                user_id=user_id,
                topic=topic,
                num_days=7,
            )
            # Extract just the topic titles from the AI response
            return [t.get("title", topic) for t in raw_tasks if t.get("title")]
        except Exception as e:
            logger.warning(
                "AI topic extraction failed, using raw topic. Error: %s", str(e)
            )
            return [topic]

    # ── Task Management ───────────────────────────────────────────────────────

    @staticmethod
    def update_task(
        db: Session, task_id: int, task_in: StudyTaskUpdate
    ) -> StudyTask:
        """
        Update a study task (e.g., mark it as completed or reschedule).
        """
        task = db.query(StudyTask).filter(StudyTask.id == task_id).first()
        if not task:
            raise DocumentNotFoundError(
                message="Study task not found.",
                details={"task_id": task_id}
            )

        if task_in.completed is not None:
            task.completed = task_in.completed
        if task_in.scheduled_date is not None:
            task.scheduled_date = task_in.scheduled_date

        db.commit()
        db.refresh(task)

        logger.info("Study task %d updated (completed=%s).", task_id, task.completed)
        return task

    # ── Queries ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_by_id(db: Session, plan_id: int) -> StudyPlan | None:
        """
        Retrieve a study plan by ID, including nested tasks.
        """
        return db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()

    @staticmethod
    def get_by_user(db: Session, user_id: int) -> List[StudyPlan]:
        """
        Retrieve all study plans for a user, most recent first.
        """
        return (
            db.query(StudyPlan)
            .filter(StudyPlan.user_id == user_id)
            .order_by(StudyPlan.created_at.desc())
            .all()
        )
