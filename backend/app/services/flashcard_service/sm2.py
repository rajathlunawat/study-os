"""
StudyOS Flashcard Service — SM-2 Scheduler.

Responsibility: Implements the SuperMemo-2 (SM-2) spaced repetition algorithm.
Calculates the next review date, updated ease factor, and interval
based on the student's self-reported recall score (0-5).

Design Decision: This is isolated into its own file because SM-2 is a
pure algorithm with no database or AI dependencies. This makes it
independently testable and swappable for SM-18, FSRS, or Anki's
algorithm later.

Reference: https://en.wikipedia.org/wiki/SuperMemo#Algorithm_SM-2
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class ReviewResult:
    """
    The output of the SM-2 algorithm after a review.
    
    Attributes:
        next_review: UTC timestamp for the next scheduled review.
        ease_factor: Updated difficulty multiplier (minimum 1.3).
        interval: Days until the next review.
        repetitions: Updated successful-recall streak count.
    """
    next_review: datetime
    ease_factor: float
    interval: int
    repetitions: int


def sm2_schedule(
    score: int,
    current_ease: float = 2.5,
    current_interval: int = 0,
    current_repetitions: int = 0,
) -> ReviewResult:
    """
    Apply the SM-2 algorithm to compute the next review schedule.

    Args:
        score: The student's self-assessed recall quality (0-5).
            0 — Complete blackout.
            1 — Incorrect; remembered upon seeing the answer.
            2 — Incorrect; answer seemed easy to recall.
            3 — Correct with serious difficulty.
            4 — Correct after hesitation.
            5 — Perfect response.
        current_ease: The card's current ease factor (default 2.5 for new cards).
        current_interval: The card's current interval in days.
        current_repetitions: How many times the card has been recalled correctly in a row.

    Returns:
        A ReviewResult with the updated scheduling fields.
    """
    if not 0 <= score <= 5:
        raise ValueError(f"Score must be between 0 and 5, got {score}.")

    if score >= 3:
        # Successful recall — increase the interval
        if current_repetitions == 0:
            interval = 1
        elif current_repetitions == 1:
            interval = 6
        else:
            interval = round(current_interval * current_ease)

        repetitions = current_repetitions + 1
    else:
        # Failed recall — reset to the beginning
        interval = 1
        repetitions = 0

    # Update ease factor using the SM-2 formula
    # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    ease_factor = current_ease + (0.1 - (5 - score) * (0.08 + (5 - score) * 0.02))

    # Enforce minimum ease factor of 1.3
    ease_factor = max(ease_factor, 1.3)

    # Calculate the next review timestamp
    next_review = datetime.now(timezone.utc) + timedelta(days=interval)

    return ReviewResult(
        next_review=next_review,
        ease_factor=round(ease_factor, 2),
        interval=interval,
        repetitions=repetitions,
    )
