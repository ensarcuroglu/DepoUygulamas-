"""Performans Event Publisher arayüzü.

Use case'ler bu arayüze bağımlı kalır; Faz 1'de implementasyon
DB-tabanlı transactional outbox (`DbOutboxPerformansEventPublisher`)
şeklindedir. Faz 5'te aynı arayüzü implement eden bir RabbitMQ adapter
eklenebilir, use case kodu değişmez.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional


class IPerformansEventPublisher(ABC):
    """Görev yaşam döngüsü olaylarını yayınlama arayüzü.

    Tüm metodlar `auto_commit=False` ile çağrılan repository'leri kullanır;
    commit, çağıran use case'in transaction sahibi tarafından yapılır.
    """

    @abstractmethod
    def gorev_baslatildi(
        self,
        gorev_tipi: str,
        gorev_id: int,
        kullanici_id: int,
        depo_id: Optional[int] = None,
        payload: Optional[dict] = None,
    ) -> None: ...

    @abstractmethod
    def gorev_tamamlandi(
        self,
        gorev_tipi: str,
        gorev_id: int,
        kullanici_id: int,
        sure_saniye: int,
        depo_id: Optional[int] = None,
        payload: Optional[dict] = None,
    ) -> None: ...

    @abstractmethod
    def gorev_iptal(
        self,
        gorev_tipi: str,
        gorev_id: int,
        kullanici_id: int,
        iptal_nedeni: Optional[str] = None,
        sure_saniye: Optional[int] = None,
        depo_id: Optional[int] = None,
        payload: Optional[dict] = None,
    ) -> None: ...
