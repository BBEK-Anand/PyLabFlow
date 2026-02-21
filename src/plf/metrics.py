"""
Structured metric logging for experiment tracking.

This module provides a simple, local-first metric logging API that stores:
- Step-wise metric records in SQLite for fast querying.
- Step-wise metric records in JSONL on the file system for portability.
- Run metadata for reproducibility (config hash, args hash, log context).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union
from uuid import uuid4

import pandas as pd

from ._version import __version__
from .context import get_caller, get_shared_data
from .utils import Db, hash_args

__all__ = [
    "MetricLogger",
    "start_run",
    "end_run",
    "get_metrics",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _metric_tables() -> List[str]:
    return [
        """
        CREATE TABLE IF NOT EXISTS metric_runs (
            runid TEXT PRIMARY KEY,
            pplid TEXT NOT NULL,
            logid TEXT,
            args_hash TEXT,
            config_hash TEXT,
            config_path TEXT,
            run_name TEXT,
            status TEXT NOT NULL DEFAULT 'running'
                CHECK(status IN ('running', 'completed', 'failed', 'stopped')),
            created_at TEXT NOT NULL,
            ended_at TEXT,
            caller TEXT,
            plf_version TEXT,
            metadata_json TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS metrics (
            recid INTEGER PRIMARY KEY AUTOINCREMENT,
            runid TEXT NOT NULL,
            pplid TEXT NOT NULL,
            step INTEGER NOT NULL,
            split TEXT NOT NULL DEFAULT 'train',
            name TEXT NOT NULL,
            value REAL NOT NULL,
            created_at TEXT NOT NULL,
            extra_json TEXT,
            FOREIGN KEY(runid) REFERENCES metric_runs(runid),
            UNIQUE(runid, step, split, name)
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_metrics_pplid_step ON metrics(pplid, step);",
        "CREATE INDEX IF NOT EXISTS idx_metrics_runid ON metrics(runid);",
    ]


class MetricLogger:
    """
    Step-wise metric logger for a single pipeline run.

    Parameters
    ----------
    pplid : str
        Pipeline identifier.
    runid : str, optional
        Explicit run id. If None, a unique run id is generated.
    run_name : str, optional
        Friendly run name.
    data_path : str, optional
        Base lab data path. If omitted, uses runtime shared context.
    strict_ppl : bool, optional
        If True, validate that `pplid` exists in `ppls.db`.
    metadata : dict, optional
        Additional reproducibility metadata attached to the run.
    """

    def __init__(
        self,
        pplid: str,
        runid: Optional[str] = None,
        run_name: Optional[str] = None,
        data_path: Optional[str] = None,
        strict_ppl: bool = True,
        metadata: Optional[Dict] = None,
    ):
        if not pplid:
            raise ValueError("pplid is required")

        self.settings = get_shared_data()
        self.data_path = os.path.abspath(data_path or self.settings.get("data_path", ""))
        if not self.data_path:
            raise ValueError("Lab context not initialized. Run lab_setup() first or pass data_path.")

        self.pplid = pplid
        self.runid = runid or self._make_runid(pplid)
        self.run_name = run_name
        self.strict_ppl = strict_ppl
        self._last_step = -1
        self._closed = False

        self.metrics_db_path = os.path.join(self.data_path, "metrics.db")
        self.runs_dir = os.path.join(self.data_path, "Metrics", self.pplid, self.runid)
        os.makedirs(self.runs_dir, exist_ok=True)

        self._init_db()
        self.run_meta = self._build_run_meta(metadata=metadata)
        self._insert_run_meta()

    @staticmethod
    def _make_runid(pplid: str) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{pplid}_{stamp}_{uuid4().hex[:8]}"

    def _init_db(self) -> None:
        with Db(self.metrics_db_path) as db:
            for stmt in _metric_tables():
                db.execute(stmt)

    def _read_config(self) -> Dict:
        cfg_path = os.path.join(self.data_path, "Configs", f"{self.pplid}.json")
        if not os.path.exists(cfg_path):
            return {}
        with open(cfg_path, encoding="utf-8") as fp:
            return json.load(fp)

    def _fetch_args_hash(self) -> Optional[str]:
        ppls_db_path = os.path.join(self.data_path, "ppls.db")
        with Db(ppls_db_path) as db:
            rows = db.query("SELECT args_hash FROM ppls WHERE pplid = ?", (self.pplid,))
        if not rows:
            if self.strict_ppl:
                raise ValueError(f"pplid '{self.pplid}' not found in ppls.db")
            return None
        return rows[0][0]

    def _build_run_meta(self, metadata: Optional[Dict] = None) -> Dict:
        cfg = self._read_config()
        args_hash = self._fetch_args_hash()
        config_hash = hash_args(cfg) if cfg else None
        config_path = os.path.join("Configs", f"{self.pplid}.json") if cfg else None

        run_meta = {
            "runid": self.runid,
            "pplid": self.pplid,
            "run_name": self.run_name,
            "logid": self.settings.get("logid"),
            "caller": get_caller(),
            "args_hash": args_hash,
            "config_hash": config_hash,
            "config_path": config_path,
            "plf_version": __version__,
            "created_at": _utc_now(),
            "metadata": metadata or {},
        }

        with open(os.path.join(self.runs_dir, "meta.json"), "w", encoding="utf-8") as fp:
            json.dump(run_meta, fp, indent=2)

        return run_meta

    def _insert_run_meta(self) -> None:
        with Db(self.metrics_db_path) as db:
            db.execute(
                """
                INSERT INTO metric_runs (
                    runid, pplid, logid, args_hash, config_hash, config_path,
                    run_name, status, created_at, caller, plf_version, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.runid,
                    self.pplid,
                    self.run_meta["logid"],
                    self.run_meta["args_hash"],
                    self.run_meta["config_hash"],
                    self.run_meta["config_path"],
                    self.run_meta["run_name"],
                    "running",
                    self.run_meta["created_at"],
                    self.run_meta["caller"],
                    self.run_meta["plf_version"],
                    json.dumps(self.run_meta["metadata"], sort_keys=True),
                ),
            )

    def _append_jsonl(self, record: Dict) -> None:
        with open(os.path.join(self.runs_dir, "metrics.jsonl"), "a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, sort_keys=True) + "\n")

    def log_metric(
        self,
        step: int,
        name: str,
        value: Union[int, float],
        split: str = "train",
        extra: Optional[Dict] = None,
    ) -> None:
        """Log a single metric for a given step."""
        if self._closed:
            raise RuntimeError("Cannot log metric: run is already closed")
        if not isinstance(step, int) or step < 0:
            raise ValueError("step must be a non-negative integer")
        if step < self._last_step:
            raise ValueError("step must be non-decreasing for a run")
        if not name:
            raise ValueError("metric name is required")

        value = float(value)
        created_at = _utc_now()
        record = {
            "runid": self.runid,
            "pplid": self.pplid,
            "step": step,
            "split": split,
            "name": name,
            "value": value,
            "created_at": created_at,
            "extra": extra or {},
        }

        with Db(self.metrics_db_path) as db:
            db.execute(
                """
                INSERT OR REPLACE INTO metrics (
                    runid, pplid, step, split, name, value, created_at, extra_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.runid,
                    self.pplid,
                    step,
                    split,
                    name,
                    value,
                    created_at,
                    json.dumps(extra or {}, sort_keys=True),
                ),
            )

        self._append_jsonl(record)
        self._last_step = step

    def log_metrics(
        self,
        step: int,
        metrics: Dict[str, Union[int, float]],
        split: str = "train",
        extra: Optional[Dict] = None,
    ) -> None:
        """Log multiple metrics at a given step."""
        for name, value in metrics.items():
            self.log_metric(step=step, name=name, value=value, split=split, extra=extra)

    def end_run(self, status: str = "completed") -> None:
        """Close run tracking with final status."""
        if status not in {"completed", "failed", "stopped", "running"}:
            raise ValueError("status must be one of: running, completed, failed, stopped")
        ended_at = _utc_now()
        with Db(self.metrics_db_path) as db:
            db.execute(
                "UPDATE metric_runs SET status = ?, ended_at = ? WHERE runid = ?",
                (status, ended_at, self.runid),
            )
        self._closed = True


def start_run(
    pplid: str,
    run_name: Optional[str] = None,
    runid: Optional[str] = None,
    data_path: Optional[str] = None,
    strict_ppl: bool = True,
    metadata: Optional[Dict] = None,
) -> MetricLogger:
    """Create and return a MetricLogger for a pipeline run."""
    return MetricLogger(
        pplid=pplid,
        runid=runid,
        run_name=run_name,
        data_path=data_path,
        strict_ppl=strict_ppl,
        metadata=metadata,
    )


def end_run(logger: MetricLogger, status: str = "completed") -> None:
    """Convenience wrapper for ending a run."""
    logger.end_run(status=status)


def get_metrics(
    pplid: Optional[str] = None,
    runid: Optional[str] = None,
    split: Optional[str] = None,
    name: Optional[str] = None,
    data_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Query logged metrics and return a pandas DataFrame.
    """
    settings = get_shared_data()
    root = os.path.abspath(data_path or settings.get("data_path", ""))
    if not root:
        raise ValueError("Lab context not initialized. Run lab_setup() first or pass data_path.")

    db_path = os.path.join(root, "metrics.db")
    if not os.path.exists(db_path):
        return pd.DataFrame(
            columns=["runid", "pplid", "step", "split", "name", "value", "created_at", "extra_json"]
        )

    clauses = []
    params: List = []
    if pplid:
        clauses.append("pplid = ?")
        params.append(pplid)
    if runid:
        clauses.append("runid = ?")
        params.append(runid)
    if split:
        clauses.append("split = ?")
        params.append(split)
    if name:
        clauses.append("name = ?")
        params.append(name)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    query = (
        "SELECT runid, pplid, step, split, name, value, created_at, extra_json "
        f"FROM metrics{where} ORDER BY runid, step, name"
    )

    with Db(db_path) as db:
        rows = db.query(query, tuple(params))

    return pd.DataFrame(
        rows,
        columns=["runid", "pplid", "step", "split", "name", "value", "created_at", "extra_json"],
    )
