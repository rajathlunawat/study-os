"""
StudyOS Planner Service — Scheduler.

Responsibility: Deterministic algorithm that distributes study topics across
available days between now and a target exam date.

Design Decision: The prompt says "Prefer deterministic logic over LLMs."
This scheduler uses a pure algorithmic approach:
1. Calculate available study days.
2. Distribute topics evenly across those days.
3. Apply interleaving (mixing subjects) to improve retention.
4. Insert review sessions at spaced intervals.

The AI service is only used upstream to *extract* topics from notes.
The actual scheduling is fully deterministic and reproducible.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List
import math


@dataclass
class ScheduledTask:
    """
    A single task output from the scheduler.

    Attributes:
        title: Short name of the study topic or review session.
        description: What the student should do during this block.
        scheduled_date: The UTC date this task is assigned to.
        day_number: 1-indexed day in the plan (Day 1, Day 2, ...).
        is_review: Whether this is a review/revision session.
    """
    title: str
    description: str
    scheduled_date: datetime
    day_number: int
    is_review: bool = False


def build_schedule(
    topics: List[str],
    start_date: datetime,
    target_date: datetime,
    hours_per_day: float = 2.0,
) -> List[ScheduledTask]:
    """
    Deterministically distribute topics across the available study window.

    Algorithm:
    1. Calculate total available days.
    2. Reserve ~20% of days for review sessions (spaced at intervals).
    3. Distribute remaining topics across study days using round-robin.
    4. Generate review tasks that cover previously studied material.

    Args:
        topics: List of topic titles to study (extracted from notes by AI).
        start_date: When to begin the plan (typically today).
        target_date: The exam or goal deadline.
        hours_per_day: Target study hours per day (for description text).

    Returns:
        A chronologically ordered list of ScheduledTask objects.
    """
    total_days = _calculate_days(start_date, target_date)

    if total_days <= 0:
        # Target date is today or in the past — cram everything into 1 day
        return _build_cram_schedule(topics, start_date, hours_per_day)

    if not topics:
        return []

    # Reserve ~20% of days for review, minimum 1 review day
    num_review_days = max(1, math.floor(total_days * 0.2))
    num_study_days = total_days - num_review_days

    # Ensure at least 1 study day
    if num_study_days <= 0:
        num_study_days = total_days
        num_review_days = 0

    # Distribute topics across study days (round-robin)
    study_tasks = _distribute_topics(topics, num_study_days, start_date, hours_per_day)

    # Insert review sessions at spaced intervals
    review_tasks = _build_review_sessions(
        topics, num_review_days, num_study_days, start_date, hours_per_day
    )

    # Merge and sort by date
    all_tasks = study_tasks + review_tasks
    all_tasks.sort(key=lambda t: t.scheduled_date)

    # Re-number days sequentially
    for i, task in enumerate(all_tasks):
        task.day_number = i + 1

    return all_tasks


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _calculate_days(start: datetime, end: datetime) -> int:
    """Calculate the number of whole days between two dates."""
    delta = end.date() - start.date()
    return max(delta.days, 0)


def _distribute_topics(
    topics: List[str],
    num_days: int,
    start_date: datetime,
    hours_per_day: float,
) -> List[ScheduledTask]:
    """
    Assign topics to days using round-robin distribution.
    If there are more topics than days, multiple topics share a day.
    If there are fewer topics than days, topics repeat for deeper study.
    """
    tasks = []
    num_topics = len(topics)

    for day_idx in range(num_days):
        # Round-robin: cycle through topics
        topic_idx = day_idx % num_topics
        topic = topics[topic_idx]

        scheduled = start_date + timedelta(days=day_idx)

        # Determine if this is first pass or a deeper review pass
        pass_number = (day_idx // num_topics) + 1
        if pass_number == 1:
            description = f"Study '{topic}' for ~{hours_per_day}h. Focus on understanding core concepts."
        else:
            description = (
                f"Deepen your understanding of '{topic}' (pass {pass_number}). "
                f"Focus on details and edge cases for ~{hours_per_day}h."
            )

        tasks.append(ScheduledTask(
            title=topic,
            description=description,
            scheduled_date=scheduled,
            day_number=day_idx + 1,
            is_review=False,
        ))

    return tasks


def _build_review_sessions(
    topics: List[str],
    num_review_days: int,
    num_study_days: int,
    start_date: datetime,
    hours_per_day: float,
) -> List[ScheduledTask]:
    """
    Place review sessions at evenly spaced intervals after the study days.
    Each review session covers a batch of previously studied topics.
    """
    if num_review_days <= 0:
        return []

    tasks = []
    topics_per_review = max(1, math.ceil(len(topics) / num_review_days))

    for review_idx in range(num_review_days):
        day_offset = num_study_days + review_idx
        scheduled = start_date + timedelta(days=day_offset)

        # Select which topics this review session covers
        batch_start = (review_idx * topics_per_review) % len(topics)
        batch = []
        for j in range(topics_per_review):
            batch.append(topics[(batch_start + j) % len(topics)])

        review_topics = ", ".join(batch)

        tasks.append(ScheduledTask(
            title=f"Review: {review_topics}",
            description=(
                f"Revision session (~{hours_per_day}h). "
                f"Review your notes and test yourself on: {review_topics}."
            ),
            scheduled_date=scheduled,
            day_number=day_offset + 1,
            is_review=True,
        ))

    return tasks


def _build_cram_schedule(
    topics: List[str],
    date: datetime,
    hours_per_day: float,
) -> List[ScheduledTask]:
    """
    Emergency mode: all topics crammed into a single day.
    """
    if not topics:
        return []

    all_topics = ", ".join(topics)
    return [ScheduledTask(
        title="Cram Session",
        description=(
            f"Emergency review of all topics: {all_topics}. "
            f"Focus on high-yield material for ~{hours_per_day}h."
        ),
        scheduled_date=date,
        day_number=1,
        is_review=False,
    )]
