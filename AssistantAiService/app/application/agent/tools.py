"""Local tool registry for the depo asistani agent.

Tasarim notlari:
- **Authoritative state Backend'de**. Bu registry yalniz LLM'in alet
  cagirabilmesi icin gereken meta + read-only yardimci executor'lari icerir.
- **HITL aletler asla burada calistirilmaz.** `hitl=True` aletlerin
  `executor` alani `None` olur; graph dispatcher cagriyi yakalayip
  `proposed_action`'a donusturur (bkz. `nodes.py`).
- LangChain `StructuredTool`'a donusum sadece graph build sirasinda yapilir;
  registry domain'i framework'siz tutulur.

Faz 2 PoC araclari:
- `tarih_saat_simdi` (read-only, herkes) — Turkiye saatiyle anlik datetime.
- `yerlestirme_konum_degistir` (HITL, admin/lojistik/depocu) — kanit gorevi;
  asla burada calistirilmaz, ProposedAction olusur.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Iterable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, model_validator

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool spec & registry
# ---------------------------------------------------------------------------

ToolExecutor = Callable[..., Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    description: str
    hitl: bool
    rbac_roles: frozenset[str]
    args_schema: type[BaseModel]
    executor: ToolExecutor | None = None

    def __post_init__(self) -> None:
        if self.hitl and self.executor is not None:
            raise ValueError(
                f"HITL aleti '{self.tool_id}' icin executor tanimlanamaz; "
                "graph dispatcher cagriyi yakalayip ProposedAction'a cevirir."
            )
        if not self.hitl and self.executor is None:
            raise ValueError(
                f"Read-only alet '{self.tool_id}' icin executor zorunludur."
            )

    def authorized_for(self, rol: str) -> bool:
        return rol in self.rbac_roles


class LocalToolRegistry:
    """In-process registry. Singleton kullanim icin `default_registry()`."""

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
    ) -> list[StructuredTool]:
        """Build LangChain `StructuredTool` instances filtered by role + allowlist.

        `izinli_tool_idleri` Backend'in JWT'den cikarttigi guvenli liste.
        Defansif olarak hem registry rbac'i hem de allowlist uygulanir.
        """
        allow = set(izinli_tool_idleri) if izinli_tool_idleri is not None else None
        out: list[StructuredTool] = []
        for spec in self._tools.values():
            if not spec.authorized_for(rol):
                continue
            if allow is not None and spec.tool_id not in allow:
                continue
            out.append(_spec_to_structured_tool(spec))
        return out


# Modul seviyesi singleton — Faz 2'de bootstrap'ta tools register edilir.
_default_registry: LocalToolRegistry | None = None


def default_registry() -> LocalToolRegistry:
    """Lazy-initialize the default registry with built-in v1 tools."""
    global _default_registry
    if _default_registry is None:
        _default_registry = LocalToolRegistry()
        for spec in _builtin_specs():
            _default_registry.register(spec)
    return _default_registry


def reset_default_registry() -> None:
    """Test isolation helper."""
    global _default_registry
    _default_registry = None


# ---------------------------------------------------------------------------
# LangChain conversion
# ---------------------------------------------------------------------------

def _spec_to_structured_tool(spec: ToolSpec) -> StructuredTool:
    """Convert a ToolSpec into a StructuredTool usable by ChatOllama.bind_tools."""
    if spec.hitl:
        # HITL araclarinin coroutine'i hicbir zaman dispatcher tarafindan
        # cagrilmamali; yanlislikla cagrilirsa actor'a anlamli hata vermeli.
        async def _hitl_should_not_run(**_kwargs: Any) -> str:
            raise RuntimeError(
                f"HITL alet '{spec.tool_id}' graph dispatcher tarafindan "
                "yakalanmaliydi; bu cagri yanlis route edildi."
            )

        return StructuredTool.from_function(
            name=spec.tool_id,
            description=spec.description,
            args_schema=spec.args_schema,
            coroutine=_hitl_should_not_run,
        )

    assert spec.executor is not None  # __post_init__ ensures
    return StructuredTool.from_function(
        name=spec.tool_id,
        description=spec.description,
        args_schema=spec.args_schema,
        coroutine=spec.executor,
    )


# ---------------------------------------------------------------------------
# v1 PoC tools
# ---------------------------------------------------------------------------

class _TarihSaatArgs(BaseModel):
    zone_offset_saat: int = Field(
        default=3,
        ge=-12,
        le=14,
        description="UTC offset saat olarak. Turkiye icin 3.",
    )


_GUNLER_TR = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]


async def _tarih_saat_simdi_executor(zone_offset_saat: int = 3) -> dict[str, Any]:
    tz = timezone(timedelta(hours=zone_offset_saat))
    simdi = datetime.now(tz)
    return {
        "iso_datetime": simdi.isoformat(timespec="seconds"),
        "zone_offset_saat": zone_offset_saat,
        "gun_adi": _GUNLER_TR[simdi.weekday()],
    }


class _YerlestirmeKonumDegistirArgs(BaseModel):
    gorev_id: int | None = Field(
        None,
        ge=1,
        description="Bekleyen yerlestirme gorev kimligi. Palet no biliniyorsa bos birak.",
    )
    palet_no: str | None = Field(
        None,
        min_length=1,
        max_length=30,
        description="Raf bilgisi duzeltilecek palet numarasi, ornek: PRD-20260519-0001.",
    )
    yeni_konum_kodu: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Hedef raf/lokasyon kodu, ornek: 'B-12-3'.",
    )

    @model_validator(mode="after")
    def _target_required(self):
        if self.gorev_id is None and not self.palet_no:
            raise ValueError("gorev_id veya palet_no alanlarindan biri zorunludur.")
        return self


def _builtin_specs() -> list[ToolSpec]:
    _ALL_ROLLER = frozenset({"admin", "lojistik", "depocu"})
    return [
        ToolSpec(
            tool_id="tarih_saat_simdi",
            description=(
                "Sistemin anlik tarih ve saatini Turkiye saatine gore donderir. "
                "Kullanicidan acikca istendiginde veya zaman damgasi gerektiren "
                "bir cevap olusturmak gerektiginde cagir."
            ),
            hitl=False,
            rbac_roles=_ALL_ROLLER,
            args_schema=_TarihSaatArgs,
            executor=_tarih_saat_simdi_executor,
        ),
        ToolSpec(
            tool_id="yerlestirme_konum_degistir",
            description=(
                "Bir paletin mevcut raf bilgisini duzeltmek veya bekleyen bir "
                "yerlestirme gorevinin hedef konumunu degistirmek icin **onay "
                "teklifi** uretir. Kullanici palet numarasi verdiyse palet_no, "
                "gorev numarasi verdiyse gorev_id kullan. Calistirma kullanici "
                "onayindan sonra Backend tarafinda yapilir; sonucu uydurma."
            ),
            hitl=True,
            rbac_roles=_ALL_ROLLER,
            args_schema=_YerlestirmeKonumDegistirArgs,
            executor=None,
        ),
    ]


# ---------------------------------------------------------------------------
# Yardimci: ProposedAction icin Turkce ozet
# ---------------------------------------------------------------------------

def compose_proposed_action_ozet(tool_id: str, params: dict[str, Any]) -> str:
    """HITL aksiyonu kullaniciya gosterilirken seven gozler icin kisa ozet."""
    if tool_id == "yerlestirme_konum_degistir":
        palet_no = params.get("palet_no")
        gorev = params.get("gorev_id")
        konum = params.get("yeni_konum_kodu")
        if palet_no:
            return f"Palet {palet_no} icin yeni raf/konum: {konum}"
        return f"Gorev #{gorev} icin yeni hedef konum: {konum}"
    # Geri donus: tool_id + key=value listesi
    pieces = ", ".join(f"{k}={v}" for k, v in params.items())
    return f"{tool_id}({pieces})"
