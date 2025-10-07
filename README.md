## Crypto Scalper Research (LOB Replay)

Goal: Realistic backtests via order-book replay with queue-aware fills, configurable latencies and fees, and parameter sweeps. No live API calls.

### Stack
- Python 3.11+
- hftbacktest (LOB replay, queue-position and latency modeling)
- polars, pyarrow (fast Parquet/CSV I/O)
- numpy, numba, pandas
- pydantic (config)
- typer (CLI)
- Optional: vectorbt for candle-level coarse sweeps (kept separate)

### Quickstart
1) Create a virtualenv and install deps:
```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Prepare local datasets (no API calls). Use Binance-style L2/L3 deltas and trades in Parquet/CSV. Update paths in `configs/example.toml`.

3) Run a backtest (single):
```bash
python -m scalper_research.cli run --config configs/example.toml
```

4) Run grid/random sweeps:
```bash
python -m scalper_research.cli sweep-grid --config configs/example.toml
python -m scalper_research.cli sweep-random --config configs/example.toml --n-samples 50
```

Outputs (trades, PnL, report) will be written under `backtest.output_dir` in the config.

Notes:
- `hftbacktest` integration is encapsulated in `scalper_research/engine.py`. You can swap datasets and exchange specifics later (e.g., MEXC) without changing the CLI.
- If `vectorbt` is desired for coarse sweeps, install it separately and use the optional module.

