from __future__ import annotations

from pathlib import Path

import typer

from .config import AppConfig, load_config
from .orchestrator import run_single, sweep_grid, sweep_random


app = typer.Typer(add_completion=False)


@app.command()
def run(
    config: Path = typer.Option(..., exists=True, help="Path to TOML config"),
):
    cfg: AppConfig = load_config(config)
    outputs = run_single(cfg)
    for k, v in outputs.items():
        typer.echo(f"{k}: {v}")


@app.command("sweep-grid")
def sweep_grid_cmd(
    config: Path = typer.Option(..., exists=True, help="Path to TOML config with sweep.param_grid"),
):
    cfg = load_config(config)
    out = sweep_grid(cfg)
    typer.echo(f"Completed {len(out)} grid runs")


@app.command("sweep-random")
def sweep_random_cmd(
    config: Path = typer.Option(..., exists=True, help="Path to TOML config with sweep.param_grid"),
    n_samples: int = typer.Option(20, help="Number of random samples"),
):
    cfg = load_config(config)
    out = sweep_random(cfg, n_samples=n_samples)
    typer.echo(f"Completed {len(out)} random runs")


def main() -> None:
    app()


if __name__ == "__main__":
    main()


