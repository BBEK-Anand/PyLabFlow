from typing import Optional, Dict
import json
from pathlib import Path
import numpy as np

from plf.utils import WorkFlow


class MinimalMLWorkFlow(WorkFlow):
    """A minimal, self-contained ML workflow using NumPy.

    Demonstrates how to implement `new`, `prepare`, `run` and `get_path`.
    Training is a tiny linear regression via gradient descent.
    """

    def __init__(self):
        super().__init__()
        self.paths = ["model", "history"]
        self._state = {}

    def new(self, args: Dict):
        # expected args: lr, epochs, samples
        self.template = ["lr", "epochs", "samples"]
        # store defaults if not present
        self._args = {
            "lr": float(args.get("lr", 0.01)),
            "epochs": int(args.get("epochs", 5)),
            "samples": int(args.get("samples", 100)),
        }

    def prepare(self):
        # create synthetic dataset
        rng = np.random.RandomState(0)
        n = self._args["samples"]
        X = rng.randn(n, 1)
        true_w = 2.5
        y = X[:, 0] * true_w + 0.1 * rng.randn(n)

        self._state["X"] = X
        self._state["y"] = y
        self._state["w"] = rng.randn(1)  # init weight
        self._state["history"] = []
        return True

    def run(self):
        X = self._state["X"]
        y = self._state["y"]
        w = self._state["w"]
        lr = self._args["lr"]
        epochs = self._args["epochs"]

        for e in range(epochs):
            preds = X[:, 0] * w
            loss = float(((preds - y) ** 2).mean())
            # gradient for linear weight
            grad = 2 * ((preds - y) * X[:, 0]).mean()
            w = w - lr * grad
            self._state["history"].append({"epoch": e, "loss": loss})
            # allow pipeline to stop if requested
            try:
                if not self.P.should_running:
                    break
            except Exception:
                pass

        self._state["w"] = w

        # save model artifact and history
        model_path = Path(self.get_path(of="model", args={}))
        history_path = Path(self.get_path(of="history", args={}))

        np.savez(model_path, w=w)
        with open(history_path, "w", encoding="utf-8") as fh:
            json.dump(self._state["history"], fh, indent=2)

    def get_path(self, of: str, args: Optional[Dict] = None) -> str:
        pplid = args.get("pplid") if args and "pplid" in args else None
        if not pplid and getattr(self, "P", None):
            pplid = self.P.pplid
        if of == "model":
            return str(Path("Models") / f"{pplid}.npz")
        if of == "history":
            return str(Path("History") / f"{pplid}_history.json")
        raise ValueError(f"Unknown artifact type: {of}")

    def status(self):
        # return last loss
        hist = self._state.get("history", [])
        return {"last_loss": hist[-1]["loss"] if hist else None}
