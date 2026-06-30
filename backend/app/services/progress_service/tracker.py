"""
StudyOS Progress Service — Activity Tracker.

Responsibility: Logs user activity to maintain streaks and track daily engagement.

Design Decision: To keep the database schema minimal for V1 (and low RAM usage), 
we don't maintain a massive "ActivityLog" table with thousands of rows per user. 
Instead, we update simple state fields on the User model (e.g., last_study_date, 
current_streak). 
(Note: Since we haven't added these specific fields to the User schema yet, 
this file represents the logic that will drive them once the schema is expanded).
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.db.models.user import User

logger = get_logger(__name__)


class ProgressTracker:
    """
    Handles state updates for user study activity and streaks.
    """

    @staticmethod
    def log_study_activity(db: Session, user_id: int) -> int:
        """
        Logs that a user performed a study action today (e.g., reviewed a card,
        completed a quiz, or finished a study task). Updates their daily streak.

        Args:
            db: Database session.
            user_id: The ID of the student.

        Returns:
            The user's current streak count.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning("Failed to log activity: User %d not found.", user_id)
            return 0

        # Note: In a production schema, 'last_active_date' and 'current_streak'
        # would exist on the User model. For this scaffold, we demonstrate the logic.
        
        now_date = datetime.now(timezone.utc).date()
        
        # We simulate the logic using dynamic attributes for demonstration.
        # In actual SQLAlchemy, these must be defined in models/user.py.
        last_active = getattr(user, "last_active_date", None)
        current_streak = getattr(user, "current_streak", 0)

        if last_active == now_date:
            # Already logged activity today, streak remains the same
            return current_streak
            
        if last_active is None:
            # First time studying
            current_streak = 1
        else:
            # Check if they studied yesterday
            delta_days = (now_date - last_active).days
            if delta_days == 1:
                # Streak continues
                current_streak += 1
            else:
                # Streak broken
                current_streak = 1

        # Apply updates (assuming schema supports it)
        try:
            setattr(user, "last_active_date", now_date)
            setattr(user, "current_streak", current_streak)
            db.commit()
            logger.info("User %d streak updated to %d.", user_id, current_streak)
        except Exception as e:
            logger.error("Failed to update streak for user %d: %s", user_id, str(e))
            db.rollback()

        return current_streak
