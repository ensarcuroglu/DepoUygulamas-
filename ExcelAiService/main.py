"""ExcelAiService FastAPI entrypoint (placeholder, Adim 7'de dolacak)."""

from __future__ import annotations

import logging

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("excel-ai")

app = FastAPI(
    title="ExcelAiService",
    description="AI destekli Excel yorumlama ve WMS sema esleme mikroservisi.",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "ExcelAiService", "status": "scaffold"}
