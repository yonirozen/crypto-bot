from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

# Note: We avoid importing heavy hftbacktest types at module import time to keep CLI snappy


@dataclass
class ExecutionResult:
    trades: List[Dict[str, Any]]
    pnl: List[Dict[str, Any]]


class LOBEngine:
    def __init__(
        self,
        feed_latency_ms: float,
        order_latency_ms: float,
        jitter_ms: float,
        seed: int,
        maker_bps: float,
        taker_bps: float,
        funding_bps_per_8h: float,
        derivatives: bool,
    ) -> None:
        self.feed_latency_ms = feed_latency_ms
        self.order_latency_ms = order_latency_ms
        self.jitter_ms = jitter_ms
        self.rng = np.random.default_rng(seed)
        self.maker_bps = maker_bps
        self.taker_bps = taker_bps
        self.funding_bps_per_8h = funding_bps_per_8h
        self.derivatives = derivatives

    def _init_hft(self) -> None:
        # Import on demand to avoid import cost when simply printing help
        from hftbacktest import SimulatedExchange
        from hftbacktest.order_latency_models import ConstantLatency
        # For queue models, use conservative risk-averse by default
        from hftbacktest.queue_models import RiskAverseQueueModel

        self._exchange_cls = SimulatedExchange
        self._latency_cls = ConstantLatency
        self._queue_model_cls = RiskAverseQueueModel

    def run(
        self,
        lob_events: Iterable[dict],
        trade_events: Optional[Iterable[dict]],
        strategy_cb,
        seed: int,
    ) -> ExecutionResult:
        self._init_hft()
        from hftbacktest import SimulatedExchange
        from hftbacktest.order_latency_models import ConstantLatency
        from hftbacktest.queue_models import RiskAverseQueueModel

        # Build latency model with jitter overlay (simple gaussian clipped at 0)
        base_latency = ConstantLatency(self.feed_latency_ms / 1000.0, self.order_latency_ms / 1000.0)

        def jitter_seconds() -> float:
            if self.jitter_ms <= 0:
                return 0.0
            val = self.rng.normal(loc=0.0, scale=self.jitter_ms / 1000.0)
            return max(0.0, float(val))

        # Create exchange with queue and latency
        exchange = SimulatedExchange(
            queue_model=RiskAverseQueueModel(),
            latency_model=base_latency,
            extra_order_latency=jitter_seconds,
        )

        # Feed events into exchange. Expect dict-like events that hftbacktest accepts
        for ev in lob_events:
            exchange.on_lob_event(ev)
        if trade_events is not None:
            for ev in trade_events:
                exchange.on_trade_event(ev)

        # Run strategy callback which interacts with the exchange object
        strategy_cb(exchange, seed)

        # Collect results (placeholder fields; adapt to actual hftbacktest API)
        trades = getattr(exchange, "executed_trades", [])
        pnl = getattr(exchange, "pnl_time_series", [])
        return ExecutionResult(trades=trades, pnl=pnl)


