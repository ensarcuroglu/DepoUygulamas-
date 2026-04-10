"""
Yerleştirme Görevi Use Case'leri.
"""

from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from app.core.repositories.yerlestirme_gorevi_repository import IYerlestirmeGoreviRepository
from app.core.repositories.palet_repository import IPaletRepository
from app.core.repositories.raf_repository import IRafRepository
from app.core.repositories.zon_repository import IZonRepository
from app.core.repositories.urun_repository import IUrunRepository
from app.core.repositories.lot_repository import ILotRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.repositories.mal_kabul_irsaliye_repository import IMalKabulIrsaliyeRepository
from app.core.entities.yerlestirme_gorevi import YerlestirmeGorevi, GorevTipi, GorevDurum
from app.core.entities.mal_kabul_irsaliye import MalKabulDurum
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.entities.zon import ZonTipi
from app.core.exceptions import KayitBulunamadiError, GecersizIslemError

# Görev tamamlandı sayılan durumlar (bu ikisi varsa irsaliye kapanır)
_GOREV_BITTI_DURUMLARI = {GorevDurum.TAMAMLANDI, GorevDurum.IPTAL_EDILDI}


def _kapanma_ozeti_olustur(irsaliye, gorevler) -> dict:
    """Kapanış anında snapshot özeti üretir."""
    toplam = len(irsaliye.kalemler)
    tamamlanan = sum(1 for g in gorevler if g.durum == GorevDurum.TAMAMLANDI)
    iptal = sum(1 for g in gorevler if g.durum == GorevDurum.IPTAL_EDILDI)
    istisna = irsaliye.istisna_sayisi()

    # Ortalama yerleştirme süresi (saniye)
    sureler = []
    for g in gorevler:
        if g.durum == GorevDurum.TAMAMLANDI and g.baslama_tarihi and g.tamamlanma_tarihi:
            delta = (g.tamamlanma_tarihi - g.baslama_tarihi).total_seconds()
            sureler.append(delta)
    ort_sure_dk = round(sum(sureler) / len(sureler) / 60.0, 1) if sureler else None

    return {
        "toplam_kalem": toplam,
        "yerlestirilen": tamamlanan,
        "iptal_edilen": iptal,
        "istisna_sayisi": istisna,
        "ort_yerlestirme_sure_dk": ort_sure_dk,
    }


def _irsaliye_otomatik_kapat(
    gorev: YerlestirmeGorevi,
    gorev_repo: IYerlestirmeGoreviRepository,
    mal_kabul_repo: IMalKabulIrsaliyeRepository,
) -> None:
    """Son görev tamamlandığında irsaliyeyi otomatik kapatır ve kapanma_ozeti oluşturur."""
    if not gorev.mal_kabul_irsaliye_id:
        return
    irsaliye_gorevleri = gorev_repo.getir_irsaliye_id_ile(gorev.mal_kabul_irsaliye_id)
    if not irsaliye_gorevleri:
        return
    if all(g.durum in _GOREV_BITTI_DURUMLARI for g in irsaliye_gorevleri):
        irsaliye = mal_kabul_repo.getir_id_ile(gorev.mal_kabul_irsaliye_id)
        if irsaliye and irsaliye.durum == MalKabulDurum.ONAYLANDI:
            irsaliye.kapanma_ozeti = _kapanma_ozeti_olustur(irsaliye, irsaliye_gorevleri)
            irsaliye.kapat()
            mal_kabul_repo.guncelle(irsaliye)


def _gorev_depo_id_belirle(gorev: YerlestirmeGorevi, raf_repo: IRafRepository) -> Optional[int]:
    """Görevin depo bağlamını doğrudan görevden, yoksa ilişkili raflardan çözer."""
    if gorev.depo_id is not None:
        return gorev.depo_id

    if gorev.onerilen_raf_id:
        onerilen_raf = raf_repo.getir_id_ile(gorev.onerilen_raf_id)
        if onerilen_raf and onerilen_raf.depo_id is not None:
            return onerilen_raf.depo_id

    if gorev.kaynak_raf_id:
        kaynak_raf = raf_repo.getir_id_ile(gorev.kaynak_raf_id)
        if kaynak_raf and kaynak_raf.depo_id is not None:
            return kaynak_raf.depo_id

    return None


from app.application.dto.yerlestirme_gorevi_dto import (    # noqa: E402
    YerlestirmeGoreviOlusturRequestDTO,
    YerlestirmeGoreviTamamlaRequestDTO,
    YerlestirmeGoreviOverrideRequestDTO,
    YerlestirmeGoreviIptalRequestDTO,
    YerlestirmeGoreviResponseDTO,
    YerlestirmeOnaylaRequestDTO,
    YerlestirmeOnaylaSonucDTO,
    AlternatifRafDTO,
    KarantinadanCikarRequestDTO,
    KarantinayaAlRequestDTO,
    BilinmeyenKonumGorevleriOlusturSonucDTO,
)

if TYPE_CHECKING:
    from app.core.services.zon_uyumluluk_servisi import ZonUyumlulukServisi
    from app.core.services.kapasite_dogrulama_servisi import KapasiteDogrulamaServisi
    from app.core.services.yerlestirme_algoritmasi import YerlestirmeAlgoritmasi


class YerlestirmeGoreviListeleUseCase:
    def __init__(self, repo: IYerlestirmeGoreviRepository):
        self._repo = repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        atanan_kullanici_id: Optional[int] = None,
        palet_id: Optional[int] = None,
        depo_id: Optional[int] = None,
    ) -> List[YerlestirmeGoreviResponseDTO]:
        gorevler = self._repo.getir_hepsi(
            skip=skip, limit=limit, durum=durum,
            atanan_kullanici_id=atanan_kullanici_id, palet_id=palet_id,
            depo_id=depo_id,
        )
        return [YerlestirmeGoreviResponseDTO.from_entity(g) for g in gorevler]


class YerlestirmeGoreviGetirUseCase:
    def __init__(self, repo: IYerlestirmeGoreviRepository):
        self._repo = repo

    def execute(self, gorev_id: int) -> YerlestirmeGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)
        return YerlestirmeGoreviResponseDTO.from_entity(gorev)


class YerlestirmeGoreviOlusturUseCase:
    """
    Manuel görev oluşturur. Otomatik oluşturma irsaliye onay akışından tetiklenir.

    İş kuralları:
    - Palet var olmalı.
    - Önerilen raf var olmalı.
    - Transfer görevinde kaynak_raf_id zorunlu.
    """

    def __init__(
        self,
        repo: IYerlestirmeGoreviRepository,
        palet_repo: IPaletRepository,
        raf_repo: IRafRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._log_repo = log_repo

    def execute(
        self, dto: YerlestirmeGoreviOlusturRequestDTO, kullanici_id: int
    ) -> YerlestirmeGoreviResponseDTO:
        palet = self._palet_repo.getir_id_ile(dto.palet_id)
        if not palet:
            raise KayitBulunamadiError("Palet", dto.palet_id)

        raf = self._raf_repo.getir_id_ile(dto.onerilen_raf_id)
        if not raf:
            raise KayitBulunamadiError("Raf", dto.onerilen_raf_id)

        if dto.tip == GorevTipi.TRANSFER and not dto.kaynak_raf_id:
            raise GecersizIslemError("Transfer görevi için kaynak_raf_id zorunludur.")

        gorev = YerlestirmeGorevi(
            palet_id=dto.palet_id,
            mal_kabul_irsaliye_id=dto.mal_kabul_irsaliye_id,
            depo_id=raf.depo_id,
            tip=dto.tip,
            kaynak_raf_id=dto.kaynak_raf_id,
            onerilen_raf_id=dto.onerilen_raf_id,
            oncelik=dto.oncelik,
        )
        kaydedilen = self._repo.olustur(gorev)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Yerleştirme",
                detay=f"Yerleştirme görevi oluşturuldu: Palet {dto.palet_id} → Raf {raf.kod}",
                yeni_veri={"palet_id": dto.palet_id, "onerilen_raf_id": dto.onerilen_raf_id},
            )
        )
        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)


class SonrakiGorevisiniAlUseCase:
    """Pull-based FIFO: Operatör sıradaki görevi kilitleyerek çeker."""

    def __init__(self, repo: IYerlestirmeGoreviRepository):
        self._repo = repo

    def execute(self, kullanici_id: int, depo_id: Optional[int] = None) -> Optional[YerlestirmeGoreviResponseDTO]:
        gorev = self._repo.sonraki_gorevi_kilitle(kullanici_id, depo_id=depo_id)
        if not gorev:
            return None
        return YerlestirmeGoreviResponseDTO.from_entity(gorev)


class ZamanAsimiBirakUseCase:
    """ATANDI durumundaki ve timeout'u aşmış görevleri Bekliyor'a geri alır."""

    def __init__(self, repo: IYerlestirmeGoreviRepository, timeout_dk: int = 60):
        self._repo = repo
        self._timeout_dk = timeout_dk

    def execute(self) -> dict:
        """Timeout geçmiş görevleri serbest bırakır. Serbest bırakılan görev sayısını döner."""
        gorevler = self._repo.getir_zaman_asimi_gecmis(self._timeout_dk)
        serbest_birakildi = 0
        for gorev in gorevler:
            gorev.bırak()
            self._repo.guncelle(gorev)
            serbest_birakildi += 1
        return {"serbest_birakildi": serbest_birakildi, "timeout_dk": self._timeout_dk}


class YerlestirmeGoreviBaslatUseCase:
    """Operatör paleti fiziksel olarak aldığında DEVAM_EDIYOR'a geçer."""

    def __init__(self, repo: IYerlestirmeGoreviRepository):
        self._repo = repo

    def execute(self, gorev_id: int, kullanici_id: int) -> YerlestirmeGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)
        if gorev.atanan_kullanici_id != kullanici_id:
            raise GecersizIslemError("Bu görev size atanmamış.")
        gorev.baslat()
        kaydedilen = self._repo.guncelle(gorev)
        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)


class YerlestirmeGoreviTamamlaUseCase:
    """Operatör raf barkodunu okuttu — görev tamamlanır, palet rafına atanır."""

    def __init__(
        self,
        repo: IYerlestirmeGoreviRepository,
        palet_repo: IPaletRepository,
        raf_repo: IRafRepository,
        log_repo: ISistemLogRepository,
        mal_kabul_repo: IMalKabulIrsaliyeRepository,
    ):
        self._repo = repo
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._log_repo = log_repo
        self._mal_kabul_repo = mal_kabul_repo

    def execute(
        self, gorev_id: int, dto: YerlestirmeGoreviTamamlaRequestDTO, kullanici_id: int
    ) -> YerlestirmeGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)
        if gorev.atanan_kullanici_id != kullanici_id:
            raise GecersizIslemError("Bu görev size atanmamış.")

        raf = self._raf_repo.getir_id_ile(dto.gerceklesen_raf_id)
        if not raf:
            raise KayitBulunamadiError("Raf", dto.gerceklesen_raf_id)

        palet = self._palet_repo.getir_id_ile(gorev.palet_id)
        if not palet:
            raise KayitBulunamadiError("Palet", gorev.palet_id)

        palet.raf_ata(dto.gerceklesen_raf_id)
        self._palet_repo.guncelle(palet, auto_commit=False)

        gorev.tamamla(dto.gerceklesen_raf_id)
        kaydedilen = self._repo.guncelle(gorev)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Yerleştirme",
                detay=f"Görev tamamlandı: ID {gorev_id} → Raf {raf.kod}",
                yeni_veri={"gerceklesen_raf_id": dto.gerceklesen_raf_id},
            )
        )

        _irsaliye_otomatik_kapat(gorev, self._repo, self._mal_kabul_repo)

        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)


class YerlestirmeGoreviOverrideUseCase:
    """Süpervizör kapasite/zon kuralı ihlali ile override tamamlama."""

    def __init__(
        self,
        repo: IYerlestirmeGoreviRepository,
        palet_repo: IPaletRepository,
        raf_repo: IRafRepository,
        log_repo: ISistemLogRepository,
        mal_kabul_repo: IMalKabulIrsaliyeRepository,
    ):
        self._repo = repo
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._log_repo = log_repo
        self._mal_kabul_repo = mal_kabul_repo

    def execute(
        self, gorev_id: int, dto: YerlestirmeGoreviOverrideRequestDTO, supervisor_id: int
    ) -> YerlestirmeGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)

        raf = self._raf_repo.getir_id_ile(dto.gerceklesen_raf_id)
        if not raf:
            raise KayitBulunamadiError("Raf", dto.gerceklesen_raf_id)

        palet = self._palet_repo.getir_id_ile(gorev.palet_id)
        if not palet:
            raise KayitBulunamadiError("Palet", gorev.palet_id)

        palet.raf_ata(dto.gerceklesen_raf_id)
        self._palet_repo.guncelle(palet, auto_commit=False)

        gorev.override_ile_tamamla(dto.gerceklesen_raf_id, supervisor_id, dto.neden)
        kaydedilen = self._repo.guncelle(gorev)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=supervisor_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Yerleştirme",
                detay=f"Override tamamlama: Görev {gorev_id} → Raf {raf.kod}. Gerekçe: {dto.neden}",
                yeni_veri={"gerceklesen_raf_id": dto.gerceklesen_raf_id, "neden": dto.neden},
            )
        )

        _irsaliye_otomatik_kapat(gorev, self._repo, self._mal_kabul_repo)

        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)


class YerlestirmeGoreviBirakUseCase:
    """Operatör görevi havuza iade eder: ATANDI → BEKLIYOR."""

    def __init__(self, repo: IYerlestirmeGoreviRepository):
        self._repo = repo

    def execute(self, gorev_id: int, kullanici_id: int) -> YerlestirmeGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)
        if gorev.atanan_kullanici_id != kullanici_id:
            raise GecersizIslemError("Bu görev size atanmamış.")
        gorev.bırak()
        kaydedilen = self._repo.guncelle(gorev)
        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)


class YerlestirmeGoreviYerlestirmeGoreviBekleyenOzetUseCase:
    """Bekleyen görev havuzunu özetler: sayı ve öncelik dağılımı."""

    def __init__(self, repo: IYerlestirmeGoreviRepository):
        self._repo = repo

    def execute(self, depo_id: Optional[int] = None) -> dict:
        bekleyenler = self._repo.getir_hepsi(durum="Bekliyor", limit=10000, depo_id=depo_id)
        toplam = len(bekleyenler)
        acil = sum(1 for g in bekleyenler if g.oncelik == 1)
        yuksek = sum(1 for g in bekleyenler if g.oncelik == 2)
        normal = sum(1 for g in bekleyenler if g.oncelik >= 3)
        return {
            "toplam_bekleyen": toplam,
            "acil": acil,
            "yuksek_oncelikli": yuksek,
            "normal": normal,
        }


class YerlestirmeGoreviIptalUseCase:
    def __init__(self, repo: IYerlestirmeGoreviRepository, log_repo: ISistemLogRepository):
        self._repo = repo
        self._log_repo = log_repo

    def execute(
        self, gorev_id: int, dto: YerlestirmeGoreviIptalRequestDTO, kullanici_id: int
    ) -> YerlestirmeGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)

        gorev.iptal_et(dto.neden)
        kaydedilen = self._repo.guncelle(gorev)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Yerleştirme",
                detay=f"Görev iptal edildi: ID {gorev_id}. Neden: {dto.neden}",
            )
        )
        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# FAZ 2.2 — FİZİKSEL YERLEŞTİRME ONAYI (Scan-to-Verify)
# ─────────────────────────────────────────────────────────────────

class YerlestirmeOnaylaUseCase:
    """
    Operatör raf barkodunu okuttuğunda:
      1. Zon uyumluluk + kapasite kontrolü yapar.
      2. Başarılı ise → palet.raf_id güncellenir, görev TAMAMLANDI'ya geçer.
      3. Başarısız ise → hata tipi + alternatif raflar döner (override için).
    """

    def __init__(
        self,
        repo: IYerlestirmeGoreviRepository,
        palet_repo: IPaletRepository,
        raf_repo: IRafRepository,
        lot_repo: ILotRepository,
        urun_repo: IUrunRepository,
        zon_repo: IZonRepository,
        zon_uyumluluk: "ZonUyumlulukServisi",
        kapasite: "KapasiteDogrulamaServisi",
        log_repo: ISistemLogRepository,
        mal_kabul_repo: IMalKabulIrsaliyeRepository,
    ):
        self._repo = repo
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._lot_repo = lot_repo
        self._urun_repo = urun_repo
        self._zon_repo = zon_repo
        self._zon_uyumluluk = zon_uyumluluk
        self._kapasite = kapasite
        self._log_repo = log_repo
        self._mal_kabul_repo = mal_kabul_repo

    def execute(
        self, gorev_id: int, dto: YerlestirmeOnaylaRequestDTO, kullanici_id: int
    ) -> YerlestirmeOnaylaSonucDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)

        if gorev.atanan_kullanici_id != kullanici_id:
            raise GecersizIslemError("Bu görev size atanmamış.")

        gorev_depo_id = _gorev_depo_id_belirle(gorev, self._raf_repo)
        if gorev_depo_id is None:
            raise GecersizIslemError(
                "Görev için depo bağlamı bulunamadı. Lütfen yöneticiniz ile iletişime geçin."
            )

        hedef_raf = self._raf_repo.getir_kod_ile(dto.okutulan_raf_kodu, gorev_depo_id)
        if not hedef_raf:
            raise KayitBulunamadiError("Raf", dto.okutulan_raf_kodu)

        palet = self._palet_repo.getir_id_ile(gorev.palet_id)
        if not palet:
            raise KayitBulunamadiError("Palet", gorev.palet_id)

        lot = self._lot_repo.getir_id_ile(palet.lot_id) if palet.lot_id else None
        urun = self._urun_repo.getir_id_ile(lot.urun_id) if lot else None

        onerilen_raf = self._raf_repo.getir_id_ile(gorev.onerilen_raf_id)

        # Zon uyumluluk kontrolü
        if urun and hedef_raf.zon_id:
            zon = self._zon_repo.getir_id_ile(hedef_raf.zon_id)
            if zon and not self._zon_uyumluluk.uyumlu_mu(urun.depolama_tipi, zon.tip):
                return self._hata_sonucu(
                    hata_tipi="ZON_UYUMSUZ",
                    mesaj=self._zon_uyumluluk.uyumsuzluk_mesaji(urun.depolama_tipi, zon.tip),
                    hedef_raf=hedef_raf,
                    palet=palet,
                    onerilen_raf=onerilen_raf,
                )

        # Kapasite kontrolü
        palet_kg = palet.palet_kg or 0.0
        kapasite_sonuc = self._kapasite.dogrula(hedef_raf, palet_kg)
        if not kapasite_sonuc.yeterli:
            return self._hata_sonucu(
                hata_tipi="KAPASITE_YETERSIZ",
                mesaj=f"Kapasite Yetersiz: {kapasite_sonuc.neden}",
                hedef_raf=hedef_raf,
                palet=palet,
                onerilen_raf=onerilen_raf,
            )

        # Başarılı — palet + görev güncelle
        palet.raf_ata(hedef_raf.id)
        self._palet_repo.guncelle(palet)

        gorev.tamamla(hedef_raf.id)
        self._repo.guncelle(gorev)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Yerleştirme",
                detay=f"Scan-to-verify tamamlandı: Görev {gorev_id} → Raf {hedef_raf.kod}",
                yeni_veri={"gerceklesen_raf_id": hedef_raf.id},
            )
        )

        _irsaliye_otomatik_kapat(gorev, self._repo, self._mal_kabul_repo)

        return YerlestirmeOnaylaSonucDTO(
            basarili=True,
            durum="TAMAMLANDI",
            palet_no=palet.palet_no,
            raf_kod=hedef_raf.kod,
            onerilen_raf_kod=onerilen_raf.kod if onerilen_raf else None,
            mesaj="Palet başarıyla yerleştirildi.",
            gorev=YerlestirmeGoreviResponseDTO.from_entity(gorev),
        )

    def _hata_sonucu(
        self, hata_tipi: str, mesaj: str, hedef_raf, palet, onerilen_raf
    ) -> YerlestirmeOnaylaSonucDTO:
        alternatifler = []
        if hedef_raf.zon_id:
            alt_raflar = self._kapasite.alternatif_raflar_getir(
                hedef_raf.zon_id, palet.palet_kg or 0.0, limit=3
            )
            for r in alt_raflar:
                mevcut_paletler = self._palet_repo.getir_hepsi(
                    raf_id=r.id, sadece_aktif=True, limit=500
                )
                alternatifler.append(AlternatifRafDTO(
                    raf_id=r.id,
                    raf_kod=r.kod,
                    bos_slot=max(0, r.kapasite - len(mevcut_paletler)),
                    skor=round(self._kapasite.doluluk_orani(r) * 100, 1),
                ))

        return YerlestirmeOnaylaSonucDTO(
            basarili=False,
            durum="DOGRULAMA_HATASI",
            palet_no=palet.palet_no,
            raf_kod=hedef_raf.kod,
            onerilen_raf_kod=onerilen_raf.kod if onerilen_raf else None,
            mesaj=mesaj,
            hata_tipi=hata_tipi,
            alternatifler=alternatifler,
            override_gerekli=True,
        )


# ─────────────────────────────────────────────────────────────────
# FAZ 2.4 — KONUMU BELİRSİZ PALETLERİ YERLEŞTİRME
# ─────────────────────────────────────────────────────────────────

class BilinmeyenKonumGorevleriOlusturUseCase:
    """
    MIGRATION_STAGING raftaki aktif paletler için yüksek öncelikli yerleştirme
    görevi oluşturur. Migration sonrası veya manuel tetikleme ile çalıştırılır.
    """

    def __init__(
        self,
        repo: IYerlestirmeGoreviRepository,
        palet_repo: IPaletRepository,
        raf_repo: IRafRepository,
        lot_repo: ILotRepository,
        urun_repo: IUrunRepository,
        algoritma: "YerlestirmeAlgoritmasi",
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._lot_repo = lot_repo
        self._urun_repo = urun_repo
        self._algoritma = algoritma
        self._log_repo = log_repo

    def execute(self, depo_id: int, kullanici_id: int) -> BilinmeyenKonumGorevleriOlusturSonucDTO:
        staging_raf = self._raf_repo.getir_staging_raf(depo_id)
        if not staging_raf:
            raise GecersizIslemError(
                f"Depo {depo_id} için MIGRATION_STAGING rafı bulunamadı."
            )

        paletler = self._palet_repo.getir_hepsi(
            raf_id=staging_raf.id, sadece_aktif=True, limit=1000
        )

        olusturulan = 0
        uyarilar: List[str] = []

        for palet in paletler:
            lot = self._lot_repo.getir_id_ile(palet.lot_id) if palet.lot_id else None
            urun = self._urun_repo.getir_id_ile(lot.urun_id) if lot else None

            if not urun:
                uyarilar.append(f"Palet {palet.palet_no}: ürün bilgisi bulunamadı, atlandı.")
                continue

            oneri = self._algoritma.raf_oner(palet, urun, depo_id)
            if not oneri:
                uyarilar.append(f"Palet {palet.palet_no}: uygun raf bulunamadı, atlandı.")
                continue

            gorev = YerlestirmeGorevi(
                palet_id=palet.id,
                depo_id=depo_id,
                tip=GorevTipi.BELIRSIZ_KONUM,
                onerilen_raf_id=oneri.onerilen_raf.id,
                oncelik=1,
            )
            self._repo.olustur(gorev)
            olusturulan += 1

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Yerleştirme",
                detay=(
                    f"Konumu belirsiz palet görevleri oluşturuldu: "
                    f"{olusturulan}/{len(paletler)} palet, Depo {depo_id}"
                ),
            )
        )

        return BilinmeyenKonumGorevleriOlusturSonucDTO(
            olusturulan_gorev_sayisi=olusturulan,
            palet_sayisi=len(paletler),
            uyari_mesajlari=uyarilar,
        )


# ─────────────────────────────────────────────────────────────────
# FAZ 2.5 — KARANTİNA ÇIKIŞ / GİRİŞ (Transfer Görevi)
# ─────────────────────────────────────────────────────────────────

class KarantinadanCikarUseCase:
    """
    Admin/QC paleti karantinadan çıkarır → Transfer görevi oluşturur.
    Görev tamamlandığında palet normal stok rafına taşınır.
    """

    def __init__(
        self,
        repo: IYerlestirmeGoreviRepository,
        palet_repo: IPaletRepository,
        raf_repo: IRafRepository,
        lot_repo: ILotRepository,
        urun_repo: IUrunRepository,
        zon_repo: IZonRepository,
        algoritma: "YerlestirmeAlgoritmasi",
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._lot_repo = lot_repo
        self._urun_repo = urun_repo
        self._zon_repo = zon_repo
        self._algoritma = algoritma
        self._log_repo = log_repo

    def execute(
        self, dto: KarantinadanCikarRequestDTO, kullanici_id: int
    ) -> YerlestirmeGoreviResponseDTO:
        palet = self._palet_repo.getir_id_ile(dto.palet_id)
        if not palet:
            raise KayitBulunamadiError("Palet", dto.palet_id)
        if not palet.aktif:
            raise GecersizIslemError("Pasif palet karantinadan çıkarılamaz.")

        kaynak_raf = self._raf_repo.getir_id_ile(palet.raf_id)
        if not kaynak_raf or not kaynak_raf.zon_id:
            raise GecersizIslemError("Paletin raf/zon bilgisi bulunamadı.")

        kaynak_zon = self._zon_repo.getir_id_ile(kaynak_raf.zon_id)
        if not kaynak_zon or kaynak_zon.tip != ZonTipi.KARANTINA:
            raise GecersizIslemError(
                f"Palet karantina zonunda değil (mevcut zon: {kaynak_zon.tip if kaynak_zon else '?'})."
            )

        lot = self._lot_repo.getir_id_ile(palet.lot_id) if palet.lot_id else None
        urun = self._urun_repo.getir_id_ile(lot.urun_id) if lot else None
        if not urun:
            raise GecersizIslemError("Paletin ürün bilgisi bulunamadı.")

        oneri = self._algoritma.raf_oner(palet, urun, kaynak_zon.depo_id)
        if not oneri:
            raise GecersizIslemError(
                "Karantina çıkışı için uygun hedef raf bulunamadı. "
                "Lütfen önce raf kapasitelerini kontrol edin."
            )

        gorev = YerlestirmeGorevi(
            palet_id=palet.id,
            depo_id=kaynak_zon.depo_id,
            tip=GorevTipi.TRANSFER,
            kaynak_raf_id=palet.raf_id,
            onerilen_raf_id=oneri.onerilen_raf.id,
            oncelik=2,
        )
        kaydedilen = self._repo.olustur(gorev)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Yerleştirme",
                detay=(
                    f"Karantinadan çıkış onayı: Palet {palet.palet_no}, "
                    f"onaylayan: kullanici_id={kullanici_id}"
                ),
                yeni_veri={"gorev_id": kaydedilen.id, "onerilen_raf_id": oneri.onerilen_raf.id},
            )
        )

        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)


class KarantinayaAlUseCase:
    """
    Admin paleti karantinaya alır → Transfer görevi oluşturur (oncelik=1, acil).
    """

    def __init__(
        self,
        repo: IYerlestirmeGoreviRepository,
        palet_repo: IPaletRepository,
        raf_repo: IRafRepository,
        zon_repo: IZonRepository,
        kapasite: "KapasiteDogrulamaServisi",
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._zon_repo = zon_repo
        self._kapasite = kapasite
        self._log_repo = log_repo

    def execute(
        self, dto: KarantinayaAlRequestDTO, kullanici_id: int
    ) -> YerlestirmeGoreviResponseDTO:
        palet = self._palet_repo.getir_id_ile(dto.palet_id)
        if not palet:
            raise KayitBulunamadiError("Palet", dto.palet_id)
        if not palet.aktif:
            raise GecersizIslemError("Pasif palet karantinaya alınamaz.")

        mevcut_raf = self._raf_repo.getir_id_ile(palet.raf_id)
        if mevcut_raf and mevcut_raf.zon_id:
            mevcut_zon = self._zon_repo.getir_id_ile(mevcut_raf.zon_id)
            if mevcut_zon and mevcut_zon.tip == ZonTipi.KARANTINA:
                raise GecersizIslemError("Palet zaten karantina zonunda.")

        depo_id = mevcut_raf.depo_id if mevcut_raf else None
        if not depo_id:
            raise GecersizIslemError("Paletin depo bilgisi çözümlenemedi.")

        karantina_raf = self._karantina_raf_bul(depo_id, palet.palet_kg or 0.0)
        if not karantina_raf:
            raise GecersizIslemError(
                "Karantina zonunda uygun raf bulunamadı. Kapasite dolmuş olabilir."
            )

        gorev = YerlestirmeGorevi(
            palet_id=palet.id,
            depo_id=depo_id,
            tip=GorevTipi.TRANSFER,
            kaynak_raf_id=palet.raf_id,
            onerilen_raf_id=karantina_raf.id,
            oncelik=1,
        )
        kaydedilen = self._repo.olustur(gorev)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.ERROR,
                modul="Yerleştirme",
                detay=f"Karantinaya alma: Palet {palet.palet_no}. Neden: {dto.neden}",
                yeni_veri={"gorev_id": kaydedilen.id, "karantina_raf_id": karantina_raf.id},
            )
        )

        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)

    def _karantina_raf_bul(self, depo_id: int, palet_kg: float):
        """Karantina zonundaki kapasitesi uygun ilk rafı döner."""
        karantina_zonlari = [
            z for z in self._zon_repo.getir_hepsi(depo_id=depo_id, sadece_aktif=True)
            if z.tip == ZonTipi.KARANTINA
        ]
        for zon in karantina_zonlari:
            raflar = self._raf_repo.getir_hepsi(zon_id=zon.id, sadece_aktif=True, limit=100)
            for raf in raflar:
                if self._kapasite.dogrula(raf, palet_kg).yeterli:
                    return raf
        return None
