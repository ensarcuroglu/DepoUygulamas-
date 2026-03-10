from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
import io
import csv

from database import get_db
from auth import require_role
from models import Kullanici, RaporLogu
import crud
from schemas import (
    RaporSablonuCreate, RaporSablonuUpdate, RaporSablonuResponse,
    RaporLoguCreate, RaporLoguResponse,
    RaporScheduleCreate, RaporScheduleUpdate, RaporScheduleResponse
)

router = APIRouter(prefix="/api/raporlar", tags=["Raporlar"])


# ========================
# RAPOR ŞABLONLARI
# ========================

@router.get("/sablonlar", response_model=list[RaporSablonuResponse])
def rapor_sablonlarini_listele(
    skip: int = 0,
    limit: int = 100,
    tur: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Tüm rapor şablonlarını listeler"""
    return crud.get_rapor_sablonlari(db, skip=skip, limit=limit, tur=tur)


@router.get("/sablonlar/{sablon_id}", response_model=RaporSablonuResponse)
def rapor_sablonunu_getir(
    sablon_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Belirli bir rapor şablonunu getirir"""
    db_sablon = crud.get_rapor_sablonu(db, sablon_id)
    if not db_sablon:
        raise HTTPException(status_code=404, detail="Rapor şablonu bulunamadı")
    return db_sablon


@router.post("/sablonlar", response_model=RaporSablonuResponse, status_code=201)
def rapor_sablonu_ekle(
    sablon: RaporSablonuCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Yeni bir rapor şablonu oluşturur"""
    return crud.create_rapor_sablonu(db, sablon, kullanici_id=current_user.id)


@router.put("/sablonlar/{sablon_id}", response_model=RaporSablonuResponse)
def rapor_sablonunu_guncelle(
    sablon_id: int,
    sablon_update: RaporSablonuUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Rapor şablonunu günceller"""
    db_sablon = crud.update_rapor_sablonu(db, sablon_id, sablon_update, kullanici_id=current_user.id)
    if not db_sablon:
        raise HTTPException(status_code=404, detail="Rapor şablonu bulunamadı")
    return db_sablon


@router.delete("/sablonlar/{sablon_id}")
def rapor_sablonunu_sil(
    sablon_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Rapor şablonunu pasife alır"""
    success = crud.delete_rapor_sablonu(db, sablon_id, kullanici_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Rapor şablonu bulunamadı")
    return {"message": "Rapor şablonu başarıyla pasife alındı", "id": sablon_id}


# ========================
# RAPOR VERİLERİ
# ========================

@router.get("/stok/veriler")
def stok_raporu_verisi(
    urun_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """Stok raporu için veri döndür"""
    veri = crud.get_stok_raporu_verileri(db, urun_id=urun_id)
    # Rapor logu kaydet
    crud.create_rapor_logu(db, RaporLoguCreate(
        sablon_id=None, parametreler={"urun_id": urun_id, "tur": "stok"}, durum="Basarili"
    ), kullanici_id=current_user.id)
    return {"veri": veri}


@router.get("/siparis/veriler")
def siparis_raporu_verisi(
    baslang_tarihi: Optional[date] = Query(None),
    bitis_tarihi: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Sipariş raporu için veri döndür"""
    veri = crud.get_siparis_raporu_verileri(db, baslang_tarihi, bitis_tarihi)
    crud.create_rapor_logu(db, RaporLoguCreate(
        sablon_id=None,
        parametreler={"baslang_tarihi": str(baslang_tarihi), "bitis_tarihi": str(bitis_tarihi), "tur": "siparis"},
        durum="Basarili"
    ), kullanici_id=current_user.id)
    return {"veri": veri}


@router.get("/hareket/veriler")
def hareket_raporu_verisi(
    baslang_tarihi: Optional[date] = Query(None),
    bitis_tarihi: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """Stok hareketi raporu için veri döndür"""
    veri = crud.get_hareket_raporu_verileri(db, baslang_tarihi, bitis_tarihi)
    crud.create_rapor_logu(db, RaporLoguCreate(
        sablon_id=None,
        parametreler={"baslang_tarihi": str(baslang_tarihi), "bitis_tarihi": str(bitis_tarihi), "tur": "hareket"},
        durum="Basarili"
    ), kullanici_id=current_user.id)
    return {"veri": veri}


@router.get("/kritik-stok")
def kritik_stok_raporu(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """Min stok seviyesinin altındaki ürünler"""
    veri = crud.get_kritik_stok_raporu(db)
    crud.create_rapor_logu(db, RaporLoguCreate(
        sablon_id=None, parametreler={"tur": "kritik_stok"}, durum="Basarili"
    ), kullanici_id=current_user.id)
    return {"veri": [dict(row._mapping) for row in veri]}


@router.get("/skt")
def skt_raporu(
    gun: int = Query(30, description="Kaç gün içinde SKT dolacak"),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """Son kullanma tarihi yaklaşan ürünler"""
    veri = crud.get_skt_raporu(db, gun=gun)
    crud.create_rapor_logu(db, RaporLoguCreate(
        sablon_id=None, parametreler={"tur": "skt", "gun": gun}, durum="Basarili"
    ), kullanici_id=current_user.id)
    return {"veri": [dict(row._mapping) for row in veri]}


@router.get("/abc-analiz")
def abc_analiz_raporu(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """ABC analizi: ürünleri satış değerine göre A/B/C sınıfına ayırır"""
    veri = crud.get_abc_analiz(db)
    crud.create_rapor_logu(db, RaporLoguCreate(
        sablon_id=None, parametreler={"tur": "abc"}, durum="Basarili"
    ), kullanici_id=current_user.id)
    return {"veri": veri}


@router.get("/doluluk")
def depo_doluluk_raporu(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """Depo raf doluluk oranları"""
    return {"veri": crud.get_depo_doluluk(db)}


@router.post("/export")
def rapor_export(
    sablon_id: Optional[int] = None,
    tur: str = Query("stok", description="stok | siparis | hareket | kritik_stok | skt"),
    format: str = Query("csv", description="csv | excel"),
    baslang_tarihi: Optional[date] = Query(None),
    bitis_tarihi: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Raporu CSV veya Excel olarak dışa aktar"""
    # Veriyi türe göre çek
    if tur == "stok":
        rows = crud.get_stok_raporu_verileri(db)
    elif tur == "siparis":
        rows = crud.get_siparis_raporu_verileri(db, baslang_tarihi, bitis_tarihi)
    elif tur == "hareket":
        rows = crud.get_hareket_raporu_verileri(db, baslang_tarihi, bitis_tarihi)
    elif tur == "kritik_stok":
        rows = crud.get_kritik_stok_raporu(db)
    elif tur == "skt":
        rows = crud.get_skt_raporu(db)
    else:
        raise HTTPException(status_code=400, detail=f"Geçersiz rapor türü: {tur}")

    if not rows:
        raise HTTPException(status_code=404, detail="Rapor için veri bulunamadı")

    # Rapor logu
    crud.create_rapor_logu(db, RaporLoguCreate(
        sablon_id=sablon_id,
        parametreler={"tur": tur, "format": format},
        durum="Basarili"
    ), kullanici_id=current_user.id)

    if format == "csv":
        output = io.StringIO()
        # SQLAlchemy Row'dan dict çevir
        row_dicts = [dict(r._mapping) for r in rows] if hasattr(rows[0], '_mapping') else rows
        writer = csv.DictWriter(output, fieldnames=row_dicts[0].keys())
        writer.writeheader()
        writer.writerows(row_dicts)
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8-sig")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=rapor_{tur}.csv"}
        )

    elif format == "excel":
        try:
            import openpyxl
            from openpyxl.styles import Font
        except ImportError:
            raise HTTPException(status_code=500, detail="Excel export için openpyxl paketi kurulu değil")

        row_dicts = [dict(r._mapping) for r in rows] if hasattr(rows[0], '_mapping') else rows
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = tur.capitalize()

        headers = list(row_dicts[0].keys())
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=str(header))
            cell.font = Font(bold=True)

        for row_idx, row_data in enumerate(row_dicts, 2):
            for col_idx, value in enumerate(row_data.values(), 1):
                ws.cell(row=row_idx, column=col_idx, value=str(value) if value is not None else "")

        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=rapor_{tur}.xlsx"}
        )

    raise HTTPException(status_code=400, detail="Geçersiz format. 'csv' veya 'excel' kullanın.")


@router.post("/schedule/tetikle")
def rapor_schedule_tetikle(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Belirtilen zamanlı raporu manuel olarak tetikler"""
    db_schedule = crud.get_rapor_schedule(db, schedule_id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Zamanlı rapor bulunamadı")

    db_schedule.son_calistirilma = datetime.utcnow()
    db.commit()

    # Rapor logu yaz
    crud.create_rapor_logu(db, RaporLoguCreate(
        sablon_id=db_schedule.sablon_id,
        parametreler={"periyod": db_schedule.periyod, "format": db_schedule.format, "tetikleyen": "manuel"},
        durum="Basarili"
    ), kullanici_id=current_user.id)

    return {
        "message": f"'{db_schedule.sablon_adi}' raporu tetiklendi",
        "schedule_id": schedule_id,
        "son_calistirilma": db_schedule.son_calistirilma
    }


# ========================
# RAPOR LOGLARI
# ========================

@router.get("/log", response_model=list[RaporLoguResponse])
def rapor_loglari_listele(
    skip: int = 0,
    limit: int = 100,
    sablon_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Rapor oluşturma geçmişini listeler"""
    return crud.get_rapor_loglari(db, skip=skip, limit=limit, sablon_id=sablon_id)


# ========================
# RAPOR ZAMANLAMASI
# ========================

@router.get("/schedule", response_model=list[RaporScheduleResponse])
def rapor_schedules_listele(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Zamanlı raporları listeler"""
    return crud.get_rapor_schedules(db, skip=skip, limit=limit)


@router.get("/schedule/{schedule_id}", response_model=RaporScheduleResponse)
def rapor_schedule_detay(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Zamanlı rapor detayını getirir"""
    db_schedule = crud.get_rapor_schedule(db, schedule_id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Zamanlı rapor bulunamadı")
    return db_schedule


@router.post("/schedule", response_model=RaporScheduleResponse, status_code=201)
def rapor_schedule_ekle(
    schedule: RaporScheduleCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Yeni zamanlı rapor oluşturur"""
    return crud.create_rapor_schedule(db, schedule, kullanici_id=current_user.id)


@router.put("/schedule/{schedule_id}", response_model=RaporScheduleResponse)
def rapor_schedule_guncelle(
    schedule_id: int,
    schedule_update: RaporScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Zamanlı raporu günceller"""
    db_schedule = crud.update_rapor_schedule(db, schedule_id, schedule_update, kullanici_id=current_user.id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Zamanlı rapor bulunamadı")
    return db_schedule


@router.delete("/schedule/{schedule_id}")
def rapor_schedule_sil(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Zamanlı raporu siler"""
    success = crud.delete_rapor_schedule(db, schedule_id, kullanici_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Zamanlı rapor bulunamadı")
    return {"message": "Zamanlı rapor başarıyla silindi", "id": schedule_id}
