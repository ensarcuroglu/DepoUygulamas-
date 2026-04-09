"""
Dependency Injection Container — FastAPI Depends tabanlı re-export hub.

Tüm factory fonksiyonları app/infrastructure/di/modules/ altındaki
domain-odaklı modüllerde tanımlanmıştır. Bu dosya yalnızca geriye
dönük uyumluluk için tüm factory'leri tek noktadan re-export eder;
router import'ları değişmez.

    from app.infrastructure.di.container import get_urun_listele_uc

Modül grupları:
    urun_di            — Ürün
    stok_di            — Stok Hareketi, Stok Sayım
    katalog_di         — Marka, Kategori, Tedarikçi
    depo_envanter_di   — Depo, Raf, Lot, Palet, Palet Bazlı Stok
    kullanici_destek_di — Kullanıcı, Destek Talebi, Sistem Log
    siparis_lojistik_di — Sipariş, İrsaliye, Sevkiyat, Mal Kabul, Stok Çıkış, İrsaliye Onay+Görev
    rapor_dashboard_di  — Rapor, Dashboard
"""

from app.infrastructure.di.modules.kullanici_destek_di import (  # noqa: F401
    get_kullanici_repo,
    get_destek_repo,
    get_log_repo,
    get_kullanici_listele_uc,
    get_kullanici_getir_uc,
    get_kullanici_guncelle_uc,
    get_kullanici_sil_uc,
    get_destek_listele_uc,
    get_destek_getir_uc,
    get_destek_olustur_uc,
    get_destek_guncelle_uc,
    get_sistem_log_listele_uc,
    get_sistem_log_olustur_uc,
)

from app.infrastructure.di.modules.urun_di import (  # noqa: F401
    get_urun_repo,
    get_urun_listele_uc,
    get_urun_getir_uc,
    get_kritik_urunler_uc,
    get_urun_olustur_uc,
    get_urun_guncelle_uc,
    get_urun_sil_uc,
)

from app.infrastructure.di.modules.katalog_di import (  # noqa: F401
    get_marka_repo,
    get_kategori_repo,
    get_tedarikci_repo,
    get_marka_listele_uc,
    get_marka_getir_uc,
    get_marka_olustur_uc,
    get_marka_guncelle_uc,
    get_marka_sil_uc,
    get_kategori_listele_uc,
    get_kategori_getir_uc,
    get_kategori_olustur_uc,
    get_kategori_guncelle_uc,
    get_kategori_sil_uc,
    get_tedarikci_listele_uc,
    get_tedarikci_getir_uc,
    get_tedarikci_olustur_uc,
    get_tedarikci_guncelle_uc,
    get_tedarikci_sil_uc,
)

from app.infrastructure.di.modules.depo_envanter_di import (  # noqa: F401
    get_depo_repo,
    get_zon_repo,
    get_raf_repo,
    get_lot_repo,
    get_palet_repo,
    get_hareket_repo,
    get_mal_kabul_irsaliye_repo,
    get_depo_listele_uc,
    get_depo_getir_uc,
    get_depo_olustur_uc,
    get_depo_guncelle_uc,
    get_depo_sil_uc,
    get_zon_listele_uc,
    get_zon_getir_uc,
    get_zon_olustur_uc,
    get_zon_guncelle_uc,
    get_zon_sil_uc,
    get_raf_listele_uc,
    get_raf_getir_uc,
    get_raf_olustur_uc,
    get_raf_guncelle_uc,
    get_raf_sil_uc,
    get_lot_listele_uc,
    get_lot_getir_uc,
    get_lot_skt_yaklasan_uc,
    get_lot_olustur_uc,
    get_lot_guncelle_uc,
    get_lot_sil_uc,
    get_palet_listele_uc,
    get_palet_getir_uc,
    get_palet_barkod_ile_getir_uc,
    get_palet_sonraki_numara_uc,
    get_palet_olustur_uc,
    get_palet_guncelle_uc,
    get_palet_sil_uc,
    get_palet_veri_kaynagi,
    get_palet_bazli_stok_service,
    get_palet_sorgulama_service,
    get_yerlestirme_gorevi_repo,
    get_yerlestirme_gorevi_listele_uc,
    get_yerlestirme_gorevi_getir_uc,
    get_yerlestirme_gorevi_olustur_uc,
    get_sonraki_gorevini_al_uc,
    get_yerlestirme_gorevi_baslat_uc,
    get_yerlestirme_gorevi_tamamla_uc,
    get_yerlestirme_gorevi_override_uc,
    get_yerlestirme_gorevi_iptal_uc,
    get_yerlestirme_gorevi_birak_uc,
    get_yerlestirme_gorevi_bekleyen_ozet_uc,
    get_zaman_asimi_birak_uc,
    get_zon_uyumluluk_servisi,
    get_kapasite_dogrulama_servisi,
    get_yerlestirme_algoritmasi,
    get_yerlestirme_onayla_uc,
    get_bilinmeyen_konum_gorevleri_olustur_uc,
    get_karantinadan_cikar_uc,
    get_karantinaya_al_uc,
)

from app.infrastructure.di.modules.stok_di import (  # noqa: F401
    get_stok_sayim_repo,
    get_stok_hareketi_listele_uc,
    get_stok_hareketi_olustur_uc,
    get_stok_sayim_listele_uc,
    get_stok_sayim_getir_uc,
    get_stok_sayim_baslat_uc,
    get_stok_sayim_kalem_kaydet_uc,
    get_stok_sayim_varyans_uc,
    get_stok_sayim_bitir_uc,
    get_stok_sayim_onayla_uc,
)

from app.infrastructure.di.modules.siparis_lojistik_di import (  # noqa: F401
    get_siparis_repo,
    get_irsaliye_repo,
    get_sevkiyat_repo,
    get_stok_cikis_service,
    get_siparis_listele_uc,
    get_siparis_getir_uc,
    get_siparis_olustur_uc,
    get_siparis_guncelle_uc,
    get_siparis_sil_uc,
    get_irsaliye_listele_uc,
    get_irsaliye_getir_uc,
    get_irsaliye_olustur_uc,
    get_irsaliye_guncelle_uc,
    get_irsaliye_yazdir_uc,
    get_sevkiyat_listele_uc,
    get_sevkiyat_getir_uc,
    get_sevkiyat_olustur_uc,
    get_sevkiyat_guncelle_uc,
    get_sevkiyat_sil_uc,
    get_mal_kabul_irsaliye_listele_uc,
    get_mal_kabul_irsaliye_getir_uc,
    get_mal_kabul_irsaliye_olustur_uc,
    get_mal_kabul_irsaliye_guncelle_uc,
    get_mal_kabul_irsaliye_sil_uc,
    get_irsaliye_onayla_ve_gorev_olustur_uc,
    get_mal_kabul_kalemi_istisna_bildir_uc,
)

from app.infrastructure.di.modules.rapor_dashboard_di import (  # noqa: F401
    get_rapor_sablon_repo,
    get_rapor_log_repo,
    get_rapor_schedule_repo,
    get_rapor_veri_repo,
    get_dashboard_repo,
    get_rapor_sablon_listele_uc,
    get_rapor_sablon_getir_uc,
    get_rapor_sablon_olustur_uc,
    get_rapor_sablon_guncelle_uc,
    get_rapor_sablon_sil_uc,
    get_rapor_logu_listele_uc,
    get_rapor_logu_yaz_uc,
    get_rapor_schedule_listele_uc,
    get_rapor_schedule_getir_uc,
    get_rapor_schedule_olustur_uc,
    get_rapor_schedule_guncelle_uc,
    get_rapor_schedule_sil_uc,
    get_rapor_schedule_tetikle_uc,
    get_rapor_veri_sorgula_uc,
    get_rapor_export_uc,
    get_dashboard_istatistik_uc,
)
