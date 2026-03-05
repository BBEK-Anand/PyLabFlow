"""Runnable minimal example showing how to use the MinimalMLWorkFlow.

Run this script from the repository root to create and run a small pipeline.
"""
from datetime import datetime
from plf._pipeline import PipeLine


def main():
    P = PipeLine()
    pplid = f"ml_example_{int(datetime.utcnow().timestamp())}"

    args = {
        "workflow": {
            "loc": "examples.ml_minimal.ml_workflow.MinimalMLWorkFlow",
            "args": {},
        },
        "args": {"lr": 0.1, "epochs": 5, "samples": 200},
    }

    P.new(pplid=pplid, args=args, prepare=True)
    P.run()
    print("Run finished. Model and history written under data path.")


if __name__ == "__main__":
    main()
