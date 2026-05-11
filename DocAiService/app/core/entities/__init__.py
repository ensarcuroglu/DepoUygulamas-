"""Core entities."""

from app.core.entities.belge import Belge, BelgeAlani, BelgeTipi, ExtractionSonucu
from app.core.entities.irsaliye_taslagi import (
    IrsaliyeKalemiSchema,
    IrsaliyeTaslagiSchema,
    MetinAlani,
    SayisalAlan,
    TarihAlani,
)

__all__ = [
    "Belge",
    "BelgeAlani",
    "BelgeTipi",
    "ExtractionSonucu",
    "IrsaliyeKalemiSchema",
    "IrsaliyeTaslagiSchema",
    "MetinAlani",
    "SayisalAlan",
    "TarihAlani",
]
