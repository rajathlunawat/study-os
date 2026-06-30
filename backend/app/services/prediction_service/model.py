"""
StudyOS Prediction Service — Readiness Model.

This module provides the public ``ReadinessModel.predict()`` API consumed by
the prediction service.  It attempts to load trained scikit-learn models
(GradientBoostingRegressor + RandomForestClassifier) from disk.  If models
are unavailable it falls back to the original deterministic weighted heuristic,
ensuring the service is always functional — even before training has run.

Architecture
------------
* **Lazy singleton** model loading: models are loaded once on first call and
  cached for the process lifetime.
* **Graceful degradation**: ``ModelLoadError`` is caught internally and logged;
  the weighted fallback is transparent to callers.
* **Same public API**: ``ReadinessModel.predict(features)`` returns the same
  ``Dict[str, Any]`` shape regardless of backend.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from app.services.prediction_service.features import ReadinessFeatures

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model Paths
# ---------------------------------------------------------------------------

_ML_MODELS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "ml" / "models"
_SCORE_MODEL_PATH = _ML_MODELS_DIR / "score_predictor.joblib"
_CLASSIFIER_PATH = _ML_MODELS_DIR / "pass_classifier.joblib"
_IMPORTANCES_PATH = _ML_MODELS_DIR / "feature_importances.json"

# Canonical feature order — MUST match ml.data_generator.FEATURE_NAMES
_FEATURE_ORDER: List[str] = [
    "quiz_accuracy",
    "flashcard_mastery",
    "task_completion",
    "consistency_score",
    "syllabus_coverage",
]


# ---------------------------------------------------------------------------
# Lazy Model Loader (singleton)
# ---------------------------------------------------------------------------

class _ModelCache:
    """
    Thread-safe-ish lazy loader for the trained ML models.

    On first access the models are deserialized from ``.joblib`` files.
    If loading fails (missing files, version mismatch, etc.) the fields
    remain ``None`` and the caller falls back to the heuristic.
    """

    _instance: Optional["_ModelCache"] = None

    def __init__(self) -> None:
        self.score_model: Any = None
        self.pass_model: Any = None
        self.feature_importances: Dict[str, Dict[str, float]] = {}
        self._loaded: bool = False

    @classmethod
    def get(cls) -> "_ModelCache":
        """Return the singleton instance, loading models on first call."""
        if cls._instance is None:
            cls._instance = cls()
        if not cls._instance._loaded:
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Attempt to load models from disk."""
        self._loaded = True  # Set early to avoid retry loops on failure

        try:
            import joblib  # noqa: delayed import to avoid hard dependency
        except ImportError:
            logger.warning(
                "joblib not installed — ML model loading disabled. "
                "Falling back to weighted heuristic."
            )
            return

        if _SCORE_MODEL_PATH.exists():
            try:
                self.score_model = joblib.load(_SCORE_MODEL_PATH)
                logger.info("Loaded score predictor from %s", _SCORE_MODEL_PATH)
            except Exception as exc:
                logger.warning("Failed to load score predictor: %s", exc)
        else:
            logger.info(
                "Score predictor not found at %s — using heuristic fallback.",
                _SCORE_MODEL_PATH,
            )

        if _CLASSIFIER_PATH.exists():
            try:
                self.pass_model = joblib.load(_CLASSIFIER_PATH)
                logger.info("Loaded pass classifier from %s", _CLASSIFIER_PATH)
            except Exception as exc:
                logger.warning("Failed to load pass classifier: %s", exc)
        else:
            logger.info(
                "Pass classifier not found at %s — using heuristic fallback.",
                _CLASSIFIER_PATH,
            )

        if _IMPORTANCES_PATH.exists():
            try:
                with open(_IMPORTANCES_PATH, "r", encoding="utf-8") as f:
                    self.feature_importances = json.load(f)
            except Exception as exc:
                logger.warning("Failed to load feature importances: %s", exc)

    @property
    def ml_available(self) -> bool:
        """True if at least the regressor loaded successfully."""
        return self.score_model is not None


# ---------------------------------------------------------------------------
# Heuristic Fallback (original V1 logic)
# ---------------------------------------------------------------------------

# V1 weights preserved as the deterministic fallback
_HEURISTIC_WEIGHTS: Dict[str, float] = {
    "syllabus_coverage": 0.35,
    "quiz_accuracy": 0.30,
    "flashcard_mastery": 0.15,
    "task_completion": 0.10,
    "consistency_score": 0.10,
}


def _heuristic_score(features: ReadinessFeatures) -> float:
    """Compute the weighted-sum heuristic score (0-100)."""
    score = (
        features.syllabus_coverage * _HEURISTIC_WEIGHTS["syllabus_coverage"]
        + features.quiz_accuracy * _HEURISTIC_WEIGHTS["quiz_accuracy"]
        + features.flashcard_mastery * _HEURISTIC_WEIGHTS["flashcard_mastery"]
        + features.task_completion * _HEURISTIC_WEIGHTS["task_completion"]
        + features.consistency_score * _HEURISTIC_WEIGHTS["consistency_score"]
    )
    return round(score * 100.0, 1)


# ---------------------------------------------------------------------------
# Insight Generation
# ---------------------------------------------------------------------------

def _generate_insights(
    features: ReadinessFeatures,
    importances: Dict[str, float] | None = None,
) -> List[str]:
    """
    Produce actionable study advice.

    When trained-model feature importances are available the advice is
    ordered by how much each feature actually matters to the model.
    Otherwise we fall back to hard-coded thresholds.
    """
    # Threshold rules: (feature_attr, threshold, advice)
    _RULES = [
        (
            "syllabus_coverage",
            0.6,
            "You have significant gaps in your syllabus coverage. "
            "Upload more notes or prioritise unread topics.",
        ),
        (
            "quiz_accuracy",
            0.7,
            "Your quiz accuracy is low. Focus on taking more quizzes "
            "and reviewing your mistakes.",
        ),
        (
            "consistency_score",
            0.4,
            "Your study consistency is dropping. Try to build a daily "
            "study streak, even if just for 15 minutes.",
        ),
        (
            "flashcard_mastery",
            0.5,
            "Many of your flashcards are due for review. Clear your "
            "backlog to improve long-term retention.",
        ),
        (
            "task_completion",
            0.5,
            "You have incomplete study tasks. Finishing them will "
            "strengthen your overall preparation.",
        ),
    ]

    # If we have importances, sort rules so the most-impactful feature
    # surfaces first in the insight list.
    if importances:
        _RULES = sorted(
            _RULES,
            key=lambda r: importances.get(r[0], 0.0),
            reverse=True,
        )

    insights: List[str] = []
    for attr, threshold, advice in _RULES:
        if getattr(features, attr, 1.0) < threshold:
            insights.append(advice)

    if not insights:
        insights.append(
            "Great job! You are consistently hitting your targets "
            "across all metrics."
        )

    return insights


# ---------------------------------------------------------------------------
# Band Classification
# ---------------------------------------------------------------------------

def _readiness_band(score: float) -> str:
    """Map a 0-100 score to a qualitative readiness band."""
    if score >= 85:
        return "Highly Prepared"
    elif score >= 70:
        return "On Track"
    elif score >= 50:
        return "Needs Review"
    return "At Risk"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ReadinessModel:
    """
    Lightweight model façade that routes prediction through a trained
    ML model or falls back to the weighted heuristic.

    Public contract::

        result = ReadinessModel.predict(features)
        # result == {
        #     "readiness_score": 72.3,
        #     "readiness_band": "On Track",
        #     "pass_probability": 0.87,
        #     "prediction_backend": "ml_model",
        #     "insights": ["..."],
        # }
    """

    @classmethod
    def predict(cls, features: ReadinessFeatures) -> Dict[str, Any]:
        """
        Calculate the readiness score.

        Args:
            features: The normalised ReadinessFeatures dataclass.

        Returns:
            A dictionary containing the final score (0-100), readiness band,
            pass probability, prediction backend used, and actionable insights.
        """
        cache = _ModelCache.get()

        if cache.ml_available:
            return cls._predict_ml(features, cache)
        return cls._predict_heuristic(features)

    # ------------------------------------------------------------------
    # ML-backed prediction
    # ------------------------------------------------------------------

    @classmethod
    def _predict_ml(
        cls,
        features: ReadinessFeatures,
        cache: _ModelCache,
    ) -> Dict[str, Any]:
        """Predict using the trained scikit-learn models."""
        feature_vector = np.array([[
            features.quiz_accuracy,
            features.flashcard_mastery,
            features.task_completion,
            features.consistency_score,
            features.syllabus_coverage,
        ]])

        # Regression: exam score
        raw_score: float = float(cache.score_model.predict(feature_vector)[0])
        score = round(min(max(raw_score, 0.0), 100.0), 1)

        # Classification: pass probability
        pass_prob = 0.5  # fallback
        if cache.pass_model is not None:
            proba = cache.pass_model.predict_proba(feature_vector)[0]
            # Class 1 (pass) probability
            pass_prob = round(float(proba[1]), 3)

        # Insights — use regressor importances if available
        reg_importances = cache.feature_importances.get("regressor")
        insights = _generate_insights(features, reg_importances)

        return {
            "readiness_score": score,
            "readiness_band": _readiness_band(score),
            "pass_probability": pass_prob,
            "prediction_backend": "ml_model",
            "insights": insights,
        }

    # ------------------------------------------------------------------
    # Heuristic fallback (original V1)
    # ------------------------------------------------------------------

    @classmethod
    def _predict_heuristic(cls, features: ReadinessFeatures) -> Dict[str, Any]:
        """Fallback to the deterministic weighted-sum model."""
        score = _heuristic_score(features)
        insights = _generate_insights(features)

        return {
            "readiness_score": score,
            "readiness_band": _readiness_band(score),
            "pass_probability": round(score / 100.0, 3),
            "prediction_backend": "heuristic",
            "insights": insights,
        }
