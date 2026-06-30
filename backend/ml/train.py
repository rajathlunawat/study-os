"""
StudyOS ML Pipeline — Model Training & Evaluation.

Trains two scikit-learn models for exam readiness prediction:

    1. **GradientBoostingRegressor** → predicts continuous exam_score (0-100).
    2. **RandomForestClassifier** → predicts binary pass/fail (≥ 50).

Both models are serialized with joblib into ``ml/models/`` for the
prediction service to load at runtime.

Usage::

    python -m ml.train            # from backend/
    python ml/train.py            # also works
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split

from ml.data_generator import FEATURE_NAMES, PASS_THRESHOLD

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_PATH = Path(__file__).resolve().parent / "data" / "training_data.csv"
MODELS_DIR = Path(__file__).resolve().parent / "models"
SCORE_MODEL_PATH = MODELS_DIR / "score_predictor.joblib"
CLASSIFIER_MODEL_PATH = MODELS_DIR / "pass_classifier.joblib"
FEATURE_IMPORTANCE_PATH = MODELS_DIR / "feature_importances.json"


# ---------------------------------------------------------------------------
# Hyper-parameters (tuned for the synthetic data scale)
# ---------------------------------------------------------------------------

REGRESSOR_PARAMS: Dict[str, Any] = {
    "n_estimators": 300,
    "max_depth": 5,
    "learning_rate": 0.08,
    "subsample": 0.85,
    "min_samples_split": 10,
    "min_samples_leaf": 5,
    "random_state": 42,
}

CLASSIFIER_PARAMS: Dict[str, Any] = {
    "n_estimators": 200,
    "max_depth": 8,
    "min_samples_split": 8,
    "min_samples_leaf": 4,
    "class_weight": "balanced",
    "random_state": 42,
}

TEST_SIZE = 0.20
RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# Trainer Class
# ---------------------------------------------------------------------------

class ModelTrainer:
    """
    Orchestrates loading data, training models, evaluating metrics,
    and serializing artifacts.
    """

    def __init__(self, data_path: Path | str = DATA_PATH) -> None:
        self.data_path = Path(data_path)
        self.df: pd.DataFrame | None = None
        self.X_train: np.ndarray | None = None
        self.X_test: np.ndarray | None = None
        self.y_train_score: np.ndarray | None = None
        self.y_test_score: np.ndarray | None = None
        self.y_train_pass: np.ndarray | None = None
        self.y_test_pass: np.ndarray | None = None
        self.regressor: GradientBoostingRegressor | None = None
        self.classifier: RandomForestClassifier | None = None

    # ------------------------------------------------------------------
    # 1. Load & Split
    # ------------------------------------------------------------------

    def load_data(self) -> pd.DataFrame:
        """Load the CSV training data and validate required columns."""
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Training data not found at {self.data_path}. "
                "Run `python -m ml.data_generator` first."
            )

        self.df = pd.read_csv(self.data_path)

        missing = set(FEATURE_NAMES + ["exam_score", "passed"]) - set(self.df.columns)
        if missing:
            raise ValueError(f"Missing columns in training data: {missing}")

        print(f"Loaded {len(self.df):,} samples from {self.data_path.name}")
        return self.df

    def split_data(self, test_size: float = TEST_SIZE) -> None:
        """
        Stratified train/test split for classification, simple split for
        regression (same indices used for both).
        """
        if self.df is None:
            raise RuntimeError("Call load_data() first.")

        X = self.df[FEATURE_NAMES].values
        y_score = self.df["exam_score"].values
        y_pass = self.df["passed"].values

        (
            self.X_train,
            self.X_test,
            self.y_train_score,
            self.y_test_score,
            self.y_train_pass,
            self.y_test_pass,
        ) = train_test_split(
            X,
            y_score,
            y_pass,
            test_size=test_size,
            random_state=RANDOM_STATE,
            stratify=y_pass,
        )

        print(
            f"Split → Train: {len(self.X_train):,}  |  Test: {len(self.X_test):,} "
            f"(test_size={test_size})"
        )

    # ------------------------------------------------------------------
    # 2. Train
    # ------------------------------------------------------------------

    def train_regressor(self) -> GradientBoostingRegressor:
        """Train a GradientBoostingRegressor for exam_score prediction."""
        print("\n--- Training GradientBoostingRegressor ---")
        self.regressor = GradientBoostingRegressor(**REGRESSOR_PARAMS)
        self.regressor.fit(self.X_train, self.y_train_score)
        print("  ✓ Regressor fitted.")
        return self.regressor

    def train_classifier(self) -> RandomForestClassifier:
        """Train a RandomForestClassifier for pass/fail prediction."""
        print("\n--- Training RandomForestClassifier ---")
        self.classifier = RandomForestClassifier(**CLASSIFIER_PARAMS)
        self.classifier.fit(self.X_train, self.y_train_pass)
        print("  ✓ Classifier fitted.")
        return self.classifier

    # ------------------------------------------------------------------
    # 3. Evaluate
    # ------------------------------------------------------------------

    def evaluate_regressor(self) -> Dict[str, float]:
        """Print and return regression metrics on the test set."""
        y_pred = self.regressor.predict(self.X_test)

        mse = mean_squared_error(self.y_test_score, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(self.y_test_score, y_pred)
        r2 = r2_score(self.y_test_score, y_pred)

        print("\n=== Regressor Evaluation (test set) ===")
        print(f"  MSE  : {mse:.3f}")
        print(f"  RMSE : {rmse:.3f}")
        print(f"  MAE  : {mae:.3f}")
        print(f"  R²   : {r2:.4f}")

        return {"mse": mse, "rmse": rmse, "mae": mae, "r2": r2}

    def evaluate_classifier(self) -> str:
        """Print and return the classification report on the test set."""
        y_pred = self.classifier.predict(self.X_test)

        report = classification_report(
            self.y_test_pass,
            y_pred,
            target_names=["Fail (<50)", "Pass (≥50)"],
        )

        print("\n=== Classifier Evaluation (test set) ===")
        print(report)
        return report

    # ------------------------------------------------------------------
    # 4. Feature Importances
    # ------------------------------------------------------------------

    def get_feature_importances(self) -> Dict[str, Dict[str, float]]:
        """
        Extract feature importance rankings from both models.

        Returns:
            Dict with keys ``regressor`` and ``classifier``, each mapping
            feature name → importance (sorted descending).
        """
        importances: Dict[str, Dict[str, float]] = {}

        if self.regressor is not None:
            reg_imp = dict(zip(FEATURE_NAMES, self.regressor.feature_importances_))
            importances["regressor"] = dict(
                sorted(reg_imp.items(), key=lambda kv: kv[1], reverse=True)
            )

        if self.classifier is not None:
            clf_imp = dict(zip(FEATURE_NAMES, self.classifier.feature_importances_))
            importances["classifier"] = dict(
                sorted(clf_imp.items(), key=lambda kv: kv[1], reverse=True)
            )

        return importances

    # ------------------------------------------------------------------
    # 5. Serialize
    # ------------------------------------------------------------------

    def save_models(self) -> None:
        """Serialize trained models and feature importances to disk."""
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        if self.regressor is not None:
            joblib.dump(self.regressor, SCORE_MODEL_PATH)
            print(f"\n✓ Regressor  → {SCORE_MODEL_PATH}")

        if self.classifier is not None:
            joblib.dump(self.classifier, CLASSIFIER_MODEL_PATH)
            print(f"✓ Classifier → {CLASSIFIER_MODEL_PATH}")

        importances = self.get_feature_importances()
        if importances:
            with open(FEATURE_IMPORTANCE_PATH, "w", encoding="utf-8") as f:
                json.dump(importances, f, indent=2)
            print(f"✓ Feature importances → {FEATURE_IMPORTANCE_PATH}")

    # ------------------------------------------------------------------
    # 6. Full Pipeline
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """
        Execute the complete training pipeline end-to-end.

        Returns:
            Dictionary with regression metrics and feature importances.
        """
        self.load_data()
        self.split_data()

        self.train_regressor()
        self.train_classifier()

        reg_metrics = self.evaluate_regressor()
        self.evaluate_classifier()

        importances = self.get_feature_importances()
        self.save_models()

        # Pretty-print feature importances
        print("\n=== Feature Importance Rankings ===")
        for model_name, imp in importances.items():
            print(f"\n  {model_name}:")
            for feat, score in imp.items():
                bar = "█" * int(score * 40)
                print(f"    {feat:22s} {score:.4f}  {bar}")

        return {"metrics": reg_metrics, "importances": importances}


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    """Train models from the command line."""
    print("=" * 60)
    print("StudyOS — Model Training Pipeline")
    print("=" * 60)

    trainer = ModelTrainer()
    results = trainer.run()

    r2 = results["metrics"]["r2"]
    print("\n" + "=" * 60)
    if r2 >= 0.70:
        print(f"✓ Training successful!  R² = {r2:.4f} (target ≥ 0.70)")
    else:
        print(f"⚠ R² = {r2:.4f} is below the 0.70 target. Review data or hyper-params.")
    print("=" * 60)


if __name__ == "__main__":
    main()
