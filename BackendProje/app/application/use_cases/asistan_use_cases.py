"""AssistantAiService entegrasyonu icin use case'ler.

Sorumluluk dagilimi:
- `AsistanChatProxyUseCase`: frontend chat istegini alir, kullanici baglamini
  cikarir, AssistantAiService'e proxy yapar; LLM HITL tool secerse taslagi
  veritabanina yazar ve frontend'e taslak ozetiyle birlikte cevabi doner.
- `AsistanTaslakOnaylaUseCase`: bekleyen taslagi tool registry uzerinden
  authoritative use case'e iletir, sonucu kaydeder, durum gecisi yapar.
- `AsistanTaslakReddetUseCase`: taslagi reddet (durum gecisi + executed_at).
- `AsistanTaslakListeleUseCase`: kullaniciya/role gore filtreli liste.

AssistantAiService DB'ye **dokunmaz**. Tum yazimlar burada gerceklesir.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.application.dto.asistan_dto import (
    AsistanChatRequestDTO,
    AsistanChatResponseDTO,
    AsistanTaslakOnaylaRequestDTO,
    AsistanTaslakReddetRequestDTO,
    AsistanTaslakResponseDTO,
    AsistanUpstreamChatRequestDTO,
    AsistanUserContextDTO,
    ProposedActionDTO,
)
from app.application.services.asistan_tool_registry import (
    AsistanToolRegistry,
    ToolExecutionContext,
)
from app.core.entities.asistan_aksiyon_taslagi import (
    AsistanAksiyonTaslagi,
    AsistanTaslakDurum,
)
from app.core.repositories.asistan_aksiyon_taslagi_repository import (
    IAsistanAksiyonTaslagiRepository,
)
from core.api_exceptions import (
    APIException,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_response_dto(entity: AsistanAksiyonTaslagi) -> AsistanTaslakResponseDTO:
    return AsistanTaslakResponseDTO(
        id=entity.id,
        kullanici_id=entity.kullanici_id,
        rol=entity.rol,
        tool_id=entity.tool_id,
        payload_json=entity.payload_json,
        durum=entity.durum,
        ozet=entity.ozet,
        idempotency_key=entity.idempotency_key,
        sonuc_json=entity.sonuc_json,
        hata_mesaji=entity.hata_mesaji,
        created_at=entity.created_at,
        expires_at=entity.expires_at,
        executed_at=entity.executed_at,
    )


# ---------------------------------------------------------------------------
# Chat proxy
# ---------------------------------------------------------------------------

class AsistanChatProxyUseCase:
    def __init__(
        self,
        tool_registry: AsistanToolRegistry,
        taslak_repo: IAsistanAksiyonTaslagiRepository,
        client,  # AssistantAiClient (duck-typed for testability)
        db: Session,
        draft_ttl_seconds: int = 900,
    ) -> None:
        self._registry = tool_registry
        self._taslak_repo = taslak_repo
        self._client = client
        self._db = db
        self._ttl_seconds = draft_ttl_seconds

    def execute(
        self,
        istek: AsistanChatRequestDTO,
        kullanici_id: int,
        rol: str,
    ) -> AsistanChatResponseDTO:
        izinli_tools = [spec.tool_id for spec in self._registry.list_for_role(rol)]

        user_context = AsistanUserContextDTO(
            kullanici_id=kullanici_id,
            rol=rol,
            aktif_gorev_id=istek.aktif_gorev_id,
            aktif_ekran=istek.aktif_ekran,
            izinli_tool_idleri=izinli_tools,
        )
        upstream = AsistanUpstreamChatRequestDTO(
            soru=istek.soru,
            session_id=istek.session_id,
            user_context=user_context,
        )

        cevap = self._client.chat(upstream)

        taslak_dto: Optional[AsistanTaslakResponseDTO] = None
        if cevap.proposed_action is not None:
            taslak_dto = self._persist_draft(
                proposed=cevap.proposed_action,
                kullanici_id=kullanici_id,
                rol=rol,
            )

        return AsistanChatResponseDTO(
            soru=istek.soru,
            cevap=cevap.cevap,
            session_id=cevap.session_id or istek.session_id,
            taslak=taslak_dto,
            debug=cevap.debug,
        )

    # ----- internal -----

    def _persist_draft(
        self,
        proposed: ProposedActionDTO,
        kullanici_id: int,
        rol: str,
    ) -> AsistanTaslakResponseDTO:
        # Tool registry'de yoksa veya rol yetkisi yoksa hemen 4xx don;
        # AssistantAi yanlis tool secmis demektir.
        self._registry.authorize(proposed.tool_id, rol)

        simdi = datetime.utcnow()
        entity = AsistanAksiyonTaslagi(
            kullanici_id=kullanici_id,
            rol=rol,
            tool_id=proposed.tool_id,
            payload_json=proposed.params,
            durum=AsistanTaslakDurum.BEKLEMEDE,
            ozet=proposed.ozet,
            idempotency_key=uuid.uuid4().hex,
            created_at=simdi,
            expires_at=simdi + timedelta(seconds=self._ttl_seconds),
        )
        try:
            kayit = self._taslak_repo.olustur(entity)
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return _to_response_dto(kayit)


# ---------------------------------------------------------------------------
# Listele
# ---------------------------------------------------------------------------

class AsistanTaslakListeleUseCase:
    def __init__(self, repo: IAsistanAksiyonTaslagiRepository) -> None:
        self._repo = repo

    def execute(
        self,
        kullanici_id: Optional[int] = None,
        durum: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AsistanTaslakResponseDTO]:
        kayitlar = self._repo.getir_hepsi(
            kullanici_id=kullanici_id,
            durum=durum,
            skip=skip,
            limit=limit,
        )
        return [_to_response_dto(k) for k in kayitlar]


# ---------------------------------------------------------------------------
# Onayla
# ---------------------------------------------------------------------------

class AsistanTaslakOnaylaUseCase:
    def __init__(
        self,
        tool_registry: AsistanToolRegistry,
        taslak_repo: IAsistanAksiyonTaslagiRepository,
        db: Session,
    ) -> None:
        self._registry = tool_registry
        self._taslak_repo = taslak_repo
        self._db = db

    def execute(
        self,
        taslak_id: int,
        kullanici_id: int,
        rol: str,
        istek: AsistanTaslakOnaylaRequestDTO,
    ) -> AsistanTaslakResponseDTO:
        taslak = self._taslak_repo.getir_id_ile(taslak_id, kilitli_mi=True)
        if taslak is None:
            raise NotFoundError("Asistan Aksiyon Taslagi", taslak_id)

        if taslak.kullanici_id != kullanici_id:
            raise PermissionDeniedError(
                "Bu taslagi sadece olusturan kullanici onaylayabilir."
            )

        if taslak.durum != AsistanTaslakDurum.BEKLEMEDE:
            raise BadRequestError(
                f"Taslak zaten {taslak.durum} durumunda; onay islemi yapilamaz."
            )

        if taslak.suresi_dolmus_mu():
            taslak.suresi_doldu()
            try:
                self._taslak_repo.guncelle(taslak)
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise
            raise BadRequestError("Taslagin onay suresi dolmus.")

        context = ToolExecutionContext(
            kullanici_id=kullanici_id,
            rol=rol,
            payload=taslak.payload_json,
            db=self._db,
        )

        try:
            sonuc = self._registry.execute(context, taslak.tool_id)
        except APIException as exc:
            self._db.rollback()
            # Tool calistirilamadiysa taslagi hala BEKLEMEDE birak; kullanici
            # tool register edildikten sonra tekrar deneyebilir.
            taslak.hata_mesaji = exc.message[:500]
            try:
                self._taslak_repo.guncelle(taslak)
                self._db.commit()
            except Exception:
                self._db.rollback()
            raise

        taslak.onayla(sonuc)
        try:
            kayit = self._taslak_repo.guncelle(taslak)
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return _to_response_dto(kayit)


# ---------------------------------------------------------------------------
# Reddet
# ---------------------------------------------------------------------------

class AsistanTaslakReddetUseCase:
    def __init__(
        self,
        taslak_repo: IAsistanAksiyonTaslagiRepository,
        db: Session,
    ) -> None:
        self._taslak_repo = taslak_repo
        self._db = db

    def execute(
        self,
        taslak_id: int,
        kullanici_id: int,
        istek: AsistanTaslakReddetRequestDTO,
    ) -> AsistanTaslakResponseDTO:
        taslak = self._taslak_repo.getir_id_ile(taslak_id, kilitli_mi=True)
        if taslak is None:
            raise NotFoundError("Asistan Aksiyon Taslagi", taslak_id)

        if taslak.kullanici_id != kullanici_id:
            raise PermissionDeniedError(
                "Bu taslagi sadece olusturan kullanici reddedebilir."
            )

        if taslak.durum != AsistanTaslakDurum.BEKLEMEDE:
            raise BadRequestError(
                f"Taslak zaten {taslak.durum} durumunda; reddetme islemi yapilamaz."
            )

        taslak.reddet()
        if istek.sebep:
            taslak.hata_mesaji = istek.sebep[:500]
        try:
            kayit = self._taslak_repo.guncelle(taslak)
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return _to_response_dto(kayit)
