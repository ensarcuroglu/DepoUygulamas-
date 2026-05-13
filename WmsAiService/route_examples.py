"""Curated examples used by the semantic router."""

from __future__ import annotations

ROUTE_SQL = "sql"
ROUTE_DOCS = "docs"

ROUTE_EXAMPLES: list[dict[str, str]] = [
    {"route": ROUTE_SQL, "text": "Aktif palet sayisi kac?"},
    {"route": ROUTE_SQL, "text": "Dun kac palet geldi?"},
    {"route": ROUTE_SQL, "text": "Bugun yapilan mal kabul sayisini ver."},
    {"route": ROUTE_SQL, "text": "Stogu olmayan urunleri listele."},
    {"route": ROUTE_SQL, "text": "En cok stogu olan 10 urun hangileri?"},
    {"route": ROUTE_SQL, "text": "Son 7 gunde yapilan cikis hareketlerini raporla."},
    {"route": ROUTE_SQL, "text": "Depolara gore aktif palet dagilimi nedir?"},
    {"route": ROUTE_SQL, "text": "Bekleyen siparis sayisi kac?"},
    {"route": ROUTE_SQL, "text": "SKT'si 30 gunden az kalan lotlari getir."},
    {"route": ROUTE_SQL, "text": "Bugun yuklenecek sevkiyatlari listele."},
    {"route": ROUTE_DOCS, "text": "Sistem nasil calisir?"},
    {"route": ROUTE_DOCS, "text": "FEFO mantigi nedir?"},
    {"route": ROUTE_DOCS, "text": "Yerlestirme ve putaway sureci nasil isler?"},
    {"route": ROUTE_DOCS, "text": "RabbitMQ entegrasyonunda fallback davranisi nedir?"},
    {"route": ROUTE_DOCS, "text": "DocAiService hangi sinirlara sahip?"},
    {"route": ROUTE_DOCS, "text": "AgvSimService mimarisi nasil?"},
    {"route": ROUTE_DOCS, "text": "Backend Clean Architecture kurallari nelerdir?"},
    {"route": ROUTE_DOCS, "text": "AI servislerini gelistirirken nelere dikkat edilmeli?"},
    {"route": ROUTE_DOCS, "text": "Docker compose ile proje nasil baslatilir?"},
    {"route": ROUTE_DOCS, "text": "Slash command kacis kapagi nasil kullanilir?"},
]
