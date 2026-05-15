"""DataGenService Typer CLI iskeleti.

Senaryo komutları Faz 7'de bağlanacak. Şimdilik yalnız `info` komutu.
"""

from __future__ import annotations

import typer

from app.core.config import get_settings

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
    scenario: str = typer.Argument(..., help="Senaryo adı (Faz 7'de aktif)"),
) -> None:
    """Senaryo çalıştırıcı (placeholder — Faz 7)."""
    typer.echo(
        f"[placeholder] '{scenario}' senaryosu henüz bağlı değil. Faz 7'de eklenecek."
    )
    raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
