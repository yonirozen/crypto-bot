from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class StrategyContext:
    inventory_target: float
    quote_width_bps: float
    imbalance_threshold: float
    cancel_cadence_ms: int
    max_orders_per_minute: int
    order_size: float


def twosided_mm_strategy(ctx: StrategyContext) -> Callable[[Any, int], None]:
    def run(exchange, seed: int) -> None:
        # Minimal placeholder: submit and cancel quotes via exchange methods
        # Adapt this to the exact hftbacktest exchange API
        _ = seed
        if hasattr(exchange, "quote_two_sided"):
            exchange.quote_two_sided(
                width_bps=ctx.quote_width_bps,
                size=ctx.order_size,
                max_orders_per_minute=ctx.max_orders_per_minute,
            )
    return run


