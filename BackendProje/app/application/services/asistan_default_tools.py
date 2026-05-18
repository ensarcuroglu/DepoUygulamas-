"""Built-in authoritative tools for BackendProje's assistant registry."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.application.services.asistan_tool_registry import (
    AsistanToolRegistry,
    ToolExecutionContext,
    ToolSpec,
)
from app.core.entities.yerlestirme_gorevi import GorevDurum
from core.api_exceptions import (
    BadRequestError,
    KayitBulunamadiError,
    PermissionDeniedError,
)
from models import Kullanici as KullaniciORM
from models import Palet as PaletORM
from models import Raf as RafORM
from models import YerlestirmeGorevi as YerlestirmeGoreviORM


_YERLESTIRME_KONUM_DEGISTIR = "yerlestirme_konum_degistir"
_ALL_ROLES = frozenset({"admin", "lojistik", "depocu"})


def ensure_default_asistan_tools_registered(registry: AsistanToolRegistry) -> None:
    """Register built-in HITL tools once.

    The registry is process-wide; this helper is intentionally idempotent so it
    can be called from FastAPI dependency wiring without worrying about reloads.
    """
    if registry.get(_YERLESTIRME_KONUM_DEGISTIR) is not None:
        return

    registry.register(
        ToolSpec(
            tool_id=_YERLESTIRME_KONUM_DEGISTIR,
            aciklama=(
                "Paletin mevcut raf bilgisini duzeltir veya bekleyen yerlestirme "
                "gorevinin hedef rafini degistirir."
            ),
            hitl=True,
            rbac_roles=_ALL_ROLES,
            executor=_yerlestirme_konum_degistir,
        )
    )


def _yerlestirme_konum_degistir(context: ToolExecutionContext) -> dict[str, Any]:
    payload = context.payload or {}
    yeni_konum_kodu = _string_al(
        payload,
        "yeni_konum_kodu",
        aliases=("yeni_konum", "raf_kodu", "yeni_raf_kodu"),
    )

    gorev_id = _int_opsiyonel(payload.get("gorev_id"))
    palet_no = _string_opsiyonel(payload.get("palet_no"))

    if gorev_id is None and not palet_no:
        raise BadRequestError("gorev_id veya palet_no alanlarindan biri zorunludur.")

    if gorev_id is not None:
        return _gorev_hedef_raf_degistir(context, gorev_id, yeni_konum_kodu)

    assert palet_no is not None
    return _palet_raf_degistir(context, palet_no, yeni_konum_kodu)


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

    eski_raf_id = gorev.onerilen_raf_id
    gorev.onerilen_raf_id = hedef_raf.id
    if gorev.depo_id is None:
        gorev.depo_id = hedef_raf.depo_id
    db.flush()

    return {
        "tool_id": _YERLESTIRME_KONUM_DEGISTIR,
        "tip": "gorev_hedef_raf_degisti",
        "gorev_id": gorev.id,
        "eski_raf_id": eski_raf_id,
        "yeni_raf_id": hedef_raf.id,
        "yeni_raf_kodu": hedef_raf.kod,
    }


def _palet_raf_degistir(
    context: ToolExecutionContext,
    palet_no: str,
    yeni_konum_kodu: str,
) -> dict[str, Any]:
    db = context.db
    palet = (
        db.query(PaletORM)
        .filter(PaletORM.palet_no == palet_no)
        .with_for_update()
        .first()
    )
    if palet is None:
        raise KayitBulunamadiError("Palet", palet_no)

    mevcut_raf = db.query(RafORM).filter(RafORM.id == palet.raf_id).first()
    depo_id = mevcut_raf.depo_id if mevcut_raf is not None else _int_opsiyonel(
        (context.payload or {}).get("depo_id")
    )
    _depo_erisim_dogrula(db, context.kullanici_id, context.rol, depo_id)
    hedef_raf = _raf_kod_ile_getir(db, yeni_konum_kodu, depo_id=depo_id)

    if depo_id is not None and hedef_raf.depo_id != depo_id:
        raise BadRequestError("Palet farkli depodaki bir rafa tasinamaz.")

    eski_raf_id = palet.raf_id
    palet.raf_id = hedef_raf.id
    db.flush()

    return {
        "tool_id": _YERLESTIRME_KONUM_DEGISTIR,
        "tip": "palet_raf_degisti",
        "palet_no": palet.palet_no,
        "eski_raf_id": eski_raf_id,
        "yeni_raf_id": hedef_raf.id,
        "yeni_raf_kodu": hedef_raf.kod,
    }


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
        raf = db.query(RafORM).filter(RafORM.id == palet.raf_id).first()
        if raf is not None:
            return raf.depo_id
    return None


def _raf_kod_ile_getir(
    db: Session,
    kod: str,
    *,
    depo_id: int | None,
) -> RafORM:
    query = db.query(RafORM).filter(func.lower(RafORM.kod) == kod.lower())
    if depo_id is not None:
        query = query.filter(RafORM.depo_id == depo_id)
    raf = query.first()
    if raf is None:
        raise KayitBulunamadiError("Raf", kod)
    if not raf.aktif:
        raise BadRequestError(f"Raf aktif degil: {kod}")
    return raf


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


def _string_al(payload: dict[str, Any], key: str, *, aliases: tuple[str, ...] = ()) -> str:
    for candidate in (key, *aliases):
        value = _string_opsiyonel(payload.get(candidate))
        if value:
            return value
    raise BadRequestError(f"{key} alani zorunludur.")


def _string_opsiyonel(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_opsiyonel(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise BadRequestError("gorev_id sayisal olmalidir.") from exc
    if parsed <= 0:
        raise BadRequestError("gorev_id pozitif olmalidir.")
    return parsed
