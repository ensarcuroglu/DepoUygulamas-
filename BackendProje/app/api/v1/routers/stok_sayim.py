"""Stok Sayım — Clean Architecture Router (thin controller)."""

from fastapi import APIRouter, Depends
from typing import List

from models import Kullanici
from app.core.auth import get_current_user, require_role
from app.infrastructure.di.container import (
    get_stok_sayim_listele_uc,
    get_stok_sayim_getir_uc,
    get_stok_sayim_baslat_uc,
    get_stok_sayim_kalem_kaydet_uc,
    get_stok_sayim_varyans_uc,
    get_stok_sayim_onayla_uc,
)
from app.application.dto.stok_sayim_dto import (
    StokSayimOlusturRequestDTO,
    StokSayimKalemiKaydetRequestDTO,
    StokSayimResponseDTO,
    StokSayimKalemiResponseDTO,
    VaryansResponseDTO,
)

router = APIRouter(prefix="/api/stok-sayimlar", tags=["stok-sayim"])


@router.get("", response_model=List[StokSayimResponseDTO])
def sayimlari_listele(
    uc=Depends(get_stok_sayim_listele_uc),
    current_user: Kullanici = Depends(get_current_user),
):
    return uc.execute()


@router.get("/{sayim_id}", response_model=StokSayimResponseDTO)
def sayim_detayi(
    sayim_id: int,
    uc=Depends(get_stok_sayim_getir_uc),
    current_user: Kullanici = Depends(get_current_user),
):
    return uc.execute(sayim_id)


@router.post("", response_model=StokSayimResponseDTO, status_code=201)
def sayim_basla(
    sayim_data: StokSayimOlusturRequestDTO,
    uc=Depends(get_stok_sayim_baslat_uc),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return uc.execute(sayim_data, kullanici_id=current_user.id)


@router.post("/{sayim_id}/kalemler", response_model=StokSayimKalemiResponseDTO)
def urun_sayisi_kaydet(
    sayim_id: int,
    kalem_data: StokSayimKalemiKaydetRequestDTO,
    uc=Depends(get_stok_sayim_kalem_kaydet_uc),
    current_user: Kullanici = Depends(get_current_user),
):
    return uc.execute(sayim_id, kalem_data, kullanici_id=current_user.id)


@router.get("/{sayim_id}/varyans", response_model=VaryansResponseDTO)
def varyans_hesapla(
    sayim_id: int,
    uc=Depends(get_stok_sayim_varyans_uc),
    current_user: Kullanici = Depends(get_current_user),
):
    return uc.execute(sayim_id)


@router.post("/{sayim_id}/onayla")
def sayimi_onayla(
    sayim_id: int,
    uc=Depends(get_stok_sayim_onayla_uc),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return uc.execute(sayim_id, kullanici_id=current_user.id)
