from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Union, Literal

from pydantic import BaseModel, Field

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover - fallback for older Pythons
    tomllib = None  # type: ignore


class DataConfig(BaseModel):
    lob_path: Path
    trades_path: Optional[Path] = None
    format: Literal["parquet", "csv"] = "parquet"
    exchange_style: Literal["binance", "generic"] = "binance"
    symbol: str = "BTCUSDT"
    start_ts_ns: Optional[int] = None
    end_ts_ns: Optional[int] = None


class FeeConfig(BaseModel):
    maker_bps: float = 0.0
    taker_bps: float = 0.0
    funding_bps_per_8h: float = 0.0
    derivatives: bool = False


class LatencyConfig(BaseModel):
    feed_latency_ms: float = 0.0
    order_latency_ms: float = 0.0
    jitter_ms: float = 0.0
    seed: int = 42


class StrategyParams(BaseModel):
    inventory_target: float = 0.0
    quote_width_bps: float = 5.0
    imbalance_threshold: float = 0.0
    cancel_cadence_ms: int = 1000
    max_orders_per_minute: int = 60
    order_size: float = 0.001


class StrategyConfig(BaseModel):
    name: str = "twosided_mm"
    params: StrategyParams = Field(default_factory=StrategyParams)


class BacktestConfig(BaseModel):
    seed: int = 42
    output_dir: Path = Path("outputs")
    export_trades: bool = True
    export_pnl: bool = True
    export_report: bool = True


class SweepConfig(BaseModel):
    mode: Literal["grid", "random"] = "grid"
    n_samples: Optional[int] = None
    # keys correspond to StrategyParams fields
    param_grid: Dict[str, List[Union[int, float]]] = Field(default_factory=dict)


class AppConfig(BaseModel):
    data: DataConfig
    fees: FeeConfig = Field(default_factory=FeeConfig)
    latency: LatencyConfig = Field(default_factory=LatencyConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    sweep: Optional[SweepConfig] = None


def load_config(path: Union[str, Path]) -> AppConfig:
    cfg_path = Path(path)
    if tomllib is None:
        raise RuntimeError(
            "tomllib not available. Use Python 3.11+ or install tomli and adapt loader."
        )
    with cfg_path.open("rb") as f:
        raw = tomllib.load(f)
    return AppConfig.model_validate(raw)


