"""
StudyOS ML Pipeline — Synthetic Training Data Generator.

Generates statistically realistic student behavior data grounded in
educational research:

    1. Spaced-repetition research (Pimsleur / SM-2): flashcard_mastery
       reaching intervals > 21 days indicates durable long-term retention.
    2. Testing effect (Roediger & Karpicke): quiz_accuracy is a strong
       predictor but insufficient alone without syllabus breadth.
    3. Consistency / spacing effect: study streaks show diminishing returns
       past ~14 consecutive days (log-curve benefit).
    4. Syllabus coverage is the single strongest negative predictor —
       low coverage torpedoes readiness regardless of other metrics.

The generator creates multiple *student archetypes* (strong, moderate,
cramming, inconsistent, failing) and samples around their centroids
with calibrated noise to produce a realistic joint distribution.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_OUTPUT_FILE = DEFAULT_OUTPUT_DIR / "training_data.csv"
RANDOM_SEED = 42
MIN_SCORE = 0.0
MAX_SCORE = 100.0
PASS_THRESHOLD = 50.0


# ---------------------------------------------------------------------------
# Student Archetypes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StudentArchetype:
    """
    Defines the centroid (mean feature vector) and noise level for a
    student cluster.  Each archetype models a recognisable study pattern.

    Attributes:
        name: Human-readable archetype label.
        count: Number of samples to draw for this archetype.
        means: (quiz_acc, flashcard, task_compl, consistency, syllabus_cov)
        std: Standard deviation applied to *each* feature (before clipping).
        score_noise_std: Gaussian noise σ added to the computed target score.
    """
    name: str
    count: int
    means: Tuple[float, float, float, float, float]
    std: float
    score_noise_std: float


# Archetypes calibrated against educational research heuristics.
ARCHETYPES: List[StudentArchetype] = [
    # Strong students — high across the board
    StudentArchetype(
        name="strong",
        count=900,
        means=(0.88, 0.85, 0.90, 0.82, 0.92),
        std=0.07,
        score_noise_std=4.0,
    ),
    # Good students — solid but not perfect
    StudentArchetype(
        name="good",
        count=1000,
        means=(0.75, 0.72, 0.78, 0.70, 0.80),
        std=0.09,
        score_noise_std=5.5,
    ),
    # Average / moderate students
    StudentArchetype(
        name="moderate",
        count=1100,
        means=(0.60, 0.55, 0.62, 0.55, 0.60),
        std=0.12,
        score_noise_std=6.0,
    ),
    # Crammers — high quiz accuracy, low consistency & flashcard mastery
    StudentArchetype(
        name="cramming",
        count=600,
        means=(0.78, 0.30, 0.50, 0.25, 0.55),
        std=0.10,
        score_noise_std=7.0,
    ),
    # Inconsistent — sporadic effort, decent coverage
    StudentArchetype(
        name="inconsistent",
        count=600,
        means=(0.55, 0.50, 0.40, 0.20, 0.65),
        std=0.11,
        score_noise_std=6.5,
    ),
    # Struggling / failing students — low everything
    StudentArchetype(
        name="failing",
        count=800,
        means=(0.30, 0.20, 0.25, 0.15, 0.25),
        std=0.10,
        score_noise_std=5.0,
    ),
]


# ---------------------------------------------------------------------------
# Feature Names (canonical order used everywhere)
# ---------------------------------------------------------------------------

FEATURE_NAMES: List[str] = [
    "quiz_accuracy",
    "flashcard_mastery",
    "task_completion",
    "consistency_score",
    "syllabus_coverage",
]


# ---------------------------------------------------------------------------
# Score Computation
# ---------------------------------------------------------------------------

def _compute_exam_score(
    quiz_accuracy: np.ndarray,
    flashcard_mastery: np.ndarray,
    task_completion: np.ndarray,
    consistency_score: np.ndarray,
    syllabus_coverage: np.ndarray,
    rng: np.random.Generator,
    noise_std: float,
) -> np.ndarray:
    """
    Compute a realistic exam score from features using a *non-linear*
    scoring function that encodes educational research insights.

    Key modelling choices
    ---------------------
    * **Syllabus coverage penalty**: Below 40 % coverage the student gets
      a multiplicative penalty regardless of other strengths.  This is the
      single most damaging factor.
    * **Diminishing returns on consistency**: ``log(1 + 10x)`` saturates
      around x ≈ 0.8 — matching the finding that streaks beyond ~14 days
      add marginal benefit.
    * **Interaction term**: ``quiz_accuracy * syllabus_coverage`` rewards
      knowing *most* of the material *well*, not just acing a narrow slice.
    * **Noise**: Gaussian noise models real-world variance (exam luck, day-
      of stress, question sampling, etc.).
    """
    # Base weighted sum (linear component)
    base = (
        quiz_accuracy * 22.0
        + flashcard_mastery * 12.0
        + task_completion * 8.0
        + syllabus_coverage * 30.0
    )

    # Diminishing-returns consistency bonus (0 → ~10 pts max)
    consistency_bonus = 10.0 * np.log1p(10.0 * consistency_score) / np.log1p(10.0)

    # Interaction: breadth × depth synergy (0 → ~18 pts max)
    interaction = 18.0 * quiz_accuracy * syllabus_coverage

    # Penalty for very low coverage — even a quiz-ace fails without breadth
    coverage_penalty = np.where(
        syllabus_coverage < 0.40,
        0.6 + syllabus_coverage,  # multiplicative factor ∈ [0.6, 1.0)
        1.0,
    )

    raw = (base + consistency_bonus + interaction) * coverage_penalty

    # Add calibrated Gaussian noise
    noise = rng.normal(loc=0.0, scale=noise_std, size=raw.shape)
    noisy = raw + noise

    return np.clip(noisy, MIN_SCORE, MAX_SCORE)


# ---------------------------------------------------------------------------
# Generator Class
# ---------------------------------------------------------------------------

class StudyDataGenerator:
    """
    Generates a DataFrame of synthetic student records ready for
    model training.

    Usage::

        gen = StudyDataGenerator(seed=42)
        df = gen.generate()
        gen.save(df)
    """

    def __init__(self, seed: int = RANDOM_SEED) -> None:
        self._rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        archetypes: List[StudentArchetype] | None = None,
    ) -> pd.DataFrame:
        """
        Generate the full synthetic dataset.

        Args:
            archetypes: Override the default archetype list (useful for tests).

        Returns:
            DataFrame with columns: *FEATURE_NAMES*, ``exam_score``, ``passed``,
            ``archetype``.
        """
        archetypes = archetypes or ARCHETYPES
        frames: List[pd.DataFrame] = []

        for arch in archetypes:
            df_arch = self._sample_archetype(arch)
            frames.append(df_arch)

        df = pd.concat(frames, ignore_index=True)

        # Shuffle rows so archetypes aren't contiguous
        df = df.sample(frac=1.0, random_state=self._rng.integers(1 << 31)).reset_index(drop=True)

        return df

    def save(
        self,
        df: pd.DataFrame,
        path: Path | str = DEFAULT_OUTPUT_FILE,
    ) -> Path:
        """
        Persist the DataFrame to CSV.

        Args:
            df: The generated dataset.
            path: Target file path.

        Returns:
            Resolved Path to the saved CSV.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        return path.resolve()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sample_archetype(self, arch: StudentArchetype) -> pd.DataFrame:
        """
        Draw ``arch.count`` samples around the archetype centroid.
        """
        n = arch.count
        features = np.column_stack([
            self._clipped_normal(arch.means[i], arch.std, n)
            for i in range(len(FEATURE_NAMES))
        ])

        scores = _compute_exam_score(
            quiz_accuracy=features[:, 0],
            flashcard_mastery=features[:, 1],
            task_completion=features[:, 2],
            consistency_score=features[:, 3],
            syllabus_coverage=features[:, 4],
            rng=self._rng,
            noise_std=arch.score_noise_std,
        )

        df = pd.DataFrame(features, columns=FEATURE_NAMES)
        df["exam_score"] = np.round(scores, 1)
        df["passed"] = (df["exam_score"] >= PASS_THRESHOLD).astype(int)
        df["archetype"] = arch.name
        return df

    def _clipped_normal(
        self, mean: float, std: float, size: int
    ) -> np.ndarray:
        """
        Sample from N(mean, std) and clip to [0, 1].
        """
        samples = self._rng.normal(loc=mean, scale=std, size=size)
        return np.clip(samples, 0.0, 1.0)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate and save synthetic training data."""
    print("=" * 60)
    print("StudyOS — Synthetic Training Data Generator")
    print("=" * 60)

    generator = StudyDataGenerator()
    df = generator.generate()

    # Print summary statistics
    total = len(df)
    passed = df["passed"].sum()
    failed = total - passed
    print(f"\nGenerated {total:,} samples")
    print(f"  Passed (≥{PASS_THRESHOLD}): {passed:,} ({passed / total:.1%})")
    print(f"  Failed (<{PASS_THRESHOLD}): {failed:,} ({failed / total:.1%})")
    print(f"\nArchetype distribution:")
    for name, count in df["archetype"].value_counts().items():
        print(f"  {name:15s}: {count:,}")
    print(f"\nFeature statistics:")
    print(df[FEATURE_NAMES + ["exam_score"]].describe().round(3).to_string())

    out_path = generator.save(df)
    print(f"\n✓ Saved to: {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
