"""
StudyOS Recommendation Service — Recommendation Engine.

Responsibility: Ranks and recommends topics for the student to study next.

Design Decision: The engine uses a deterministic scoring algorithm rather 
than a black-box AI model. It balances two competing needs:
1. Remediation: Reviewing topics where the student has low quiz accuracy.
2. Progression: Covering new syllabus topics that haven't been studied yet.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class TopicCandidate:
    """
    Represents a potential topic to recommend.
    """
    title: str
    is_new: bool
    quiz_accuracy: float | None = None
    last_studied_days_ago: int | None = None


@dataclass
class RecommendedTopic:
    """
    The final output format for a recommended topic.
    """
    title: str
    reason: str
    priority_score: float


class RecommendationEngine:
    """
    Calculates priority scores to recommend what the student should study next.
    """

    @staticmethod
    def generate_recommendations(
        candidates: List[TopicCandidate], 
        max_results: int = 3
    ) -> List[RecommendedTopic]:
        """
        Rank candidates based on priority and return the top recommendations.

        Priority Algorithm:
        - High priority to previously studied topics with low quiz accuracy.
        - Medium priority to entirely new, uncovered topics.
        - Low priority to topics recently studied with high accuracy.
        """
        if not candidates:
            return []

        scored_topics = []

        for candidate in candidates:
            score, reason = RecommendationEngine._score_candidate(candidate)
            scored_topics.append(
                RecommendedTopic(
                    title=candidate.title,
                    reason=reason,
                    priority_score=round(score, 2),
                )
            )

        # Sort descending by priority score
        scored_topics.sort(key=lambda x: x.priority_score, reverse=True)

        return scored_topics[:max_results]

    @staticmethod
    def _score_candidate(candidate: TopicCandidate) -> tuple[float, str]:
        """
        Calculates a priority score (0.0 to 10.0) for a single candidate.
        Returns the score and a human-readable reason.
        """
        if candidate.is_new:
            # Progression: New topics get a baseline medium-high priority
            return 7.0, "New topic you haven't covered yet."

        score = 0.0
        reason = ""

        # Remediation: Heavily weight low accuracy
        if candidate.quiz_accuracy is not None:
            if candidate.quiz_accuracy < 50.0:
                score += 8.0
                reason = "Your quiz scores are low in this area."
            elif candidate.quiz_accuracy < 75.0:
                score += 5.0
                reason = "Needs some review to solidify concepts."
            else:
                score += 2.0
                reason = "You have a good grasp, but a quick review helps."
        else:
            # If no quiz data exists but it's not new, assign medium priority
            score += 4.0
            reason = "You haven't tested yourself on this recently."

        # Spacing: Add points if it's been a long time since last studied
        if candidate.last_studied_days_ago is not None:
            if candidate.last_studied_days_ago > 14:
                score += 2.0
                reason += " It's been a while since you looked at this."
            elif candidate.last_studied_days_ago <= 2:
                # Penalty for cramming recently
                score -= 2.0

        # Clamp score between 0.0 and 10.0
        final_score = max(0.0, min(score, 10.0))
        return final_score, reason.strip()
