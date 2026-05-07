"""Operatör Performans (LMS) repository soyutlamaları.

İki ayrı repository:
  IGorevPerformansEventRepository — outbox event log (insert + outbox poll)
  IOperatorVardiyaMetrikleriRepository — vardiya bazlı KPI özeti (upsert + sorgu)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.core.entities.operator_performans import (
    GorevPerformansEvent,
    OperatorVardiyaMetrikleri,
)


class IGorevPerformansEventRepository(ABC):
    """Append-only event log + transactional outbox tüketimi."""

    @abstractmethod
    def olustur(
        self, event: GorevPerformansEvent, auto_commit: bool = False
    ) -> GorevPerformansEvent:
        """Yeni bir event ekler. Hook akışında daima `auto_commit=False`
        kullanılır; commit, ana use case'in sahibi olduğu transaction
        tarafından yapılır (transactional outbox)."""
        ...

    @abstractmethod
    def bekleyen_eventleri_getir(self, limit: int = 500) -> List[GorevPerformansEvent]:
        """`aggregate_edildi=False` event'leri olusturma_tarihi ASC sırasıyla döner.
        Aggregator job tarafından çağrılır."""
        ...

    @abstractmethod
    def aggregate_edildi_isaretle(
        self, event_idleri: List[int], auto_commit: bool = True
    ) -> int:
        """Verilen event id'lerini `aggregate_edildi=True` olarak işaretler.
        İşaretlenen kayıt sayısını döner."""
        ...


class IOperatorVardiyaMetrikleriRepository(ABC):
    """Operatör + vardiya günü bazlı aggregate KPI özeti."""

    @abstractmethod
    def upsert_artir(
        self,
        kullanici_id: int,
        vardiya_tarihi: date,
        depo_id: Optional[int],
        yerlestirme_delta: int = 0,
        toplama_delta: int = 0,
        iptal_delta: int = 0,
        sure_saniye_delta: int = 0,
        auto_commit: bool = True,
    ) -> OperatorVardiyaMetrikleri:
        """Atomik upsert + delta artırımı.

        Kayıt yoksa oluşturur; varsa sayaçları artırır ve
        ortalama_gorev_suresi_sn değerini güncel sayaçlardan tekrar hesaplar.
        """
        ...

    @abstractmethod
    def getir_kullanici_tarih_ile(
        self, kullanici_id: int, vardiya_tarihi: date
    ) -> Optional[OperatorVardiyaMetrikleri]:
        ...

    @abstractmethod
    def getir_aralik(
        self,
        kullanici_id: Optional[int] = None,
        depo_id: Optional[int] = None,
        baslangic: Optional[date] = None,
        bitis: Optional[date] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> List[OperatorVardiyaMetrikleri]:
        """Tarih aralığı + opsiyonel kullanıcı/depo filtresi ile sorgu.
        İsim ve depo adı görüntüleme alanları doldurulur."""
        ...

    @abstractmethod
    def leaderboard_getir(
        self,
        vardiya_tarihi: date,
        depo_id: Optional[int] = None,
        limit: int = 20,
    ) -> List[OperatorVardiyaMetrikleri]:
        """Verilen gün için aktif çalışmış operatörleri döner.
        Sıralama use case katmanında UPH'a göre yapılır (DB'de UPH yok)."""
        ...
