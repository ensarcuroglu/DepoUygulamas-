"""Built-in authoritative tools for BackendProje's assistant registry.

AssistantAiService only proposes tool calls. This module is the authoritative
Backend side:
- read-only tools can be executed through the internal endpoint;
- HITL tools are executed only by the draft approval use case.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.application.services.asistan_tool_registry import (
    AsistanToolRegistry,
    ToolExecutionContext,
    ToolSpec,
)
from app.core.entities.yerlestirme_gorevi import GorevDurum, GorevTipi
from app.core.entities.zon import ZonTipi
from core.api_exceptions import (
    BadRequestError,
    KayitBulunamadiError,
    PermissionDeniedError,
)
from models import Depo as DepoORM
from models import Kullanici as KullaniciORM
from models import Lot as LotORM
from models import Palet as PaletORM
from models import Raf as RafORM
from models import Siparis as SiparisORM
from models import ToplamaGorevi as ToplamaGoreviORM
from models import Urun as UrunORM
from models import YerlestirmeGorevi as YerlestirmeGoreviORM
from models import Zon as ZonORM


TOOL_TARIH_SAAT_SIMDI = "tarih_saat_simdi"
TOOL_PALET_SORGULA = "palet_sorgula"
TOOL_RAF_LISTELE = "raf_listele"
TOOL_GOREV_DURUMU_GETIR = "gorev_durumu_getir"
TOOL_STOK_SORGULA = "stok_sorgula"
TOOL_GOREVLERIM_LISTELE = "gorevlerim_listele"
TOOL_PALET_RAF_DEGISTIR = "palet_raf_degistir"
TOOL_KARANTINAYA_AL = "karantinaya_al"
TOOL_SIPARIS_ONCELIK_DEGISTIR = "siparis_oncelik_degistir"
TOOL_YERLESTIRME_KONUM_DEGISTIR = "yerlestirme_konum_degistir"

_ALL_ROLES = frozenset({"admin", "lojistik", "depocu"})
_ADMIN_ONLY = frozenset({"admin"})
_ADMIN_LOJISTIK = frozenset({"admin", "lojistik"})


# ---------------------------------------------------------------------------
# Args schemas
# ---------------------------------------------------------------------------

def _aliaslari_uygula(value: Any, aliases: dict[str, str]) -> Any:
    if not isinstance(value, dict):
        return value
    data = dict(value)
    for source, target in aliases.items():
        if source in data and target not in data:
            data[target] = data.pop(source)
    return data


class TarihSaatSimdiArgs(BaseModel):
    zone_offset_saat: int = Field(default=3, ge=-12, le=14)


class PaletSorgulaArgs(BaseModel):
    palet_no: str = Field(..., min_length=1, max_length=50)

    @model_validator(mode="before")
    @classmethod
    def _aliases(cls, value: Any) -> Any:
        return _aliaslari_uygula(value, {"palet_barkodu": "palet_no", "barkod": "palet_no"})


class RafListeleArgs(BaseModel):
    depo_id: int | None = Field(None, gt=0)
    zon_id: int | None = Field(None, gt=0)
    sadece_aktif: bool = True
    limit: int = Field(default=50, ge=1, le=100)


class GorevDurumuGetirArgs(BaseModel):
    gorev_id: int = Field(..., gt=0)
    gorev_tipi: Literal["yerlestirme", "toplama"] = "yerlestirme"

    @model_validator(mode="before")
    @classmethod
    def _aliases(cls, value: Any) -> Any:
        return _aliaslari_uygula(value, {"id": "gorev_id", "tip": "gorev_tipi"})


class StokSorgulaArgs(BaseModel):
    urun_id: int | None = Field(None, gt=0)
    urun_barkod: str | None = Field(None, min_length=1, max_length=80)
    lot_no: str | None = Field(None, min_length=1, max_length=80)
    palet_no: str | None = Field(None, min_length=1, max_length=50)

    @model_validator(mode="before")
    @classmethod
    def _aliases(cls, value: Any) -> Any:
        return _aliaslari_uygula(value, {"barkod": "urun_barkod", "urun_kodu": "urun_barkod"})

    @model_validator(mode="after")
    def _one_selector_required(self):
        if not any((self.urun_id, self.urun_barkod, self.lot_no, self.palet_no)):
            raise ValueError("urun_id, urun_barkod, lot_no veya palet_no zorunludur.")
        return self


class GorevlerimListeleArgs(BaseModel):
    gorev_tipi: Literal["hepsi", "yerlestirme", "toplama"] = "hepsi"
    durum: str | None = Field(None, min_length=1, max_length=30)
    limit: int = Field(default=20, ge=1, le=50)


class PaletRafDegistirArgs(BaseModel):
    palet_no: str = Field(..., min_length=1, max_length=50)
    yeni_raf_kodu: str = Field(..., min_length=1, max_length=50)
    neden: str | None = Field(None, max_length=500)

    @model_validator(mode="before")
    @classmethod
    def _aliases(cls, value: Any) -> Any:
        return _aliaslari_uygula(
            value,
            {
                "palet_barkodu": "palet_no",
                "raf_kodu": "yeni_raf_kodu",
                "yeni_konum": "yeni_raf_kodu",
                "yeni_konum_kodu": "yeni_raf_kodu",
            },
        )


class KarantinayaAlArgs(BaseModel):
    palet_id: int | None = Field(None, gt=0)
    palet_no: str | None = Field(None, min_length=1, max_length=50)
    neden: str = Field(..., min_length=3, max_length=500)

    @model_validator(mode="before")
    @classmethod
    def _aliases(cls, value: Any) -> Any:
        return _aliaslari_uygula(value, {"palet_barkodu": "palet_no", "gerekce": "neden"})

    @model_validator(mode="after")
    def _target_required(self):
        if self.palet_id is None and not self.palet_no:
            raise ValueError("palet_id veya palet_no zorunludur.")
        return self


class SiparisOncelikDegistirArgs(BaseModel):
    siparis_id: int | None = Field(None, gt=0)
    siparis_no: str | None = Field(None, min_length=1, max_length=50)
    yeni_oncelik: int = Field(..., ge=1, le=5)
    neden: str | None = Field(None, max_length=500)

    @model_validator(mode="before")
    @classmethod
    def _aliases(cls, value: Any) -> Any:
        return _aliaslari_uygula(
            value,
            {
                "id": "siparis_id",
                "oncelik": "yeni_oncelik",
                "yeni_oncelik_degeri": "yeni_oncelik",
                "gerekce": "neden",
            },
        )

    @model_validator(mode="after")
    def _target_required(self):
        if self.siparis_id is None and not self.siparis_no:
            raise ValueError("siparis_id veya siparis_no zorunludur.")
        return self


class YerlestirmeKonumDegistirArgs(BaseModel):
    gorev_id: int | None = Field(None, gt=0)
    palet_no: str | None = Field(None, min_length=1, max_length=50)
    yeni_konum_kodu: str = Field(..., min_length=1, max_length=50)

    @model_validator(mode="before")
    @classmethod
    def _aliases(cls, value: Any) -> Any:
        return _aliaslari_uygula(
            value,
            {
                "id": "gorev_id",
                "yeni_konum": "yeni_konum_kodu",
                "raf_kodu": "yeni_konum_kodu",
                "yeni_raf_kodu": "yeni_konum_kodu",
            },
        )

    @model_validator(mode="after")
    def _target_required(self):
        if self.gorev_id is None and not self.palet_no:
            raise ValueError("gorev_id veya palet_no zorunludur.")
        return self


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def ensure_default_asistan_tools_registered(registry: AsistanToolRegistry) -> None:
    """Register built-in assistant tools idempotently."""
    specs = [
        ToolSpec(
            tool_id=TOOL_TARIH_SAAT_SIMDI,
            aciklama="Anlik tarih/saat bilgisini Turkiye saatine gore okur.",
            hitl=False,
            rbac_roles=_ALL_ROLES,
            args_schema=TarihSaatSimdiArgs,
            executor=_tarih_saat_simdi,
        ),
        ToolSpec(
            tool_id=TOOL_PALET_SORGULA,
            aciklama="Palet numarasina gore palet, urun, lot, raf ve depo bilgisini okur.",
            hitl=False,
            rbac_roles=_ALL_ROLES,
            args_schema=PaletSorgulaArgs,
            executor=_palet_sorgula,
        ),
        ToolSpec(
            tool_id=TOOL_RAF_LISTELE,
            aciklama="Depo/zon filtresiyle aktif raf listesini okur; mutasyon yapmaz.",
            hitl=False,
            rbac_roles=_ALL_ROLES,
            args_schema=RafListeleArgs,
            executor=_raf_listele,
        ),
        ToolSpec(
            tool_id=TOOL_GOREV_DURUMU_GETIR,
            aciklama="Tek yerlestirme veya toplama gorevinin durumunu getirir.",
            hitl=False,
            rbac_roles=_ALL_ROLES,
            args_schema=GorevDurumuGetirArgs,
            executor=_gorev_durumu_getir,
        ),
        ToolSpec(
            tool_id=TOOL_STOK_SORGULA,
            aciklama="Urun, barkod, lot veya palet bazinda stok ozetini okur.",
            hitl=False,
            rbac_roles=_ALL_ROLES,
            args_schema=StokSorgulaArgs,
            executor=_stok_sorgula,
        ),
        ToolSpec(
            tool_id=TOOL_GOREVLERIM_LISTELE,
            aciklama="Oturumdaki kullaniciya atanmis acik depo gorevlerini listeler.",
            hitl=False,
            rbac_roles=_ALL_ROLES,
            args_schema=GorevlerimListeleArgs,
            executor=_gorevlerim_listele,
        ),
        ToolSpec(
            tool_id=TOOL_PALET_RAF_DEGISTIR,
            aciklama="Paletin rafini degistirir; sadece taslak onayindan sonra calisir.",
            hitl=True,
            rbac_roles=_ALL_ROLES,
            args_schema=PaletRafDegistirArgs,
            executor=_palet_raf_degistir_authoritative,
        ),
        ToolSpec(
            tool_id=TOOL_KARANTINAYA_AL,
            aciklama="Paleti karantina transfer gorevine alir; sadece admin onayindan sonra calisir.",
            hitl=True,
            rbac_roles=_ADMIN_ONLY,
            args_schema=KarantinayaAlArgs,
            executor=_karantinaya_al_authoritative,
        ),
        ToolSpec(
            tool_id=TOOL_SIPARIS_ONCELIK_DEGISTIR,
            aciklama="Siparis onceligini 1-5 araliginda gunceller; onay gerektirir.",
            hitl=True,
            rbac_roles=_ADMIN_LOJISTIK,
            args_schema=SiparisOncelikDegistirArgs,
            executor=_siparis_oncelik_degistir_authoritative,
        ),
        ToolSpec(
            tool_id=TOOL_YERLESTIRME_KONUM_DEGISTIR,
            aciklama=(
                "Legacy: paletin mevcut raf bilgisini veya bekleyen yerlestirme "
                "gorevinin hedef rafini degistirir."
            ),
            hitl=True,
            rbac_roles=_ALL_ROLES,
            args_schema=YerlestirmeKonumDegistirArgs,
            executor=_yerlestirme_konum_degistir_authoritative,
        ),
    ]
    for spec in specs:
        if registry.get(spec.tool_id) is None:
            registry.register(spec)


# ---------------------------------------------------------------------------
# Read-only tools
# ---------------------------------------------------------------------------

_GUNLER_TR = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]


def _tarih_saat_simdi(context: ToolExecutionContext) -> dict[str, Any]:
    offset = context.payload.get("zone_offset_saat", 3)
    tz = timezone(timedelta(hours=offset))
    simdi = datetime.now(tz)
    return {
        "iso_datetime": simdi.isoformat(timespec="seconds"),
        "zone_offset_saat": offset,
        "gun_adi": _GUNLER_TR[simdi.weekday()],
    }


def _palet_sorgula(context: ToolExecutionContext) -> dict[str, Any]:
    payload = context.payload
    palet = _palet_no_ile_getir(context.db, payload["palet_no"])
    _depo_erisim_dogrula(context.db, context.kullanici_id, context.rol, _palet_depo_id(context.db, palet))
    return _palet_ozeti(context.db, palet)


def _raf_listele(context: ToolExecutionContext) -> dict[str, Any]:
    payload = context.payload
    depo_id = _depo_filtresi(context.db, context.kullanici_id, context.rol, payload.get("depo_id"))
    query = context.db.query(RafORM)
    if depo_id is not None:
        query = query.filter(RafORM.depo_id == depo_id)
    if payload.get("zon_id") is not None:
        query = query.filter(RafORM.zon_id == payload["zon_id"])
    if payload.get("sadece_aktif", True):
        query = query.filter(RafORM.aktif.is_(True))

    raflar = query.order_by(RafORM.kod.asc()).limit(payload.get("limit", 50)).all()
    return {
        "toplam": len(raflar),
        "raflar": [
            {
                "id": r.id,
                "kod": r.kod,
                "depo_id": r.depo_id,
                "zon_id": r.zon_id,
                "kapasite": r.kapasite,
                "aktif": r.aktif,
            }
            for r in raflar
        ],
    }


def _gorev_durumu_getir(context: ToolExecutionContext) -> dict[str, Any]:
    payload = context.payload
    if payload["gorev_tipi"] == "toplama":
        gorev = context.db.query(ToplamaGoreviORM).filter(ToplamaGoreviORM.id == payload["gorev_id"]).first()
        if gorev is None:
            raise KayitBulunamadiError("ToplamaGorevi", payload["gorev_id"])
        _depo_erisim_dogrula(context.db, context.kullanici_id, context.rol, gorev.depo_id)
        return {
            "gorev_tipi": "toplama",
            "gorev_id": gorev.id,
            "durum": gorev.durum,
            "palet_id": gorev.palet_id,
            "urun_id": gorev.urun_id,
            "depo_id": gorev.depo_id,
            "atanan_kullanici_id": gorev.atanan_kullanici_id,
            "sira_no": gorev.sira_no,
        }

    gorev = context.db.query(YerlestirmeGoreviORM).filter(YerlestirmeGoreviORM.id == payload["gorev_id"]).first()
    if gorev is None:
        raise KayitBulunamadiError("YerlestirmeGorevi", payload["gorev_id"])
    depo_id = _gorev_depo_id_belirle(context.db, gorev)
    _depo_erisim_dogrula(context.db, context.kullanici_id, context.rol, depo_id)
    return {
        "gorev_tipi": "yerlestirme",
        "gorev_id": gorev.id,
        "durum": gorev.durum,
        "palet_id": gorev.palet_id,
        "depo_id": depo_id,
        "onerilen_raf_id": gorev.onerilen_raf_id,
        "gerceklesen_raf_id": gorev.gerceklesen_raf_id,
        "atanan_kullanici_id": gorev.atanan_kullanici_id,
        "oncelik": gorev.oncelik,
    }


def _stok_sorgula(context: ToolExecutionContext) -> dict[str, Any]:
    payload = context.payload
    if payload.get("palet_no"):
        palet = _palet_no_ile_getir(context.db, payload["palet_no"])
        _depo_erisim_dogrula(context.db, context.kullanici_id, context.rol, _palet_depo_id(context.db, palet))
        return {"tip": "palet", "palet": _palet_ozeti(context.db, palet)}

    urun = None
    if payload.get("urun_id") is not None:
        urun = context.db.query(UrunORM).filter(UrunORM.id == payload["urun_id"]).first()
    elif payload.get("urun_barkod"):
        barkod = payload["urun_barkod"]
        urun = context.db.query(UrunORM).filter(
            (UrunORM.barkod == barkod) | (UrunORM.ean == barkod)
        ).first()
    elif payload.get("lot_no"):
        lot = context.db.query(LotORM).filter(LotORM.lot_no == payload["lot_no"]).first()
        if lot is None:
            raise KayitBulunamadiError("Lot", payload["lot_no"])
        urun = context.db.query(UrunORM).filter(UrunORM.id == lot.urun_id).first()

    if urun is None:
        raise KayitBulunamadiError("Urun", payload.get("urun_id") or payload.get("urun_barkod") or payload.get("lot_no"))

    lot_query = context.db.query(LotORM).filter(LotORM.urun_id == urun.id, LotORM.aktif.is_(True))
    if payload.get("lot_no"):
        lot_query = lot_query.filter(LotORM.lot_no == payload["lot_no"])
    lotlar = lot_query.all()
    lot_ids = [lot.id for lot in lotlar]
    paletler = (
        context.db.query(PaletORM)
        .filter(PaletORM.lot_id.in_(lot_ids), PaletORM.aktif.is_(True))
        .all()
        if lot_ids
        else []
    )
    paletler = _paletleri_role_gore_filtrele(context.db, context.kullanici_id, context.rol, paletler)
    return {
        "tip": "urun",
        "urun_id": urun.id,
        "urun_adi": urun.isim,
        "barkod": urun.barkod,
        "ean": urun.ean,
        "lot_sayisi": len(lotlar),
        "palet_sayisi": len(paletler),
        "toplam_koli": sum(p.koli_adedi or 0 for p in paletler),
    }


def _gorevlerim_listele(context: ToolExecutionContext) -> dict[str, Any]:
    payload = context.payload
    limit = payload.get("limit", 20)
    sonuc: dict[str, Any] = {"yerlestirme": [], "toplama": []}
    depo_id = _depo_filtresi(context.db, context.kullanici_id, context.rol, None)

    if payload["gorev_tipi"] in {"hepsi", "yerlestirme"}:
        query = context.db.query(YerlestirmeGoreviORM).filter(
            YerlestirmeGoreviORM.atanan_kullanici_id == context.kullanici_id
        )
        if payload.get("durum"):
            query = query.filter(YerlestirmeGoreviORM.durum == payload["durum"])
        if depo_id is not None:
            query = query.filter(YerlestirmeGoreviORM.depo_id == depo_id)
        sonuc["yerlestirme"] = [
            {
                "id": g.id,
                "durum": g.durum,
                "palet_id": g.palet_id,
                "onerilen_raf_id": g.onerilen_raf_id,
                "oncelik": g.oncelik,
            }
            for g in query.order_by(YerlestirmeGoreviORM.oncelik.asc()).limit(limit).all()
        ]

    if payload["gorev_tipi"] in {"hepsi", "toplama"}:
        query = context.db.query(ToplamaGoreviORM).filter(
            ToplamaGoreviORM.atanan_kullanici_id == context.kullanici_id
        )
        if payload.get("durum"):
            query = query.filter(ToplamaGoreviORM.durum == payload["durum"])
        if depo_id is not None:
            query = query.filter(ToplamaGoreviORM.depo_id == depo_id)
        sonuc["toplama"] = [
            {
                "id": g.id,
                "durum": g.durum,
                "palet_id": g.palet_id,
                "urun_id": g.urun_id,
                "sira_no": g.sira_no,
            }
            for g in query.order_by(ToplamaGoreviORM.sira_no.asc()).limit(limit).all()
        ]

    sonuc["toplam"] = len(sonuc["yerlestirme"]) + len(sonuc["toplama"])
    return sonuc


# ---------------------------------------------------------------------------
# HITL authoritative tools
# ---------------------------------------------------------------------------

def _yerlestirme_konum_degistir_authoritative(context: ToolExecutionContext) -> dict[str, Any]:
    payload = context.payload
    yeni_konum_kodu = payload["yeni_konum_kodu"]
    gorev_id = payload.get("gorev_id")
    palet_no = payload.get("palet_no")

    if gorev_id is not None:
        return _gorev_hedef_raf_degistir(context, gorev_id, yeni_konum_kodu)

    assert palet_no is not None
    return _palet_raf_degistir(context, palet_no, yeni_konum_kodu, TOOL_YERLESTIRME_KONUM_DEGISTIR)


def _palet_raf_degistir_authoritative(context: ToolExecutionContext) -> dict[str, Any]:
    payload = context.payload
    return _palet_raf_degistir(
        context,
        payload["palet_no"],
        payload["yeni_raf_kodu"],
        TOOL_PALET_RAF_DEGISTIR,
    )


def _karantinaya_al_authoritative(context: ToolExecutionContext) -> dict[str, Any]:
    payload = context.payload
    db = context.db
    if payload.get("palet_id") is not None:
        palet = db.query(PaletORM).filter(PaletORM.id == payload["palet_id"]).with_for_update().first()
    else:
        palet = db.query(PaletORM).filter(PaletORM.palet_no == payload["palet_no"]).with_for_update().first()
    if palet is None:
        raise KayitBulunamadiError("Palet", payload.get("palet_id") or payload.get("palet_no"))
    if not palet.aktif:
        raise BadRequestError("Pasif palet karantinaya alinamaz.")

    mevcut_raf = db.query(RafORM).filter(RafORM.id == palet.raf_id).first()
    if mevcut_raf is None or mevcut_raf.depo_id is None:
        raise BadRequestError("Paletin depo/raf bilgisi cozumlenemedi.")
    _depo_erisim_dogrula(db, context.kullanici_id, context.rol, mevcut_raf.depo_id)

    if mevcut_raf.zon_id is not None:
        mevcut_zon = db.query(ZonORM).filter(ZonORM.id == mevcut_raf.zon_id).first()
        if mevcut_zon is not None and mevcut_zon.tip == ZonTipi.KARANTINA:
            raise BadRequestError("Palet zaten karantina zonunda.")

    karantina_raf = _karantina_raf_bul(db, mevcut_raf.depo_id)
    if karantina_raf is None:
        raise BadRequestError("Karantina zonunda uygun aktif raf bulunamadi.")

    gorev = YerlestirmeGoreviORM(
        palet_id=palet.id,
        depo_id=mevcut_raf.depo_id,
        tip=GorevTipi.TRANSFER,
        kaynak_raf_id=palet.raf_id,
        onerilen_raf_id=karantina_raf.id,
        oncelik=1,
        durum=GorevDurum.BEKLIYOR,
    )
    db.add(gorev)
    db.flush()
    return {
        "tool_id": TOOL_KARANTINAYA_AL,
        "tip": "karantina_transfer_gorevi_olustu",
        "palet_id": palet.id,
        "palet_no": palet.palet_no,
        "gorev_id": gorev.id,
        "kaynak_raf_id": palet.raf_id,
        "karantina_raf_id": karantina_raf.id,
        "karantina_raf_kodu": karantina_raf.kod,
    }


def _siparis_oncelik_degistir_authoritative(context: ToolExecutionContext) -> dict[str, Any]:
    payload = context.payload
    db = context.db
    query = db.query(SiparisORM)
    if payload.get("siparis_id") is not None:
        query = query.filter(SiparisORM.id == payload["siparis_id"])
    else:
        query = query.filter(SiparisORM.siparis_no == payload["siparis_no"])
    siparis = query.with_for_update().first()
    if siparis is None:
        raise KayitBulunamadiError("Siparis", payload.get("siparis_id") or payload.get("siparis_no"))
    eski_oncelik = getattr(siparis, "oncelik", 5)
    siparis.oncelik = payload["yeni_oncelik"]
    db.flush()
    return {
        "tool_id": TOOL_SIPARIS_ONCELIK_DEGISTIR,
        "siparis_id": siparis.id,
        "siparis_no": siparis.siparis_no,
        "eski_oncelik": eski_oncelik,
        "yeni_oncelik": siparis.oncelik,
    }


def _gorev_hedef_raf_degistir(
    context: ToolExecutionContext,
    gorev_id: int,
    yeni_konum_kodu: str,
) -> dict[str, Any]:
    db = context.db
    gorev = (
        db.query(YerlestirmeGoreviORM)
        .filter(YerlestirmeGoreviORM.id == gorev_id)
        .with_for_update()
        .first()
    )
    if gorev is None:
        raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)
    if gorev.durum not in {GorevDurum.BEKLIYOR, GorevDurum.ATANDI}:
        raise BadRequestError(
            f"Yerlestirme gorevi {gorev.durum} durumunda; hedef raf degistirilemez."
        )

    depo_id = _gorev_depo_id_belirle(db, gorev)
    _depo_erisim_dogrula(db, context.kullanici_id, context.rol, depo_id)
    hedef_raf = _raf_kod_ile_getir(db, yeni_konum_kodu, depo_id=depo_id)
    eski_raf = db.query(RafORM).filter(RafORM.id == gorev.onerilen_raf_id).first()

    eski_raf_id = gorev.onerilen_raf_id
    gorev.onerilen_raf_id = hedef_raf.id
    if gorev.depo_id is None:
        gorev.depo_id = hedef_raf.depo_id
    db.flush()

    return {
        "tool_id": TOOL_YERLESTIRME_KONUM_DEGISTIR,
        "tip": "gorev_hedef_raf_degisti",
        "gorev_id": gorev.id,
        "eski_raf_id": eski_raf_id,
        "eski_raf_kodu": eski_raf.kod if eski_raf is not None else None,
        "yeni_raf_id": hedef_raf.id,
        "yeni_raf_kodu": hedef_raf.kod,
    }


def _palet_raf_degistir(
    context: ToolExecutionContext,
    palet_no: str,
    yeni_raf_kodu: str,
    tool_id: str,
) -> dict[str, Any]:
    db = context.db
    palet = db.query(PaletORM).filter(PaletORM.palet_no == palet_no).with_for_update().first()
    if palet is None:
        raise KayitBulunamadiError("Palet", palet_no)

    mevcut_raf = db.query(RafORM).filter(RafORM.id == palet.raf_id).first()
    depo_id = mevcut_raf.depo_id if mevcut_raf is not None else _int_opsiyonel(
        (context.payload or {}).get("depo_id")
    )
    _depo_erisim_dogrula(db, context.kullanici_id, context.rol, depo_id)
    hedef_raf = _raf_kod_ile_getir(db, yeni_raf_kodu, depo_id=depo_id)

    if depo_id is not None and hedef_raf.depo_id != depo_id:
        raise BadRequestError("Palet farkli depodaki bir rafa tasinamaz.")

    eski_raf_id = palet.raf_id
    palet.raf_id = hedef_raf.id
    db.flush()

    return {
        "tool_id": tool_id,
        "tip": "palet_raf_degisti",
        "palet_no": palet.palet_no,
        "eski_raf_id": eski_raf_id,
        "eski_raf_kodu": mevcut_raf.kod if mevcut_raf is not None else None,
        "yeni_raf_id": hedef_raf.id,
        "yeni_raf_kodu": hedef_raf.kod,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _palet_no_ile_getir(db: Session, palet_no: str) -> PaletORM:
    palet = db.query(PaletORM).filter(PaletORM.palet_no == palet_no).first()
    if palet is None:
        raise KayitBulunamadiError("Palet", palet_no)
    return palet


def _palet_ozeti(db: Session, palet: PaletORM) -> dict[str, Any]:
    lot = db.query(LotORM).filter(LotORM.id == palet.lot_id).first() if palet.lot_id else None
    urun = db.query(UrunORM).filter(UrunORM.id == lot.urun_id).first() if lot else None
    raf = db.query(RafORM).filter(RafORM.id == palet.raf_id).first() if palet.raf_id else None
    depo = db.query(DepoORM).filter(DepoORM.id == raf.depo_id).first() if raf and raf.depo_id else None
    return {
        "palet_id": palet.id,
        "palet_no": palet.palet_no,
        "aktif": palet.aktif,
        "koli_adedi": palet.koli_adedi,
        "lot_id": lot.id if lot else None,
        "lot_no": lot.lot_no if lot else None,
        "urun_id": urun.id if urun else None,
        "urun_adi": urun.isim if urun else None,
        "raf_id": raf.id if raf else None,
        "raf_kodu": raf.kod if raf else None,
        "depo_id": depo.id if depo else None,
        "depo_adi": depo.isim if depo else None,
    }


def _palet_depo_id(db: Session, palet: PaletORM) -> int | None:
    if palet.raf_id is None:
        return None
    raf = db.query(RafORM).filter(RafORM.id == palet.raf_id).first()
    return raf.depo_id if raf is not None else None


def _paletleri_role_gore_filtrele(
    db: Session,
    kullanici_id: int,
    rol: str,
    paletler: list[PaletORM],
) -> list[PaletORM]:
    depo_id = _depo_filtresi(db, kullanici_id, rol, None)
    if depo_id is None:
        return paletler
    return [p for p in paletler if _palet_depo_id(db, p) == depo_id]


def _gorev_depo_id_belirle(db: Session, gorev: YerlestirmeGoreviORM) -> int | None:
    if gorev.depo_id is not None:
        return gorev.depo_id

    for raf_id in (gorev.onerilen_raf_id, gorev.kaynak_raf_id):
        if raf_id is None:
            continue
        raf = db.query(RafORM).filter(RafORM.id == raf_id).first()
        if raf is not None and raf.depo_id is not None:
            return raf.depo_id

    palet = db.query(PaletORM).filter(PaletORM.id == gorev.palet_id).first()
    if palet is not None:
        return _palet_depo_id(db, palet)
    return None


def _raf_kod_ile_getir(db: Session, kod: str, *, depo_id: int | None) -> RafORM:
    query = db.query(RafORM).filter(func.lower(RafORM.kod) == kod.lower())
    if depo_id is not None:
        query = query.filter(RafORM.depo_id == depo_id)
    raf = query.first()
    if raf is None:
        raise KayitBulunamadiError("Raf", kod)
    if not raf.aktif:
        raise BadRequestError(f"Raf aktif degil: {kod}")
    return raf


def _karantina_raf_bul(db: Session, depo_id: int) -> RafORM | None:
    zonlar = db.query(ZonORM).filter(ZonORM.depo_id == depo_id, ZonORM.tip == ZonTipi.KARANTINA).all()
    for zon in zonlar:
        raflar = db.query(RafORM).filter(RafORM.zon_id == zon.id, RafORM.aktif.is_(True)).order_by(RafORM.kod.asc()).all()
        for raf in raflar:
            palet_sayisi = db.query(PaletORM).filter(PaletORM.raf_id == raf.id, PaletORM.aktif.is_(True)).count()
            if palet_sayisi < (raf.kapasite or 0):
                return raf
    return None


def _depo_filtresi(db: Session, kullanici_id: int, rol: str, requested_depo_id: int | None) -> int | None:
    if rol != "depocu":
        return requested_depo_id
    kullanici = db.query(KullaniciORM).filter(KullaniciORM.id == kullanici_id).first()
    if kullanici is None:
        raise PermissionDeniedError("Kullanici kaydi bulunamadigi icin depo erisimi dogrulanamadi.")
    if kullanici.depo_erisimi_yok:
        raise PermissionDeniedError("Bu kullanicinin depo erisimi yok.")
    if kullanici.depo_id is None:
        raise PermissionDeniedError("Depocu kullaniciya depo atanmamis.")
    if requested_depo_id is not None and requested_depo_id != kullanici.depo_id:
        raise PermissionDeniedError(f"Bu depo icin yetkiniz yok: depo_id={requested_depo_id}")
    return kullanici.depo_id


def _depo_erisim_dogrula(
    db: Session,
    kullanici_id: int,
    rol: str,
    depo_id: int | None,
) -> None:
    if depo_id is None or rol == "admin":
        return
    kullanici = db.query(KullaniciORM).filter(KullaniciORM.id == kullanici_id).first()
    if kullanici is None:
        raise PermissionDeniedError("Kullanici kaydi bulunamadigi icin depo erisimi dogrulanamadi.")
    if kullanici.rol == "admin":
        return
    if kullanici.depo_erisimi_yok:
        raise PermissionDeniedError("Bu kullanicinin depo erisimi yok.")
    if kullanici.depo_id is not None and kullanici.depo_id != depo_id:
        raise PermissionDeniedError(f"Bu depo icin yetkiniz yok: depo_id={depo_id}")


def _int_opsiyonel(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise BadRequestError("Sayisal alan gecersiz.") from exc
    if parsed <= 0:
        raise BadRequestError("Sayisal alan pozitif olmalidir.")
    return parsed
