"""
Rapor API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import date

from app.core.auth import require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_rapor_sablon_listele_uc,
    get_rapor_sablon_getir_uc,
    get_rapor_sablon_olustur_uc,
    get_rapor_sablon_guncelle_uc,
    get_rapor_sablon_sil_uc,
    get_rapor_logu_listele_uc,
    get_rapor_schedule_listele_uc,
    get_rapor_schedule_getir_uc,
    get_rapor_schedule_olustur_uc,
    get_rapor_schedule_guncelle_uc,
    get_rapor_schedule_sil_uc,
    get_rapor_schedule_tetikle_uc,
    get_rapor_veri_sorgula_uc,
    get_rapor_export_uc,
    get_yerlestirme_gorevi_repo,
    get_raf_repo,
    get_palet_repo,
)
from app.application.dto.rapor_dto import (
    RaporSablonuOlusturRequestDTO,
    RaporSablonuGuncelleRequestDTO,
    RaporSablonuResponseDTO,
    RaporLoguResponseDTO,
    RaporScheduleOlusturRequestDTO,
    RaporScheduleGuncelleRequestDTO,
    RaporScheduleResponseDTO,
)
from app.application.use_cases.rapor_use_cases import (
    RaporSablonuListeleUseCase,
    RaporSablonuGetirUseCase,
    RaporSablonuOlusturUseCase,
    RaporSablonuGuncelleUseCase,
    RaporSablonuSilUseCase,
    RaporLoguListeleUseCase,
    RaporScheduleListeleUseCase,
    RaporScheduleGetirUseCase,
    RaporScheduleOlusturUseCase,
    RaporScheduleGuncelleUseCase,
    RaporScheduleSilUseCase,
    RaporScheduleTetikleUseCase,
    RaporVeriSorgulaUseCase,
    RaporExportUseCase,
)

router = APIRouter(prefix="/api/raporlar", tags=["Raporlar"])


@router.get("/sablonlar", response_model=List[RaporSablonuResponseDTO])
@limiter.limit("100/minute")
def rapor_sablonlarini_listele(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    tur: Optional[str] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: RaporSablonuListeleUseCase = Depends(get_rapor_sablon_listele_uc),
):
    return uc.execute(skip=skip, limit=limit, tur=tur)


@router.get("/sablonlar/{sablon_id}", response_model=RaporSablonuResponseDTO)
@limiter.limit("100/minute")
def rapor_sablonunu_getir(
    request: Request,
    sablon_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: RaporSablonuGetirUseCase = Depends(get_rapor_sablon_getir_uc),
):
    return uc.execute(sablon_id)


@router.post("/sablonlar", response_model=RaporSablonuResponseDTO, status_code=201)
@limiter.limit("50/minute")
def rapor_sablonu_ekle(
    request: Request,
    sablon: RaporSablonuOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: RaporSablonuOlusturUseCase = Depends(get_rapor_sablon_olustur_uc),
):
    return uc.execute(sablon, kullanici_id=current_user.id)


@router.put("/sablonlar/{sablon_id}", response_model=RaporSablonuResponseDTO)
@limiter.limit("50/minute")
def rapor_sablonunu_guncelle(
    request: Request,
    sablon_id: int,
    sablon_update: RaporSablonuGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: RaporSablonuGuncelleUseCase = Depends(get_rapor_sablon_guncelle_uc),
):
    return uc.execute(sablon_id, sablon_update, kullanici_id=current_user.id)


@router.delete("/sablonlar/{sablon_id}")
@limiter.limit("50/minute")
def rapor_sablonunu_sil(
    request: Request,
    sablon_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: RaporSablonuSilUseCase = Depends(get_rapor_sablon_sil_uc),
):
    uc.execute(sablon_id, kullanici_id=current_user.id)
    return {"message": "Rapor şablonu başarıyla pasife alındı", "id": sablon_id}


@router.get("/stok/veriler")
@limiter.limit("100/minute")
def stok_raporu_verisi(
    request: Request,
    urun_id: Optional[int] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: RaporVeriSorgulaUseCase = Depends(get_rapor_veri_sorgula_uc),
):
    return uc.execute(tur="stok", kullanici_id=current_user.id, urun_id=urun_id)


@router.get("/siparis/veriler")
@limiter.limit("100/minute")
def siparis_raporu_verisi(
    request: Request,
    baslang_tarihi: Optional[date] = Query(None),
    bitis_tarihi: Optional[date] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: RaporVeriSorgulaUseCase = Depends(get_rapor_veri_sorgula_uc),
):
    return uc.execute(
        tur="siparis", kullanici_id=current_user.id,
        baslang_tarihi=baslang_tarihi, bitis_tarihi=bitis_tarihi,
    )


@router.get("/hareket/veriler")
@limiter.limit("100/minute")
def hareket_raporu_verisi(
    request: Request,
    baslang_tarihi: Optional[date] = Query(None),
    bitis_tarihi: Optional[date] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: RaporVeriSorgulaUseCase = Depends(get_rapor_veri_sorgula_uc),
):
    return uc.execute(
        tur="hareket", kullanici_id=current_user.id,
        baslang_tarihi=baslang_tarihi, bitis_tarihi=bitis_tarihi,
    )


@router.get("/kritik-stok")
@limiter.limit("100/minute")
def kritik_stok_raporu(
    request: Request,
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: RaporVeriSorgulaUseCase = Depends(get_rapor_veri_sorgula_uc),
):
    return uc.execute(tur="kritik_stok", kullanici_id=current_user.id)


@router.get("/skt")
@limiter.limit("100/minute")
def skt_raporu(
    request: Request,
    gun: int = Query(30, description="Kaç gün içinde SKT dolacak"),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: RaporVeriSorgulaUseCase = Depends(get_rapor_veri_sorgula_uc),
):
    return uc.execute(tur="skt", kullanici_id=current_user.id, gun=gun)


@router.get("/abc-analiz")
@limiter.limit("100/minute")
def abc_analiz_raporu(
    request: Request,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: RaporVeriSorgulaUseCase = Depends(get_rapor_veri_sorgula_uc),
):
    return uc.execute(tur="abc", kullanici_id=current_user.id)


@router.get("/doluluk")
@limiter.limit("100/minute")
def depo_doluluk_raporu(
    request: Request,
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: RaporVeriSorgulaUseCase = Depends(get_rapor_veri_sorgula_uc),
):
    return uc.execute(tur="doluluk", kullanici_id=current_user.id)


@router.post("/export")
@limiter.limit("50/minute")
def rapor_export(
    request: Request,
    sablon_id: Optional[int] = None,
    tur: str = Query("stok", description="stok | siparis | hareket | kritik_stok | skt"),
    format: str = Query("csv", description="csv | excel"),
    baslang_tarihi: Optional[date] = Query(None),
    bitis_tarihi: Optional[date] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: RaporExportUseCase = Depends(get_rapor_export_uc),
):
    buffer, media_type, filename = uc.execute(
        tur=tur, format=format, kullanici_id=current_user.id,
        baslang_tarihi=baslang_tarihi, bitis_tarihi=bitis_tarihi,
        sablon_id=sablon_id,
    )
    return StreamingResponse(
        buffer, media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/log", response_model=List[RaporLoguResponseDTO])
@limiter.limit("100/minute")
def rapor_loglari_listele(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    sablon_id: Optional[int] = Query(None),
    current_user: Kullanici = Depends(require_role("admin")),
    uc: RaporLoguListeleUseCase = Depends(get_rapor_logu_listele_uc),
):
    return uc.execute(skip=skip, limit=limit, sablon_id=sablon_id)


@router.get("/schedule", response_model=List[RaporScheduleResponseDTO])
@limiter.limit("100/minute")
def rapor_schedules_listele(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: RaporScheduleListeleUseCase = Depends(get_rapor_schedule_listele_uc),
):
    return uc.execute(skip=skip, limit=limit)


@router.get("/schedule/{schedule_id}", response_model=RaporScheduleResponseDTO)
@limiter.limit("100/minute")
def rapor_schedule_detay(
    request: Request,
    schedule_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: RaporScheduleGetirUseCase = Depends(get_rapor_schedule_getir_uc),
):
    return uc.execute(schedule_id)


@router.post("/schedule", response_model=RaporScheduleResponseDTO, status_code=201)
@limiter.limit("50/minute")
def rapor_schedule_ekle(
    request: Request,
    schedule: RaporScheduleOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: RaporScheduleOlusturUseCase = Depends(get_rapor_schedule_olustur_uc),
):
    return uc.execute(schedule, kullanici_id=current_user.id)


@router.put("/schedule/{schedule_id}", response_model=RaporScheduleResponseDTO)
@limiter.limit("50/minute")
def rapor_schedule_guncelle(
    request: Request,
    schedule_id: int,
    schedule_update: RaporScheduleGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: RaporScheduleGuncelleUseCase = Depends(get_rapor_schedule_guncelle_uc),
):
    return uc.execute(schedule_id, schedule_update, kullanici_id=current_user.id)


@router.delete("/schedule/{schedule_id}")
@limiter.limit("50/minute")
def rapor_schedule_sil(
    request: Request,
    schedule_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: RaporScheduleSilUseCase = Depends(get_rapor_schedule_sil_uc),
):
    uc.execute(schedule_id, kullanici_id=current_user.id)
    return {"message": "Zamanlı rapor başarıyla silindi", "id": schedule_id}


@router.post("/schedule/tetikle")
@limiter.limit("50/minute")
def rapor_schedule_tetikle(
    request: Request,
    schedule_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: RaporScheduleTetikleUseCase = Depends(get_rapor_schedule_tetikle_uc),
):
    return uc.execute(schedule_id, kullanici_id=current_user.id)


# ─────────────────────────────────────────
# FAZ 3 — PUTAWAY RAPORLAMA ENDPOİNT'LERİ
# ─────────────────────────────────────────

@router.get("/yerlestirme-performans")
@limiter.limit("60/minute")
def yerlestirme_performans_raporu(
    request: Request,
    depo_id: Optional[int] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    gorev_repo=Depends(get_yerlestirme_gorevi_repo),
    raf_repo=Depends(get_raf_repo),
):
    """
    Yerleştirme performans raporu:
    - Ortalama yerleştirme süresi (ATANDI → TAMAMLANDI)
    - Override oranı (gerceklesen_raf != onerilen_raf)
    - Görev tipi dağılımı
    """
    gorevler = gorev_repo.getir_hepsi(durum="Tamamlandi", limit=10000)
    if depo_id is not None:
        raf_depo_cache = {}

        def _raf_depo_id_getir(raf_id: int) -> Optional[int]:
            if raf_id not in raf_depo_cache:
                raf = raf_repo.getir_id_ile(raf_id)
                raf_depo_cache[raf_id] = raf.depo_id if raf else None
            return raf_depo_cache[raf_id]

        gorevler = [
            g for g in gorevler
            if (g.gerceklesen_raf_id or g.onerilen_raf_id)
            and _raf_depo_id_getir(g.gerceklesen_raf_id or g.onerilen_raf_id) == depo_id
        ]

    sureli = [
        g for g in gorevler
        if g.baslama_tarihi and g.tamamlanma_tarihi
    ]
    override_sayisi = sum(
        1 for g in gorevler
        if g.gerceklesen_raf_id and g.gerceklesen_raf_id != g.onerilen_raf_id
    )

    ort_sure_dk = None
    if sureli:
        toplam_sn = sum(
            (g.tamamlanma_tarihi - g.baslama_tarihi).total_seconds()
            for g in sureli
        )
        ort_sure_dk = round(toplam_sn / len(sureli) / 60, 1)

    tip_dagilimi: dict = {}
    for g in gorevler:
        tip_dagilimi[g.tip] = tip_dagilimi.get(g.tip, 0) + 1

    return {
        "toplam_tamamlanan": len(gorevler),
        "override_sayisi": override_sayisi,
        "override_orani_yuzde": round(override_sayisi / max(len(gorevler), 1) * 100, 1),
        "ortalama_sure_dakika": ort_sure_dk,
        "tip_dagilimi": tip_dagilimi,
    }


@router.get("/bilinmeyen-konum")
@limiter.limit("60/minute")
def bilinmeyen_konum_raporu(
    request: Request,
    depo_id: int = Query(..., description="Depo ID"),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    raf_repo=Depends(get_raf_repo),
    palet_repo=Depends(get_palet_repo),
):
    """
    MIGRATION_STAGING raftaki palet sayısı — doluluk oranları kesin değildir uyarısı.
    """
    staging_raf = raf_repo.getir_staging_raf(depo_id)
    if not staging_raf:
        return {
            "uyari": None,
            "bilinmeyen_konum_palet_sayisi": 0,
            "mesaj": "Bu depo için MIGRATION_STAGING rafı bulunamadı.",
        }

    paletler = palet_repo.getir_hepsi(raf_id=staging_raf.id, sadece_aktif=True, limit=10000)
    palet_sayisi = len(paletler)

    return {
        "uyari": "Geçici Veri İçeriyor" if palet_sayisi > 0 else None,
        "bilinmeyen_konum_palet_sayisi": palet_sayisi,
        "staging_raf_id": staging_raf.id,
        "staging_raf_kod": staging_raf.kod,
        "mesaj": (
            f"{palet_sayisi} palet henüz konumlandırılmamış. "
            "Doluluk oranları kesin değildir."
            if palet_sayisi > 0
            else "Tüm paletler konumlandırılmış."
        ),
    }
