from datetime import date

from app.core.services.uretim_seri_no_uretici import IUretimSeriNoUretici
from app.core.repositories.uretim_seri_sayac_repository import IUretimSeriSayacRepository


class SqlUretimSeriNoUretici(IUretimSeriNoUretici):
    """Transaction-güvenli seri numara üretici.

    SELECT FOR UPDATE ile atomik artış; rollback'te gap kabul edilir.
    Format: {PREFIX}-YYYYMMDD-NNNN
    """

    def __init__(self, sayac_repo: IUretimSeriSayacRepository):
        self._sayac_repo = sayac_repo

    def uret(self, tarih: date, prefix: str = "PRD") -> str:
        seri_no = self._sayac_repo.artir_ve_dondur(tarih, prefix)
        return f"{prefix}-{tarih.strftime('%Y%m%d')}-{seri_no:04d}"
