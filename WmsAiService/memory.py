"""
Basit, in-memory konuşma hafızası.

Takip sorularını ("peki ya kategori X?") destekleyebilmek için her
session_id için son N etkileşimi tutar. Üretim ortamında Redis veya
LangChain `ChatMessageHistory` adapter'ı ile değiştirilmesi tavsiye edilir.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field

DEFAULT_HISTORY_LIMIT = 5
DEFAULT_SESSION_TTL_SEC = 60 * 30  # 30 dk
DEFAULT_MAX_SESSIONS = 200


@dataclass
class Turn:
    soru: str
    sql: str
    cevap: str
    ts: float = field(default_factory=time.time)


class ConversationStore:
    """Thread-safe LRU + TTL'li session deposu."""

    def __init__(
        self,
        history_limit: int = DEFAULT_HISTORY_LIMIT,
        session_ttl: float = DEFAULT_SESSION_TTL_SEC,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
    ) -> None:
        self._history_limit = history_limit
        self._ttl = session_ttl
        self._max_sessions = max_sessions
        self._lock = threading.RLock()
        self._sessions: OrderedDict[str, list[Turn]] = OrderedDict()

    def _evict_expired(self) -> None:
        cutoff = time.time() - self._ttl
        expired = [sid for sid, turns in self._sessions.items() if turns and turns[-1].ts < cutoff]
        for sid in expired:
            self._sessions.pop(sid, None)

    def _evict_overflow(self) -> None:
        while len(self._sessions) > self._max_sessions:
            self._sessions.popitem(last=False)

    def get(self, session_id: str) -> list[Turn]:
        with self._lock:
            self._evict_expired()
            turns = self._sessions.get(session_id, [])
            if turns:
                self._sessions.move_to_end(session_id)
            return list(turns)

    def append(self, session_id: str, turn: Turn) -> None:
        with self._lock:
            self._evict_expired()
            turns = self._sessions.get(session_id, [])
            turns.append(turn)
            if len(turns) > self._history_limit:
                turns = turns[-self._history_limit :]
            self._sessions[session_id] = turns
            self._sessions.move_to_end(session_id)
            self._evict_overflow()

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def render_history(self, session_id: str) -> str:
        """LLM promptuna gömülecek özet metin."""
        turns = self.get(session_id)
        if not turns:
            return "(önceki konuşma yok)"
        lines = []
        for i, t in enumerate(turns, 1):
            lines.append(f"{i}. Kullanıcı: {t.soru}")
            if t.sql == "[DOCS]":
                lines.append("   Asistan: Dokuman cevabi")
            else:
                lines.append(f"   Asistan SQL: {t.sql}")
        return "\n".join(lines)


# Modül seviyesinde tek instance — FastAPI dependency olarak da inject edilebilir
store = ConversationStore()
