"""Minimal end-to-end ML workflow example using PyLabFlow.

This script demonstrates how to build a lightweight and reproducible ML workflow
by subclassing PyLabFlow's abstract `Component` and `WorkFlow` classes.

Workflow stages:
1. Load a tabular dataset from CSV.
2. Train a simple binary classifier.
3. Evaluate classification accuracy.

The example uses only the Python standard library + pandas and is deterministic
through explicit random seeds.
"""

from __future__ import annotations

import csv
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from plf.utils import Component, WorkFlow


class CSVDatasetLoader(Component):
    """Load a CSV dataset and create deterministic train/test splits."""

    def __init__(self):
        super().__init__()
        self.args = {
            "csv_path": str,
            "feature_col": str,
            "label_col": str,
            "test_fraction": float,
            "seed": int,
        }
        self.csv_path: str = ""
        self.feature_col: str = ""
        self.label_col: str = ""
        self.test_fraction: float = 0.2
        self.seed: int = 42

    def _setup(self, args: Dict[str, Any], P=None) -> Optional[Any]:
        self.csv_path = args["csv_path"]
        self.feature_col = args["feature_col"]
        self.label_col = args["label_col"]
        self.test_fraction = float(args["test_fraction"])
        self.seed = int(args["seed"])
        return self

    def load(self) -> Dict[str, List[float]]:
        """Return train/test splits for a single-feature binary dataset."""
        data = pd.read_csv(self.csv_path)
        shuffled = data.sample(frac=1.0, random_state=self.seed).reset_index(drop=True)

        split_index = int(len(shuffled) * (1.0 - self.test_fraction))
        train_df = shuffled.iloc[:split_index]
        test_df = shuffled.iloc[split_index:]

        return {
            "x_train": train_df[self.feature_col].astype(float).tolist(),
            "y_train": train_df[self.label_col].astype(int).tolist(),
            "x_test": test_df[self.feature_col].astype(float).tolist(),
            "y_test": test_df[self.label_col].astype(int).tolist(),
        }


@dataclass
class ThresholdModel:
    """Very small model: classifies by thresholding one numeric feature."""

    threshold: float = 0.0


class MeanThresholdTrainer(Component):
    """Train a simple threshold model from class means."""

    def __init__(self):
        super().__init__()
        self.args = {}

    def _setup(self, args: Dict[str, Any], P=None) -> Optional[Any]:
        return self

    def train(self, x_train: List[float], y_train: List[int]) -> ThresholdModel:
        """Fit threshold = average(mean(feature|0), mean(feature|1))."""
        neg_values = [x for x, y in zip(x_train, y_train) if y == 0]
        pos_values = [x for x, y in zip(x_train, y_train) if y == 1]

        if not neg_values or not pos_values:
            raise ValueError("Training data must contain both classes 0 and 1.")

        neg_mean = sum(neg_values) / len(neg_values)
        pos_mean = sum(pos_values) / len(pos_values)
        return ThresholdModel(threshold=(neg_mean + pos_mean) / 2.0)

    def predict(self, model: ThresholdModel, x_values: List[float]) -> List[int]:
        """Predict class 1 when feature >= threshold, else class 0."""
        return [1 if x >= model.threshold else 0 for x in x_values]


class AccuracyEvaluator(Component):
    """Evaluate classification accuracy."""

    def __init__(self):
        super().__init__()
        self.args = {}

    def _setup(self, args: Dict[str, Any], P=None) -> Optional[Any]:
        return self

    def evaluate(self, y_true: List[int], y_pred: List[int]) -> float:
        """Compute accuracy as correct_predictions / total_predictions."""
        if len(y_true) != len(y_pred):
            raise ValueError("y_true and y_pred must have equal length.")
        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        return correct / len(y_true) if y_true else 0.0


class MinimalMLWorkflow(WorkFlow):
    """Minimal reproducible ML workflow built on PyLabFlow abstractions."""

    def __init__(self):
        super().__init__()
        self.template = {"dataset", "trainer", "evaluator"}
        self.workflow_args: Dict[str, Any] = {}
        self.dataset_loader: Optional[CSVDatasetLoader] = None
        self.trainer: Optional[MeanThresholdTrainer] = None
        self.evaluator: Optional[AccuracyEvaluator] = None

    def _setup(self, args: Dict[str, Any], P=None) -> Optional[Any]:
        self.new(args)
        return self

    def new(self, args: Dict[str, Any]):
        """Validate and store workflow configuration arguments."""
        missing = self.template.difference(args.keys())
        if missing:
            raise ValueError(f"Missing workflow sections: {sorted(missing)}")
        self.workflow_args = args

    def prepare(self):
        """Instantiate and setup components for dataset, training, and evaluation."""
        self.dataset_loader = CSVDatasetLoader().setup(self.workflow_args["dataset"])
        self.trainer = MeanThresholdTrainer().setup(self.workflow_args["trainer"])
        self.evaluator = AccuracyEvaluator().setup(self.workflow_args["evaluator"])

    def run(self) -> Dict[str, float]:
        """Execute full workflow: load data, train model, predict, evaluate."""
        if not all([self.dataset_loader, self.trainer, self.evaluator]):
            raise RuntimeError("Call prepare() before run().")

        split_data = self.dataset_loader.load()
        model = self.trainer.train(split_data["x_train"], split_data["y_train"])
        predictions = self.trainer.predict(model, split_data["x_test"])
        accuracy = self.evaluator.evaluate(split_data["y_test"], predictions)

        return {
            "threshold": model.threshold,
            "accuracy": accuracy,
            "test_size": float(len(split_data["y_test"])),
        }

    def get_path(self, of: str, args: Optional[Dict] = None) -> str:
        """Return output path for known artifact names."""
        args = args or {}
        base_dir = args.get("base_dir", os.getcwd())

        if of == "metrics":
            return os.path.join(base_dir, "minimal_ml_metrics.json")
        raise NotImplementedError(f"Unknown artifact type: {of}")


def create_toy_dataset(csv_path: str, n_samples: int = 120, seed: int = 7) -> None:
    """Create a deterministic toy binary dataset for demonstration.

    Labels are generated by thresholding noisy values around 0.5.
    """
    rng = random.Random(seed)

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["feature", "label"])
        writer.writeheader()

        for _ in range(n_samples):
            feature = rng.random()
            noise = rng.uniform(-0.08, 0.08)
            label = 1 if (feature + noise) >= 0.5 else 0
            writer.writerow({"feature": round(feature, 6), "label": label})


def main() -> None:
    """Run the minimal ML workflow end-to-end."""
    data_path = os.path.join(os.path.dirname(__file__), "toy_binary_dataset.csv")
    create_toy_dataset(data_path)

    workflow = MinimalMLWorkflow().setup(
        {
            "dataset": {
                "csv_path": data_path,
                "feature_col": "feature",
                "label_col": "label",
                "test_fraction": 0.25,
                "seed": 42,
            },
            "trainer": {},
            "evaluator": {},
        }
    )
    workflow.prepare()
    metrics = workflow.run()

    print("Minimal ML workflow metrics:")
    print(f"  Threshold: {metrics['threshold']:.4f}")
    print(f"  Accuracy : {metrics['accuracy']:.4f}")
    print(f"  Test size: {int(metrics['test_size'])}")


if __name__ == "__main__":
    main()
