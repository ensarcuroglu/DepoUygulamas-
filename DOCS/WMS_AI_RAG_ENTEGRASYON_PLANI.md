# WmsAiService Dokuman Bilgi Asistani RAG Entegrasyon Plani

## Approach

Mevcut WmsAiService, tek chat endpoint'i uzerinden hem veri/metrik sorularini hem de dokuman/kilavuz sorularini yanitlayacak sekilde genisletilir. Slash command varsa rota kesin belirlenir; yoksa MiniLM-L6-v2 embedding + ChromaDB tabanli semantik router kullanilir. SQL rotasi mevcut Text-to-SQL pipeline'i, docs rotasi yeni RAG pipeline'i calistirir.

## Scope

- In: `POST /api/ai/chat`, `/sql` ve `/docs` kacis kapagi, iki yeni Chroma koleksiyonu, dokuman ingestion CLI, React AI Asistan chat akisi.
- Out: MySQL schema/Alembic migration, DocAiService extraction degisikligi, `WmsAiService/wms_chroma_db/` klasorunu topluca silen islemler.

## Action Items

- [x] Add shared vector config in `WmsAiService/vector_config.py`.
- [x] Add slash command parser in `WmsAiService/slash_commands.py`.
- [x] Add semantic router in `WmsAiService/semantic_router.py`.
- [x] Add docs RAG pipeline in `WmsAiService/docs_rag.py`.
- [x] Add LangChain `RunnableBranch` orchestration in `WmsAiService/chat_orchestrator.py`.
- [x] Add ingestion CLI in `WmsAiService/ingest_docs.py`.
- [x] Add WmsAiService `POST /api/ai/chat` response fields: `route`, `route_source`, `confidence`, `sources`.
- [x] Add BackendProje proxy route `/api/ai/chat`.
- [x] Update React AI assistant to call `/ai/chat`, show slash suggestions, render docs Markdown, and show sources.
- [x] Add focused WmsAiService unit tests.

## Validation

- [x] `cd WmsAiService && pytest tests/test_chat_rag_routing.py`
- [ ] `cd WmsAiService && python ingest_docs.py --all`
- [ ] `cd WmsAiService && pytest`
- [ ] `cd BackendProje && ruff check . && pytest -m unit`
- [ ] `cd ReactProje && npm run lint && npm run build`

## Operational Notes

Rebuild only the new RAG/router collections:

```powershell
cd WmsAiService
python ingest_docs.py --all
```

Manual acceptance examples:

- `/sql Dun kac palet geldi?` -> `route=sql`, `uretilen_sql` dolu.
- `/docs FEFO mantigi nedir?` -> `route=docs`, `uretilen_sql=null`, kaynaklar dolu.
- `Aktif palet sayisi kac?` -> semantic router SQL.
- `Sistem nasil calisir?` -> semantic router docs.
- Bilgi dokuman baglaminda yoksa -> `Bu konuda bilgi bulamadım`.

## Assumptions

- RAG v1 kaynaklari: `CLAUDE.md`, `DOCS/agent/**/*.md`, `DOCS/project_doc_ai_modulu.md`, servis README dosyalari ve `DOCKER_DEV.md`.
- Arsiv klasoru `biten_rapor_dosyalari/` indekslenmez.
- Ollama modeli `qwen2.5-coder:7b` kullanilmaya devam eder.
