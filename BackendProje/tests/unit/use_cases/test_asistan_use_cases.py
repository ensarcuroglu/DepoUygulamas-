"""Asistan use case birim testleri (DB'siz, in-memory fake'lerle)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pytest

from app.application.dto.asistan_dto import (
    AsistanChatRequestDTO,
    AsistanTaslakOnaylaRequestDTO,
    AsistanTaslakReddetRequestDTO,
    AsistanUpstreamChatResponseDTO,
    ProposedActionDTO,
)
from app.application.services.asistan_tool_registry import (
    AsistanToolRegistry,
    ToolExecutionContext,
    ToolNotAuthorizedError,
    ToolSpec,
)
from app.application.use_cases.asistan_use_cases import (
    AsistanChatProxyUseCase,
    AsistanTaslakListeleUseCase,
    AsistanTaslakOnaylaUseCase,
    AsistanTaslakReddetUseCase,
)
from app.core.entities.asistan_aksiyon_taslagi import (
    AsistanAksiyonTaslagi,
    AsistanTaslakDurum,
)
from core.api_exceptions import (
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeDb:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeTaslakRepo:
    def __init__(self, baslangic: Optional[AsistanAksiyonTaslagi] = None) -> None:
        self._store: dict[int, AsistanAksiyonTaslagi] = {}
        self._next_id = 1
        self.last_kilitli_mi = False
        if baslangic is not None:
            self.olustur(baslangic)

    def getir_id_ile(
        self, taslak_id: int, kilitli_mi: bool = False
    ) -> Optional[AsistanAksiyonTaslagi]:
        self.last_kilitli_mi = kilitli_mi
        return self._store.get(taslak_id)

    def getir_idempotency_ile(self, idempotency_key: str):
        for t in self._store.values():
            if t.idempotency_key == idempotency_key:
                return t
        return None

    def getir_hepsi(
        self,
        kullanici_id: Optional[int] = None,
        durum: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AsistanAksiyonTaslagi]:
        items = list(self._store.values())
        if kullanici_id is not None:
            items = [i for i in items if i.kullanici_id == kullanici_id]
        if durum is not None:
            items = [i for i in items if i.durum == durum]
        return items[skip : skip + limit]

    def olustur(self, taslak: AsistanAksiyonTaslagi, auto_commit: bool = False):
        taslak.id = self._next_id
        self._next_id += 1
        self._store[taslak.id] = taslak
        return taslak

    def guncelle(self, taslak: AsistanAksiyonTaslagi, auto_commit: bool = False):
        self._store[taslak.id] = taslak
        return taslak


class FakeClient:
    def __init__(self, cevap: AsistanUpstreamChatResponseDTO) -> None:
        self.cevap = cevap
        self.last_request = None

    def chat(self, request):
        self.last_request = request
        return self.cevap


def _spec(
    tool_id: str = "stok_sorgula",
    *,
    hitl: bool = False,
    rbac_roles: tuple[str, ...] = ("admin", "depocu"),
    executor=lambda ctx: {"ok": True},
) -> ToolSpec:
    return ToolSpec(
        tool_id=tool_id,
        aciklama=f"{tool_id} test",
        hitl=hitl,
        rbac_roles=frozenset(rbac_roles),
        executor=executor,
    )


def _bekleyen_taslak(
    *,
    kullanici_id: int = 7,
    tool_id: str = "stok_sorgula",
    expires_in: timedelta = timedelta(seconds=900),
) -> AsistanAksiyonTaslagi:
    simdi = datetime.utcnow()
    return AsistanAksiyonTaslagi(
        id=None,
        kullanici_id=kullanici_id,
        rol="admin",
        tool_id=tool_id,
        payload_json={"x": 1},
        durum=AsistanTaslakDurum.BEKLEMEDE,
        ozet="ozet",
        idempotency_key="idem-1",
        created_at=simdi,
        expires_at=simdi + expires_in,
    )


# ---------------------------------------------------------------------------
# ChatProxy
# ---------------------------------------------------------------------------

def test_chat_proxy_no_proposed_action_returns_response_without_taslak():
    registry = AsistanToolRegistry()
    repo = FakeTaslakRepo()
    client = FakeClient(
        AsistanUpstreamChatResponseDTO(cevap="merhaba", session_id="s1"),
    )
    db = FakeDb()
    uc = AsistanChatProxyUseCase(registry, repo, client, db, draft_ttl_seconds=900)

    sonuc = uc.execute(
        AsistanChatRequestDTO(soru="merhaba", session_id="s1"),
        kullanici_id=7,
        rol="admin",
    )

    assert sonuc.cevap == "merhaba"
    assert sonuc.session_id == "s1"
    assert sonuc.taslak is None
    assert db.commits == 0


def test_chat_proxy_with_authorized_hitl_action_persists_taslak():
    registry = AsistanToolRegistry()
    registry.register(_spec("yerlestirme_konum_degistir", hitl=True, rbac_roles=("admin",)))
    repo = FakeTaslakRepo()
    client = FakeClient(
        AsistanUpstreamChatResponseDTO(
            cevap="Onayinizi bekliyorum",
            session_id="s1",
            proposed_action=ProposedActionDTO(
                tool_id="yerlestirme_konum_degistir",
                params={"gorev_id": 42, "yeni_konum": "B-12-3"},
                ozet="Gorev 42 hedefini B-12-3 yap",
            ),
        ),
    )
    db = FakeDb()
    uc = AsistanChatProxyUseCase(registry, repo, client, db, draft_ttl_seconds=600)

    sonuc = uc.execute(
        AsistanChatRequestDTO(soru="A koridoru tikali", session_id="s1"),
        kullanici_id=7,
        rol="admin",
    )

    assert sonuc.taslak is not None
    assert sonuc.taslak.tool_id == "yerlestirme_konum_degistir"
    assert sonuc.taslak.payload_json == {"gorev_id": 42, "yeni_konum": "B-12-3"}
    assert sonuc.taslak.durum == AsistanTaslakDurum.BEKLEMEDE
    assert sonuc.taslak.kullanici_id == 7
    assert sonuc.taslak.expires_at > datetime.utcnow()
    assert sonuc.taslak.idempotency_key  # uuid set
    assert db.commits == 1


def test_chat_proxy_with_unauthorized_hitl_action_raises():
    registry = AsistanToolRegistry()
    registry.register(_spec("siparis_iptal", hitl=True, rbac_roles=("admin",)))
    repo = FakeTaslakRepo()
    client = FakeClient(
        AsistanUpstreamChatResponseDTO(
            cevap="Iptal aciyorum",
            proposed_action=ProposedActionDTO(
                tool_id="siparis_iptal", params={"id": 1}
            ),
        ),
    )
    db = FakeDb()
    uc = AsistanChatProxyUseCase(registry, repo, client, db, draft_ttl_seconds=900)

    with pytest.raises(ToolNotAuthorizedError):
        uc.execute(
            AsistanChatRequestDTO(soru="iptal et"),
            kullanici_id=7,
            rol="depocu",
        )

    assert db.commits == 0


def test_chat_proxy_with_unknown_hitl_action_raises():
    registry = AsistanToolRegistry()
    repo = FakeTaslakRepo()
    client = FakeClient(
        AsistanUpstreamChatResponseDTO(
            cevap="?",
            proposed_action=ProposedActionDTO(tool_id="yok_olan", params={}),
        ),
    )
    db = FakeDb()
    uc = AsistanChatProxyUseCase(registry, repo, client, db, draft_ttl_seconds=900)

    from app.application.services.asistan_tool_registry import ToolNotRegisteredError

    with pytest.raises(ToolNotRegisteredError):
        uc.execute(
            AsistanChatRequestDTO(soru="?"),
            kullanici_id=7,
            rol="admin",
        )


def test_chat_proxy_injects_izinli_tools_into_user_context():
    registry = AsistanToolRegistry()
    registry.register(_spec("stok_sorgula", rbac_roles=("depocu",)))
    registry.register(_spec("siparis_iptal", rbac_roles=("admin",)))
    repo = FakeTaslakRepo()
    client = FakeClient(AsistanUpstreamChatResponseDTO(cevap="ok"))
    db = FakeDb()
    uc = AsistanChatProxyUseCase(registry, repo, client, db)

    uc.execute(
        AsistanChatRequestDTO(soru="?"),
        kullanici_id=7,
        rol="depocu",
    )

    assert client.last_request is not None
    assert client.last_request.user_context.izinli_tool_idleri == ["stok_sorgula"]
    assert client.last_request.user_context.kullanici_id == 7


# ---------------------------------------------------------------------------
# Listele
# ---------------------------------------------------------------------------

def test_listele_returns_dtos_filtered_by_kullanici_and_durum():
    repo = FakeTaslakRepo()
    repo.olustur(_bekleyen_taslak(kullanici_id=1))
    t2 = _bekleyen_taslak(kullanici_id=1)
    t2.idempotency_key = "idem-2"
    t2.durum = AsistanTaslakDurum.ONAYLANDI
    repo.olustur(t2)
    repo.olustur(_bekleyen_taslak(kullanici_id=2))

    uc = AsistanTaslakListeleUseCase(repo)

    sonuc = uc.execute(kullanici_id=1, durum=AsistanTaslakDurum.BEKLEMEDE)
    assert len(sonuc) == 1
    assert sonuc[0].kullanici_id == 1
    assert sonuc[0].durum == AsistanTaslakDurum.BEKLEMEDE


# ---------------------------------------------------------------------------
# Onayla
# ---------------------------------------------------------------------------

def test_onayla_yoksa_not_found():
    registry = AsistanToolRegistry()
    repo = FakeTaslakRepo()
    db = FakeDb()
    uc = AsistanTaslakOnaylaUseCase(registry, repo, db)

    with pytest.raises(NotFoundError):
        uc.execute(
            taslak_id=999,
            kullanici_id=1,
            rol="admin",
            istek=AsistanTaslakOnaylaRequestDTO(),
        )


def test_onayla_baska_kullanici_permission_denied():
    registry = AsistanToolRegistry()
    repo = FakeTaslakRepo(_bekleyen_taslak(kullanici_id=7))
    db = FakeDb()
    uc = AsistanTaslakOnaylaUseCase(registry, repo, db)

    with pytest.raises(PermissionDeniedError):
        uc.execute(
            taslak_id=1,
            kullanici_id=999,
            rol="admin",
            istek=AsistanTaslakOnaylaRequestDTO(),
        )


def test_onayla_zaten_terminal_durum_bad_request():
    registry = AsistanToolRegistry()
    taslak = _bekleyen_taslak()
    taslak.durum = AsistanTaslakDurum.REDDEDILDI
    repo = FakeTaslakRepo(taslak)
    db = FakeDb()
    uc = AsistanTaslakOnaylaUseCase(registry, repo, db)

    with pytest.raises(BadRequestError):
        uc.execute(
            taslak_id=1,
            kullanici_id=7,
            rol="admin",
            istek=AsistanTaslakOnaylaRequestDTO(),
        )


def test_onayla_suresi_dolmus_bad_request_ve_durum_guncellenir():
    registry = AsistanToolRegistry()
    taslak = _bekleyen_taslak(expires_in=timedelta(seconds=-1))
    repo = FakeTaslakRepo(taslak)
    db = FakeDb()
    uc = AsistanTaslakOnaylaUseCase(registry, repo, db)

    with pytest.raises(BadRequestError):
        uc.execute(
            taslak_id=1,
            kullanici_id=7,
            rol="admin",
            istek=AsistanTaslakOnaylaRequestDTO(),
        )
    assert repo.getir_id_ile(1).durum == AsistanTaslakDurum.SURESI_DOLDU
    assert db.commits == 1


def test_onayla_basarili_tool_calistirir_ve_durum_onaylandi():
    registry = AsistanToolRegistry()

    def exec_(ctx: ToolExecutionContext):
        return {"echo": ctx.payload}

    registry.register(_spec("stok_sorgula", executor=exec_))
    repo = FakeTaslakRepo(_bekleyen_taslak(tool_id="stok_sorgula"))
    db = FakeDb()
    uc = AsistanTaslakOnaylaUseCase(registry, repo, db)

    sonuc = uc.execute(
        taslak_id=1,
        kullanici_id=7,
        rol="admin",
        istek=AsistanTaslakOnaylaRequestDTO(),
    )

    assert sonuc.durum == AsistanTaslakDurum.ONAYLANDI
    assert sonuc.sonuc_json == {"echo": {"x": 1}}
    assert sonuc.executed_at is not None
    assert repo.last_kilitli_mi is True
    assert db.commits == 1


def test_onayla_tool_api_exception_taslagi_beklemede_birakir_ve_hata_mesaji_kaydeder():
    registry = AsistanToolRegistry()

    def exec_(ctx: ToolExecutionContext):
        raise BadRequestError("yetersiz envanter")

    registry.register(_spec("stok_sorgula", executor=exec_))
    repo = FakeTaslakRepo(_bekleyen_taslak(tool_id="stok_sorgula"))
    db = FakeDb()
    uc = AsistanTaslakOnaylaUseCase(registry, repo, db)

    with pytest.raises(BadRequestError):
        uc.execute(
            taslak_id=1,
            kullanici_id=7,
            rol="admin",
            istek=AsistanTaslakOnaylaRequestDTO(),
        )

    kayit = repo.getir_id_ile(1)
    assert kayit.durum == AsistanTaslakDurum.BEKLEMEDE
    assert "yetersiz envanter" in (kayit.hata_mesaji or "")


# ---------------------------------------------------------------------------
# Reddet
# ---------------------------------------------------------------------------

def test_reddet_yoksa_not_found():
    repo = FakeTaslakRepo()
    db = FakeDb()
    uc = AsistanTaslakReddetUseCase(repo, db)

    with pytest.raises(NotFoundError):
        uc.execute(taslak_id=42, kullanici_id=1, istek=AsistanTaslakReddetRequestDTO())


def test_reddet_baska_kullanici_permission_denied():
    repo = FakeTaslakRepo(_bekleyen_taslak(kullanici_id=7))
    db = FakeDb()
    uc = AsistanTaslakReddetUseCase(repo, db)

    with pytest.raises(PermissionDeniedError):
        uc.execute(taslak_id=1, kullanici_id=999, istek=AsistanTaslakReddetRequestDTO())


def test_reddet_basarili_durum_reddedildi_ve_sebep_kaydedilir():
    repo = FakeTaslakRepo(_bekleyen_taslak())
    db = FakeDb()
    uc = AsistanTaslakReddetUseCase(repo, db)

    sonuc = uc.execute(
        taslak_id=1,
        kullanici_id=7,
        istek=AsistanTaslakReddetRequestDTO(sebep="yanlis konum"),
    )
    assert sonuc.durum == AsistanTaslakDurum.REDDEDILDI
    assert sonuc.executed_at is not None
    assert "yanlis konum" in (sonuc.hata_mesaji or "")
    assert repo.last_kilitli_mi is True
    assert db.commits == 1
