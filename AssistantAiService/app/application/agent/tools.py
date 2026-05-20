"""Local tool registry for the LangGraph depo assistant.

The assistant service never writes to DB. Read-only tools proxy to BackendProje
through the internal tool endpoint. HITL tools have no executor here and are
converted to ProposedAction by the graph dispatcher.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Iterable, Literal

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, ValidationError, model_validator

from app.core.config import get_settings

log = logging.getLogger(__name__)


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


# ---------------------------------------------------------------------------
# Runtime, spec & registry
# ---------------------------------------------------------------------------

ToolExecutor = Callable[..., Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ToolRuntimeContext:
    user_context: dict[str, Any]
    backend_base_url: str
    internal_api_key: str | None
    timeout: float


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    description: str
    hitl: bool
    rbac_roles: frozenset[str]
    args_schema: type[BaseModel]
    executor: ToolExecutor | None = None
    requires_runtime: bool = False

    def __post_init__(self) -> None:
        if self.hitl and self.executor is not None:
            raise ValueError(
                f"HITL aleti '{self.tool_id}' icin executor tanimlanamaz; "
                "dispatcher cagriyi ProposedAction'a cevirmelidir."
            )
        if not self.hitl and self.executor is None:
            raise ValueError(f"Read-only alet '{self.tool_id}' icin executor zorunludur.")

    def authorized_for(self, rol: str) -> bool:
        return rol in self.rbac_roles


class LocalToolRegistry:
    """In-process registry. Singleton usage through `default_registry()`."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.tool_id in self._tools:
            raise ValueError(f"Alet zaten kayitli: {spec.tool_id}")
        self._tools[spec.tool_id] = spec

    def temizle(self) -> None:
        self._tools.clear()

    def get(self, tool_id: str) -> ToolSpec | None:
        return self._tools.get(tool_id)

    def list_for_role(self, rol: str) -> list[ToolSpec]:
        return [spec for spec in self._tools.values() if spec.authorized_for(rol)]

    def to_langchain_tools(
        self,
        rol: str,
        izinli_tool_idleri: Iterable[str] | None = None,
        runtime_context: ToolRuntimeContext | None = None,
    ) -> list[StructuredTool]:
        """Build StructuredTool instances filtered by Backend allowlist + local RBAC."""
        allow = set(izinli_tool_idleri) if izinli_tool_idleri is not None else None
        out: list[StructuredTool] = []
        for spec in self._tools.values():
            if not spec.authorized_for(rol):
                continue
            if allow is not None and spec.tool_id not in allow:
                continue
            out.append(_spec_to_structured_tool(spec, runtime_context))
        return out


_default_registry: LocalToolRegistry | None = None


def default_registry() -> LocalToolRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = LocalToolRegistry()
        for spec in _builtin_specs():
            _default_registry.register(spec)
    return _default_registry


def reset_default_registry() -> None:
    global _default_registry
    _default_registry = None


# ---------------------------------------------------------------------------
# Args schemas
# ---------------------------------------------------------------------------

class TarihSaatSimdiArgs(BaseModel):
    zone_offset_saat: int = Field(default=3, ge=-12, le=14)


class PaletSorgulaArgs(BaseModel):
    palet_no: str = Field(..., min_length=1, max_length=50)


class RafListeleArgs(BaseModel):
    depo_id: int | None = Field(None, gt=0)
    zon_id: int | None = Field(None, gt=0)
    sadece_aktif: bool = True
    limit: int = Field(default=50, ge=1, le=100)


class GorevDurumuGetirArgs(BaseModel):
    gorev_id: int = Field(..., gt=0)
    gorev_tipi: Literal["yerlestirme", "toplama"] = "yerlestirme"


class StokSorgulaArgs(BaseModel):
    urun_id: int | None = Field(None, gt=0)
    urun_barkod: str | None = Field(None, min_length=1, max_length=80)
    lot_no: str | None = Field(None, min_length=1, max_length=80)
    palet_no: str | None = Field(None, min_length=1, max_length=50)

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


class KarantinayaAlArgs(BaseModel):
    palet_id: int | None = Field(None, gt=0)
    palet_no: str | None = Field(None, min_length=1, max_length=50)
    neden: str = Field(..., min_length=3, max_length=500)

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

    @model_validator(mode="after")
    def _target_required(self):
        if self.siparis_id is None and not self.siparis_no:
            raise ValueError("siparis_id veya siparis_no zorunludur.")
        return self


class YerlestirmeKonumDegistirArgs(BaseModel):
    gorev_id: int | None = Field(None, gt=0)
    palet_no: str | None = Field(None, min_length=1, max_length=50)
    yeni_konum_kodu: str = Field(..., min_length=1, max_length=50)

    @model_validator(mode="after")
    def _target_required(self):
        if self.gorev_id is None and not self.palet_no:
            raise ValueError("gorev_id veya palet_no zorunludur.")
        return self


# Backwards-compatible private aliases used by existing tests/imports.
_TarihSaatArgs = TarihSaatSimdiArgs
_YerlestirmeKonumDegistirArgs = YerlestirmeKonumDegistirArgs


# ---------------------------------------------------------------------------
# LangChain conversion and validation helpers
# ---------------------------------------------------------------------------

def _spec_to_structured_tool(
    spec: ToolSpec,
    runtime_context: ToolRuntimeContext | None,
) -> StructuredTool:
    if spec.hitl:
        async def _hitl_should_not_run(**_kwargs: Any) -> str:
            raise RuntimeError(
                f"HITL alet '{spec.tool_id}' dispatcher tarafindan yakalanmaliydi."
            )

        return StructuredTool.from_function(
            name=spec.tool_id,
            description=spec.description,
            args_schema=spec.args_schema,
            coroutine=_hitl_should_not_run,
        )

    assert spec.executor is not None

    async def _readonly_wrapper(**kwargs: Any) -> dict[str, Any]:
        if spec.requires_runtime:
            if runtime_context is None:
                raise RuntimeError(f"Alet '{spec.tool_id}' runtime context olmadan calisamaz.")
            return await spec.executor(runtime_context=runtime_context, **kwargs)
        return await spec.executor(**kwargs)

    return StructuredTool.from_function(
        name=spec.tool_id,
        description=spec.description,
        args_schema=spec.args_schema,
        coroutine=_readonly_wrapper,
    )


def repair_tool_args(tool_id: str, args: dict[str, Any]) -> dict[str, Any]:
    """Apply conservative aliases seen in Turkish natural language tool calls."""
    repaired = dict(args or {})
    aliases: dict[str, dict[str, str]] = {
        TOOL_PALET_SORGULA: {"palet_barkodu": "palet_no", "barkod": "palet_no"},
        TOOL_STOK_SORGULA: {"barkod": "urun_barkod", "urun_kodu": "urun_barkod"},
        TOOL_GOREV_DURUMU_GETIR: {"id": "gorev_id", "tip": "gorev_tipi"},
        TOOL_PALET_RAF_DEGISTIR: {
            "palet_barkodu": "palet_no",
            "raf_kodu": "yeni_raf_kodu",
            "yeni_konum": "yeni_raf_kodu",
            "yeni_konum_kodu": "yeni_raf_kodu",
        },
        TOOL_KARANTINAYA_AL: {"palet_barkodu": "palet_no", "gerekce": "neden"},
        TOOL_SIPARIS_ONCELIK_DEGISTIR: {
            "id": "siparis_id",
            "oncelik": "yeni_oncelik",
            "yeni_oncelik_degeri": "yeni_oncelik",
            "gerekce": "neden",
        },
        TOOL_YERLESTIRME_KONUM_DEGISTIR: {
            "id": "gorev_id",
            "yeni_konum": "yeni_konum_kodu",
            "raf_kodu": "yeni_konum_kodu",
            "yeni_raf_kodu": "yeni_konum_kodu",
        },
    }
    for source, target in aliases.get(tool_id, {}).items():
        if source in repaired and target not in repaired:
            repaired[target] = repaired.pop(source)
    return repaired


def validate_tool_args(spec: ToolSpec, args: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    repaired = repair_tool_args(spec.tool_id, args)
    try:
        model = spec.args_schema.model_validate(repaired)
    except ValidationError as exc:
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(p) for p in first.get("loc", ())) or "parametre"
        msg = first.get("msg", "gecersiz")
        return None, f"{loc}: {msg}"
    return model.model_dump(exclude_none=True), None


# ---------------------------------------------------------------------------
# Read-only executors
# ---------------------------------------------------------------------------

_GUNLER_TR = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]


async def _tarih_saat_simdi_executor(zone_offset_saat: int = 3) -> dict[str, Any]:
    tz = timezone(timedelta(hours=zone_offset_saat))
    simdi = datetime.now(tz)
    return {
        "iso_datetime": simdi.isoformat(timespec="seconds"),
        "zone_offset_saat": zone_offset_saat,
        "gun_adi": _GUNLER_TR[simdi.weekday()],
    }


def _backend_readonly_executor(tool_id: str) -> ToolExecutor:
    async def _executor(runtime_context: ToolRuntimeContext, **kwargs: Any) -> dict[str, Any]:
        if not runtime_context.internal_api_key:
            raise RuntimeError("INTERNAL_API_KEY yok; Backend read-only tool cagrilamaz.")
        url = f"{runtime_context.backend_base_url.rstrip('/')}/api/asistan/internal/tools/{tool_id}/execute"
        body = {
            "kullanici_id": runtime_context.user_context.get("kullanici_id"),
            "rol": runtime_context.user_context.get("rol"),
            "params": kwargs,
        }
        async with httpx.AsyncClient(timeout=runtime_context.timeout) as client:
            response = await client.post(
                url,
                json=body,
                headers={"X-Internal-Api-Key": runtime_context.internal_api_key},
            )
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise RuntimeError(f"Backend tool hatasi ({response.status_code}): {detail}")
        return response.json()

    return _executor


def build_runtime_context(user_context: dict[str, Any]) -> ToolRuntimeContext:
    settings = get_settings()
    return ToolRuntimeContext(
        user_context=user_context,
        backend_base_url=settings.backend_base_url,
        internal_api_key=settings.internal_api_key,
        timeout=settings.backend_tool_timeout,
    )


# ---------------------------------------------------------------------------
# Built-ins
# ---------------------------------------------------------------------------

def _readonly_backend_spec(
    tool_id: str,
    description: str,
    args_schema: type[BaseModel],
) -> ToolSpec:
    return ToolSpec(
        tool_id=tool_id,
        description=description,
        hitl=False,
        rbac_roles=frozenset({"admin", "lojistik", "depocu"}),
        args_schema=args_schema,
        executor=_backend_readonly_executor(tool_id),
        requires_runtime=True,
    )


def _builtin_specs() -> list[ToolSpec]:
    all_roles = frozenset({"admin", "lojistik", "depocu"})
    return [
        ToolSpec(
            tool_id=TOOL_TARIH_SAAT_SIMDI,
            description="Anlik tarih ve saat bilgisini verir. Sadece saat/tarih sorularinda kullan.",
            hitl=False,
            rbac_roles=all_roles,
            args_schema=TarihSaatSimdiArgs,
            executor=_tarih_saat_simdi_executor,
        ),
        _readonly_backend_spec(
            TOOL_PALET_SORGULA,
            "Palet numarasi verilince paletin urun, lot, raf, depo ve durum bilgisini okur.",
            PaletSorgulaArgs,
        ),
        _readonly_backend_spec(
            TOOL_RAF_LISTELE,
            "Depo veya zon filtresiyle raflari listeler. Raf tasima veya guncelleme icin kullanma.",
            RafListeleArgs,
        ),
        _readonly_backend_spec(
            TOOL_GOREV_DURUMU_GETIR,
            "Tek bir yerlestirme/toplama gorevinin durumunu ve temel alanlarini okur.",
            GorevDurumuGetirArgs,
        ),
        _readonly_backend_spec(
            TOOL_STOK_SORGULA,
            "Urun, barkod, lot veya palet bazinda anlik stok ozetini okur.",
            StokSorgulaArgs,
        ),
        _readonly_backend_spec(
            TOOL_GOREVLERIM_LISTELE,
            "Kullanicinin kendisine atanmis yerlestirme/toplama gorevlerini listeler.",
            GorevlerimListeleArgs,
        ),
        ToolSpec(
            tool_id=TOOL_PALET_RAF_DEGISTIR,
            description=(
                "Paleti baska rafa tasimak/raf bilgisini duzeltmek icin onay teklifi uretir. "
                "Palet no ve yeni raf kodu zorunludur; islem onaydan once yapilmaz."
            ),
            hitl=True,
            rbac_roles=all_roles,
            args_schema=PaletRafDegistirArgs,
        ),
        ToolSpec(
            tool_id=TOOL_KARANTINAYA_AL,
            description=(
                "Paleti karantinaya alma transfer gorevi icin onay teklifi uretir. "
                "Sadece admin rolunde kullan; neden zorunludur."
            ),
            hitl=True,
            rbac_roles=frozenset({"admin"}),
            args_schema=KarantinayaAlArgs,
        ),
        ToolSpec(
            tool_id=TOOL_SIPARIS_ONCELIK_DEGISTIR,
            description=(
                "Siparis onceligini 1=Acil, 5=Normal araliginda degistirmek icin onay teklifi uretir. "
                "Sadece admin/lojistik kullanir; onaydan once islem yapilmaz."
            ),
            hitl=True,
            rbac_roles=frozenset({"admin", "lojistik"}),
            args_schema=SiparisOncelikDegistirArgs,
        ),
        ToolSpec(
            tool_id=TOOL_YERLESTIRME_KONUM_DEGISTIR,
            description=(
                "Legacy arac: yerlestirme gorevi hedef rafini veya palet rafini degistirmek icin "
                "onay teklifi uretir. Yeni palet raf taleplerinde palet_raf_degistir'i tercih et."
            ),
            hitl=True,
            rbac_roles=all_roles,
            args_schema=YerlestirmeKonumDegistirArgs,
        ),
    ]


# ---------------------------------------------------------------------------
# ProposedAction summary
# ---------------------------------------------------------------------------

def compose_proposed_action_ozet(tool_id: str, params: dict[str, Any]) -> str:
    if tool_id == TOOL_PALET_RAF_DEGISTIR:
        return f"Palet {params.get('palet_no')} icin yeni raf: {params.get('yeni_raf_kodu')}"
    if tool_id == TOOL_KARANTINAYA_AL:
        hedef = params.get("palet_no") or f"#{params.get('palet_id')}"
        return f"Palet {hedef} karantinaya alinacak. Neden: {params.get('neden')}"
    if tool_id == TOOL_SIPARIS_ONCELIK_DEGISTIR:
        hedef = params.get("siparis_no") or f"#{params.get('siparis_id')}"
        return f"Siparis {hedef} onceligi {params.get('yeni_oncelik')} yapilacak"
    if tool_id == TOOL_YERLESTIRME_KONUM_DEGISTIR:
        if params.get("palet_no"):
            return f"Palet {params.get('palet_no')} icin yeni raf/konum: {params.get('yeni_konum_kodu')}"
        return f"Gorev #{params.get('gorev_id')} icin yeni hedef konum: {params.get('yeni_konum_kodu')}"
    pieces = ", ".join(f"{k}={v}" for k, v in params.items())
    return f"{tool_id}({pieces})"
