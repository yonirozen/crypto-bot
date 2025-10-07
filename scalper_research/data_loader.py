from __future__ import annotations

from pathlib import Path
from typing import Optional

import polars as pl

from .config import DataConfig


def _scan(path: Path, fmt: str) -> pl.LazyFrame:
    if fmt == "parquet":
        return pl.scan_parquet(str(path))
    if fmt == "csv":
        return pl.scan_csv(str(path))
    raise ValueError(f"Unsupported format: {fmt}")


def load_l2_l3_deltas(cfg: DataConfig) -> pl.DataFrame:
    lf = _scan(cfg.lob_path, cfg.format)
    if cfg.start_ts_ns is not None:
        lf = lf.filter(pl.col("ts" if "ts" in lf.columns else "timestamp") >= cfg.start_ts_ns)
    if cfg.end_ts_ns is not None:
        lf = lf.filter(pl.col("ts" if "ts" in lf.columns else "timestamp") <= cfg.end_ts_ns)
    return lf.collect(streaming=True)


def load_trades(cfg: DataConfig) -> Optional[pl.DataFrame]:
    if cfg.trades_path is None:
        return None
    lf = _scan(cfg.trades_path, cfg.format)
    if cfg.start_ts_ns is not None:
        lf = lf.filter(pl.col("ts" if "ts" in lf.columns else "timestamp") >= cfg.start_ts_ns)
    if cfg.end_ts_ns is not None:
        lf = lf.filter(pl.col("ts" if "ts" in lf.columns else "timestamp") <= cfg.end_ts_ns)
    return lf.collect(streaming=True)


