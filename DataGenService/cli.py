"""DataGenService Typer CLI."""

from __future__ import annotations

import json

import typer

from app.core.config import get_settings
from app.scenarios import (
    ScenarioRunRequest,
    TargetNotAllowedError,
    run_scenario_sync,
)

app = typer.Typer(help="DataGenService CLI — sentetik veri üretici.")


@app.command()
def info() -> None:
    """Mevcut ayarları yazdırır."""
    settings = get_settings()
    typer.echo(f"backend_base_url     : {settings.backend_base_url}")
    typer.echo(f"rabbitmq_url         : {settings.rabbitmq_url}")
    typer.echo(f"rabbitmq_exchange    : {settings.rabbitmq_exchange}")
    typer.echo(f"default_seed         : {settings.default_seed}")
    typer.echo(f"locale               : {settings.locale}")
    typer.echo(f"output_dir           : {settings.output_dir}")
    typer.echo(f"batch_size           : {settings.batch_size}")
    typer.echo(f"concurrency          : {settings.concurrency}")


@app.command()
def run(
    scenario: str = typer.Argument(..., help="Senaryo adı"),
    count: int | None = typer.Option(
        None, "--count", "-c", min=1, help="Senaryo ölçeği / kayıt sayısı."
    ),
    seed: int | None = typer.Option(None, "--seed", help="Deterministik seed."),
    target: str | None = typer.Option(
        None, "--target", "-t", help="Hedef: rest, rabbit veya file."
    ),
    batch_size: int | None = typer.Option(
        None, "--batch-size", min=1, help="Batch boyutu."
    ),
    concurrency: int | None = typer.Option(
        None, "--concurrency", min=1, help="Eşzamanlılık limiti."
    ),
) -> None:
    """Senaryo çalıştırır ve JSON özet yazar."""
    request = ScenarioRunRequest(
        count=count,
        seed=seed,
        target=target,
        batch_size=batch_size,
        concurrency=concurrency,
    )
    try:
        result = run_scenario_sync(
            scenario, request, settings=get_settings()
        )
    except TargetNotAllowedError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc
    except NotImplementedError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.YELLOW)
        raise typer.Exit(code=1) from exc

    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False))


if __name__ == "__main__":
    app()
