"""AsyncSqliteSaver lifecycle.

LangGraph'in `AsyncSqliteSaver` async context manager kullanir; SQLite baglantisi
acmak ve kapatmak icin app lifespan'inde acilip kapanmasi gerekir. Bu modul,
bu protokole tek noktadan erisim saglar.

Test'lerde gercek dosyaya yazmadan calismak icin `:memory:` ya da `MemorySaver`
tercih edilebilir; tests/conftest.py bu yola gider.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


def _ensure_parent_dir(path: str) -> None:
    if path == ":memory:":
        return
    parent = Path(path).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def open_sqlite_checkpointer(
    path: str,
) -> AsyncIterator[BaseCheckpointSaver]:
    """Open an AsyncSqliteSaver against `path` and yield it.

    Closes the SQLite connection on exit. Use this in FastAPI lifespan:

        async with open_sqlite_checkpointer(settings.sqlite_checkpoint_path) as saver:
            graph = build_graph(llm, checkpointer=saver)
            yield
    """
    _ensure_parent_dir(path)
    # If we cannot write to the directory, the saver will raise on first use.
    # Surface that early by attempting to ensure parent exists above.
    async with AsyncSqliteSaver.from_conn_string(path) as saver:
        yield saver


def is_writable_path(path: str) -> bool:
    """Best-effort precheck used by /healthz and startup logs."""
    if path == ":memory:":
        return True
    p = Path(path).expanduser()
    parent = p.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
        return os.access(parent, os.W_OK)
    except OSError:
        return False
