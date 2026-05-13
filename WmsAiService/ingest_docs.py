"""Rebuild router and documentation Chroma collections.

This script deletes only the named router/docs collections. It never removes
the full persistent Chroma directory because the existing SQL few-shot store
lives there too.

Markdown chunking uses LlamaIndex `MarkdownNodeParser` + `SentenceSplitter` so
heading hierarchy is preserved and oversized sections are split on sentence
boundaries instead of raw character offsets. Each chunk text starts with a
`Title > H2 > H3` breadcrumb so retrieved snippets keep their parent context.
Runtime (Chroma + LangChain) is unchanged; LlamaIndex is only used to produce
chunks here. If LlamaIndex is not installed (e.g. dry-run / dependency-light
environments) the script falls back to the previous heading+char splitter.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Callable, Iterable

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

# Legacy fallback splitter (karakter bazli)
CHUNK_SIZE = 1600
CHUNK_OVERLAP = 180

# LlamaIndex SentenceSplitter butcesi (~1200-1800 karakter)
NODE_CHUNK_SIZE_TOKENS = 400
NODE_CHUNK_OVERLAP_TOKENS = 50

# RAG asistani operatore yonelik calisir. Sadece DOCS/rag/ altindaki surec
# dokumanlari indekslenir. CLAUDE.md, DOCS/agent/**, README'ler ve docker/dev
# dokumanlari korpus disindadir — operatore "ruff check", "npm run lint",
# Clean Architecture katmanlari gibi seyler donmesin diye. Bu dosyalar
# gelistirici dokumantasyonudur; ileride ayri bir koleksiyonda servis
# edilirse buraya degil yeni bir DEV_DOC_SOURCE_PATTERNS listesine eklenir.
DOC_SOURCE_PATTERNS = [
    "DOCS/rag/**/*.md",
]


Chunk = dict
Chunker = Callable[[str, str], list[Chunk]]


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
    chunker, backend = _get_chunker()
    documents: list[Document] = []
    for path in iter_source_paths():
        raw_text = path.read_text(encoding="utf-8", errors="replace")
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        front_matter, text = _split_front_matter(raw_text)
        title = extract_title(text, path.stem)
        # Aliases icin tek bir gizli chunk: retrieval'da "FEFO" / "SKT onceligi"
        # gibi terimlere dogrudan vurus saglar.
        aliases = _coerce_str_list(front_matter.get("aliases"))
        audience = front_matter.get("audience") or "operator"
        verified = bool(front_matter.get("verified", False))
        if aliases:
            alias_chunk_text = f"{title}\n\nEs anlamlilar / aliases:\n- " + "\n- ".join(aliases)
            documents.append(
                Document(
                    page_content=alias_chunk_text,
                    metadata={
                        "source_path": rel_path,
                        "title": title,
                        "section": "Aliases",
                        "breadcrumb": f"{title} > Aliases",
                        "chunk_id": f"{rel_path}:aliases",
                        "sha256": _sha256(alias_chunk_text),
                        "chunker": backend,
                        "audience": audience,
                        "verified": verified,
                        "kind": "aliases",
                    },
                )
            )
        for index, chunk in enumerate(chunker(text, title), 1):
            content = chunk["text"].strip()
            if not content:
                continue
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "source_path": rel_path,
                        "title": title,
                        "section": chunk["section"],
                        "breadcrumb": chunk["breadcrumb"],
                        "chunk_id": f"{rel_path}:{index}",
                        "sha256": _sha256(content),
                        "chunker": backend,
                        "audience": audience,
                        "verified": verified,
                        "kind": "body",
                    },
                )
            )
    return documents


def _split_front_matter(text: str) -> tuple[dict[str, object], str]:
    """YAML front-matter'i govdeden ayir. Front-matter yoksa bos dict doner."""
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}, text
    # Sadece dosya basindaki bloga bak; aksi halde govdeyi olduğu gibi birak.
    leading_offset = len(text) - len(stripped)
    after_open = stripped[3:]
    # Kapanis "---" satirini bul (newline ile sinirli).
    closing = after_open.find("\n---")
    if closing == -1:
        return {}, text
    fm_text = after_open[:closing]
    body_start_in_stripped = 3 + closing + len("\n---")
    # Kapanistan sonra newline varsa onu da yutalim.
    if body_start_in_stripped < len(after_open) + 3:
        # after_open[closing+4] yerine stripped'de pozisyon
        pass
    body = stripped[body_start_in_stripped:].lstrip("\n")
    front_matter = _parse_simple_yaml(fm_text)
    return front_matter, body


def _parse_simple_yaml(text: str) -> dict[str, object]:
    """Bagimsiz, ek bagimlilik istemeyen yalin YAML parser.

    Sadece bu projedeki front-matter formatini destekler:
      - `anahtar: deger`
      - `anahtar: [a, b]`  (flow list)
      - `anahtar:` ardindan `- madde` satirlari (block list)
    Karmasik YAML icin yyaml/PyYAML kullanilmaz; bagimlilik eklemek bu modul
    icin oransiz olur.
    """
    result: dict[str, object] = {}
    current_key: str | None = None
    current_list: list[str] | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith(("  - ", "\t- ", "- ")) and current_key is not None:
            item = line.split("- ", 1)[1].strip().strip("\"'")
            if current_list is None:
                current_list = []
                result[current_key] = current_list
            current_list.append(item)
            continue
        if ":" in line:
            current_list = None
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if not value:
                current_key = key
                result[key] = []
                continue
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                items = [v.strip().strip("\"'") for v in inner.split(",") if v.strip()]
                result[key] = items
            else:
                lowered = value.lower()
                if lowered in {"true", "false"}:
                    result[key] = lowered == "true"
                else:
                    result[key] = value.strip("\"'")
            current_key = key
    return result


def _coerce_str_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


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


def _get_chunker() -> tuple[Chunker, str]:
    """LlamaIndex tercih edilir; import basarisizsa legacy splitter doner."""
    try:
        return _build_llamaindex_chunker(), "llamaindex"
    except ImportError:
        return _legacy_chunker, "legacy"


def _build_llamaindex_chunker() -> Chunker:
    from llama_index.core import Document as LIDocument
    from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter

    md_parser = MarkdownNodeParser()
    size_parser = SentenceSplitter(
        chunk_size=NODE_CHUNK_SIZE_TOKENS,
        chunk_overlap=NODE_CHUNK_OVERLAP_TOKENS,
    )

    def chunk(text: str, title: str) -> list[Chunk]:
        li_doc = LIDocument(text=text)
        header_nodes = md_parser.get_nodes_from_documents([li_doc])
        leaf_nodes = size_parser.get_nodes_from_documents(header_nodes)

        chunks: list[Chunk] = []
        for node in leaf_nodes:
            body = node.get_content().strip()
            if not body:
                continue
            headers = _headers_from_metadata(node.metadata)
            breadcrumb = _build_breadcrumb(title, headers)
            section = headers[-1] if headers else (title or "Genel")
            content = f"{breadcrumb}\n\n{body}" if breadcrumb else body
            chunks.append({"text": content, "section": section, "breadcrumb": breadcrumb})
        return chunks

    return chunk


def _headers_from_metadata(metadata: dict) -> list[str]:
    """MarkdownNodeParser metadata'sindan heading zincirini sirali cikar."""
    headers: list[tuple[int, str]] = []
    for key, value in metadata.items():
        if not isinstance(value, str):
            continue
        normalized = str(key).replace("_", " ").strip().lower()
        if not normalized.startswith("header"):
            continue
        rest = normalized[len("header"):].strip()
        try:
            level = int(rest) if rest else 1
        except ValueError:
            continue
        cleaned = value.strip()
        if cleaned:
            headers.append((level, cleaned))
    headers.sort(key=lambda item: item[0])
    return [value for _, value in headers]


def _build_breadcrumb(title: str, headers: list[str]) -> str:
    parts: list[str] = []
    if title:
        parts.append(title)
    for header in headers:
        if header and (not parts or parts[-1] != header):
            parts.append(header)
    return " > ".join(parts)


def _legacy_chunker(text: str, title: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    for section, body in chunk_markdown(text):
        body = body.strip()
        if not body:
            continue
        breadcrumb = _build_breadcrumb(title, [section] if section and section != title else [])
        content = f"{breadcrumb}\n\n{body}" if breadcrumb else body
        chunks.append({"text": content, "section": section, "breadcrumb": breadcrumb})
    return chunks


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
