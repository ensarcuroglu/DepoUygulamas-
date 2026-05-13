"""Rebuild router and documentation Chroma collections.

This script deletes only the named router/docs collections. It never removes the
full persistent Chroma directory because the existing SQL few-shot store lives
there too.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Iterable

try:
    from langchain_core.documents import Document
except ModuleNotFoundError:  # pragma: no cover - dry-run without runtime deps
    class Document:
        def __init__(self, page_content: str, metadata: dict) -> None:
            self.page_content = page_content
            self.metadata = metadata

from route_examples import ROUTE_EXAMPLES
from vector_config import (
    CHROMA_PERSIST_DIR,
    DOCS_COLLECTION_NAME,
    ROUTER_COLLECTION_NAME,
    build_chroma,
)

SERVICE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SERVICE_DIR.parent
CHUNK_SIZE = 1600
CHUNK_OVERLAP = 180

DOC_SOURCE_PATTERNS = [
    "CLAUDE.md",
    "DOCS/rag/**/*.md",
    "DOCS/agent/**/*.md",
    "DOCS/project_doc_ai_modulu.md",
    "DOCKER_DEV.md",
    "DocAiService/README.md",
    "AgvSimService/README.md",
    "ReactProje/README.md",
    "ml_models/README.md",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--router", action="store_true", help="Rebuild router collection")
    parser.add_argument("--docs", action="store_true", help="Rebuild docs collection")
    parser.add_argument("--all", action="store_true", help="Rebuild router and docs")
    parser.add_argument("--dry-run", action="store_true", help="Print counts without writing")
    args = parser.parse_args()

    rebuild_router = args.all or args.router or not args.docs
    rebuild_docs = args.all or args.docs or not args.router

    if rebuild_router:
        router_docs = build_router_documents()
        if args.dry_run:
            print(f"router documents: {len(router_docs)}")
        else:
            rebuild_collection(ROUTER_COLLECTION_NAME, router_docs)
            print(f"rebuilt {ROUTER_COLLECTION_NAME}: {len(router_docs)} docs")

    if rebuild_docs:
        docs = build_markdown_documents()
        if args.dry_run:
            print(f"docs chunks: {len(docs)}")
        else:
            rebuild_collection(DOCS_COLLECTION_NAME, docs)
            print(f"rebuilt {DOCS_COLLECTION_NAME}: {len(docs)} chunks")


def rebuild_collection(collection_name: str, documents: list[Document]) -> None:
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    try:
        client.delete_collection(collection_name)
    except Exception:  # noqa: BLE001
        pass

    chroma = build_chroma(collection_name=collection_name)
    if documents:
        chroma.add_documents(documents)
    persist = getattr(chroma, "persist", None)
    if callable(persist):
        persist()


def build_router_documents() -> list[Document]:
    return [
        Document(
            page_content=example["text"],
            metadata={
                "route": example["route"],
                "source_path": "WmsAiService/route_examples.py",
                "title": "Semantic router examples",
                "section": example["route"],
                "chunk_id": f"router-{index}",
                "sha256": _sha256(example["text"]),
            },
        )
        for index, example in enumerate(ROUTE_EXAMPLES, 1)
    ]


def build_markdown_documents() -> list[Document]:
    documents: list[Document] = []
    for path in iter_source_paths():
        text = path.read_text(encoding="utf-8", errors="replace")
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        title = extract_title(text, path.stem)
        for index, (section, chunk) in enumerate(chunk_markdown(text), 1):
            chunk = chunk.strip()
            if not chunk:
                continue
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source_path": rel_path,
                        "title": title,
                        "section": section,
                        "chunk_id": f"{rel_path}:{index}",
                        "sha256": _sha256(chunk),
                    },
                )
            )
    return documents


def iter_source_paths() -> Iterable[Path]:
    seen: set[Path] = set()
    for pattern in DOC_SOURCE_PATTERNS:
        matches = sorted(REPO_ROOT.glob(pattern))
        for path in matches:
            if not path.is_file():
                continue
            if "biten_rapor_dosyalari" in path.parts:
                continue
            if "DOCS" in path.parts and "rag" in path.parts:
                rag_parts = path.relative_to(REPO_ROOT / "DOCS" / "rag").parts
                if any(part.startswith("_") for part in rag_parts):
                    continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield path


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def chunk_markdown(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_section = "Genel"
    current_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if current_lines:
                sections.extend(split_text(current_section, "\n".join(current_lines)))
                current_lines = []
            current_section = stripped.lstrip("#").strip() or current_section
        current_lines.append(line)

    if current_lines:
        sections.extend(split_text(current_section, "\n".join(current_lines)))
    return sections


def split_text(section: str, text: str) -> list[tuple[str, str]]:
    if len(text) <= CHUNK_SIZE:
        return [(section, text)]

    chunks: list[tuple[str, str]] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            paragraph_break = text.rfind("\n\n", start, end)
            if paragraph_break > start + 400:
                end = paragraph_break
        chunks.append((section, text[start:end]))
        if end >= len(text):
            break
        start = max(0, end - CHUNK_OVERLAP)
    return chunks


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    main()
