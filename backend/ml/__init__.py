"""
StudyOS ML Pipeline.

This package contains the machine learning training pipeline for
exam readiness prediction. It generates synthetic training data based on
educational research patterns, trains scikit-learn models, and exports
serialized .joblib artifacts consumed by the prediction service.

Modules:
    data_generator: Synthetic training data generation.
    train: Model training, evaluation, and serialization.
"""

from ml.data_generator import StudyDataGenerator
from ml.train import ModelTrainer

__all__ = [
    "StudyDataGenerator",
    "ModelTrainer",
]
