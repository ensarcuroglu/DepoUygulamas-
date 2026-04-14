"""
Sipariş Durum Orkestratörü — sevkiyat/irsaliye lifecycle olaylarından
sipariş durumunu türeten merkezi bileşen.

Kurallar:
- Geçerli olmayan geçişlerde no-op (idempotent).
- Repository güncellemesi çağrı yapan use case'in transaction bağlamında yürür
  (auto_commit kontrolü repo implementasyonundadır).
"""

from __future__ import annotations
from datetime import datetime

from app.core.entities.siparis import SiparisDurum
from app.core.repositories.siparis_repository import ISiparisRepository
from app.core.repositories.sevkiyat_plani_repository import ISevkiyatPlaniRepository
from app.core.exceptions import KayitBulunamadiError


class SiparisDurumOrchestrator:
    """
    Sipariş durumunu sevkiyat olaylarıyla senkronize eder.

    Olaylar:
    - sevkiyat_planlandi(siparis_id) → Bekleme ise Hazirlaniyor
    - yukleme_onaylandi(siparis_id)  → Hazirlaniyor ise YolaCikti
    - sevkiyat_teslim_edildi(siparis_id) → YolaCikti ise TeslimEdildi
    - sevkiyat_plani_iptal(siparis_id) → Hazirlaniyor ise Bekleme
      (başka aktif plan kalmadıysa)
    """

    def __init__(
        self,
        siparis_repo: ISiparisRepository,
        sevkiyat_repo: ISevkiyatPlaniRepository,
    ):
        self._siparis_repo = siparis_repo
        self._sevkiyat_repo = sevkiyat_repo

    def sevkiyat_planlandi(self, siparis_id: int) -> None:
        self._gecis_uygula(siparis_id, SiparisDurum.BEKLEME, SiparisDurum.HAZIRLANIYOR)

    def yukleme_onaylandi(self, siparis_id: int) -> None:
        self._gecis_uygula(siparis_id, SiparisDurum.HAZIRLANIYOR, SiparisDurum.YOLA_CIKTI)

    def sevkiyat_teslim_edildi(self, siparis_id: int) -> None:
        self._gecis_uygula(siparis_id, SiparisDurum.YOLA_CIKTI, SiparisDurum.TESLIM_EDILDI)

    def sevkiyat_plani_iptal(self, siparis_id: int) -> None:
        """Planlandi sevkiyat silindiğinde: başka aktif plan yoksa Hazirlaniyor→Bekleme."""
        mevcut_plan = self._sevkiyat_repo.getir_siparis_id_ile(siparis_id)
        if mevcut_plan is not None:
            return
        siparis = self._siparis_repo.getir_id_ile(siparis_id)
        if siparis is None or siparis.durum != SiparisDurum.HAZIRLANIYOR:
            return
        siparis.durum = SiparisDurum.BEKLEME
        siparis.guncelleme_tarihi = datetime.utcnow()
        self._siparis_repo.guncelle(siparis)

    def _gecis_uygula(self, siparis_id: int, beklenen: str, hedef: str) -> None:
        siparis = self._siparis_repo.getir_id_ile(siparis_id)
        if siparis is None:
            raise KayitBulunamadiError("Sipariş", siparis_id)
        if siparis.durum == hedef:
            return
        if siparis.durum != beklenen:
            return
        siparis.durum = hedef
        siparis.guncelleme_tarihi = datetime.utcnow()
        self._siparis_repo.guncelle(siparis)
