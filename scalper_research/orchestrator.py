from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import polars as pl

from .config import AppConfig, StrategyParams
from .data_loader import load_l2_l3_deltas, load_trades
from .engine import LOBEngine
from .strategy import StrategyContext, twosided_mm_strategy


def _events_from_polars(df: pl.DataFrame) -> Iterable[dict]:
    # Convert rows to dicts lazily; adapt field names to hftbacktest expected schema later
    for row in df.iter_rows(named=True):
        yield row


def run_single(cfg: AppConfig) -> Dict[str, Path]:
    cfg.backtest.output_dir.mkdir(parents=True, exist_ok=True)

    lob = load_l2_l3_deltas(cfg.data)
    trades = load_trades(cfg.data)

    engine = LOBEngine(
        feed_latency_ms=cfg.latency.feed_latency_ms,
        order_latency_ms=cfg.latency.order_latency_ms,
        jitter_ms=cfg.latency.jitter_ms,
        seed=cfg.latency.seed,
        maker_bps=cfg.fees.maker_bps,
        taker_bps=cfg.fees.taker_bps,
        funding_bps_per_8h=cfg.fees.funding_bps_per_8h,
        derivatives=cfg.fees.derivatives,
    )

    ctx = StrategyContext(
        inventory_target=cfg.strategy.params.inventory_target,
        quote_width_bps=cfg.strategy.params.quote_width_bps,
        imbalance_threshold=cfg.strategy.params.imbalance_threshold,
        cancel_cadence_ms=cfg.strategy.params.cancel_cadence_ms,
        max_orders_per_minute=cfg.strategy.params.max_orders_per_minute,
        order_size=cfg.strategy.params.order_size,
    )
    strategy = twosided_mm_strategy(ctx)

    result = engine.run(
        lob_events=_events_from_polars(lob),
        trade_events=_events_from_polars(trades) if trades is not None else None,
        strategy_cb=strategy,
        seed=cfg.backtest.seed,
    )

    outputs: Dict[str, Path] = {}
    if cfg.backtest.export_trades and result.trades:
        trades_path = cfg.backtest.output_dir / "trades.csv"
        pl.from_dicts(result.trades).write_csv(trades_path)
        outputs["trades"] = trades_path
    if cfg.backtest.export_pnl and result.pnl:
        pnl_path = cfg.backtest.output_dir / "pnl.csv"
        pl.from_dicts(result.pnl).write_csv(pnl_path)
        outputs["pnl"] = pnl_path

    if cfg.backtest.export_report:
        report_path = cfg.backtest.output_dir / "report.md"
        with report_path.open("w") as f:
            f.write("# Backtest Report\n\n")
            f.write(f"Symbol: {cfg.data.symbol}\n\n")
            if "trades" in outputs:
                f.write(f"Trades: {outputs['trades'].name}\n\n")
            if "pnl" in outputs:
                f.write(f"PnL: {outputs['pnl'].name}\n\n")
        outputs["report"] = report_path

    return outputs


def sweep_grid(cfg: AppConfig) -> List[Dict[str, Path]]:
    assert cfg.sweep is not None and cfg.sweep.param_grid, "No grid provided"

    keys = list(cfg.sweep.param_grid.keys())
    values = [cfg.sweep.param_grid[k] for k in keys]
    outputs: List[Dict[str, Path]] = []

    for combo in product(*values):
        params = dict(zip(keys, combo))
        cfg_mut = cfg.model_copy(deep=True)
        for k, v in params.items():
            if hasattr(cfg_mut.strategy.params, k):
                setattr(cfg_mut.strategy.params, k, v)  # type: ignore[arg-type]
        cfg_mut.backtest.output_dir = cfg.backtest.output_dir / (
            "grid_" + "_".join(f"{k}-{v}" for k, v in params.items())
        )
        outputs.append(run_single(cfg_mut))
    return outputs


def sweep_random(cfg: AppConfig, n_samples: int) -> List[Dict[str, Path]]:
    assert cfg.sweep is not None and cfg.sweep.param_grid, "No grid provided"
    rng = np.random.default_rng(cfg.backtest.seed)
    keys = list(cfg.sweep.param_grid.keys())
    outputs: List[Dict[str, Path]] = []
    for i in range(n_samples):
        cfg_mut = cfg.model_copy(deep=True)
        for k in keys:
            vals = cfg.sweep.param_grid[k]
            v = rng.choice(vals)
            if hasattr(cfg_mut.strategy.params, k):
                setattr(cfg_mut.strategy.params, k, v)  # type: ignore[arg-type]
        cfg_mut.backtest.output_dir = cfg.backtest.output_dir / f"random_{i:04d}"
        outputs.append(run_single(cfg_mut))
    return outputs


