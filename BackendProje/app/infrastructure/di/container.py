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
    uretim_di           — Üretim Paleti (FAZ 3)
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
    get_raf_oneri_sorgula_uc,
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
    get_toplama_gorevi_repo,
    get_rezervasyon_repo,
    get_stok_cikis_service,
    get_fefo_servisi,
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
    get_yukleme_onayla_uc,
    get_mal_kabul_irsaliye_listele_uc,
    get_mal_kabul_irsaliye_getir_uc,
    get_mal_kabul_irsaliye_olustur_uc,
    get_mal_kabul_irsaliye_guncelle_uc,
    get_mal_kabul_irsaliye_sil_uc,
    get_irsaliye_onayla_ve_gorev_olustur_uc,
    get_mal_kabul_kalemi_istisna_bildir_uc,
    get_inbound_dashboard_uc,
    get_inbound_kpi_uc,
    # Palet Rezervasyonu
    get_rezervasyon_baslat_uc,
    get_rezervasyon_iptal_uc,
    get_rezervasyon_kesinlestir_uc,
    get_rezervasyon_degistir_uc,
    get_rezervasyon_listele_uc,
    get_siparis_rezervasyonlari_uc,
    get_stok_detay_uc,
    # Toplama Görevi
    get_toplama_gorevi_listele_uc,
    get_toplama_gorevi_getir_uc,
    get_pick_task_uret_uc,
    get_siradan_gorev_al_uc,
    get_gorev_baslat_uc,
    get_gorev_tamamla_uc,
    get_gorev_iptal_uc,
    get_fefo_override_uc,
)

from app.infrastructure.di.modules.uretim_di import (  # noqa: F401
    get_uretim_seri_sayac_repo,
    get_palet_durum_log_repo,
    get_uretim_seri_no_uretici,
    get_uretim_palet_service,
    get_uretim_paleti_olustur_uc,
    get_uretim_paleti_kabul_bekle_uc,
    get_uretim_paleti_kabul_et_uc,
    get_uretim_paleti_karantina_al_uc,
    get_uretim_paleti_karantina_cikar_uc,
    get_uretim_paleti_iptal_uc,
    get_uretim_paleti_yerlestirme_bekle_uc,
    get_uretim_paleti_yerlestir_uc,
    get_uretim_paletleri_listele_uc,
    get_uretim_paleti_getir_uc,
)

from app.infrastructure.di.modules.etiket_di import (  # noqa: F401
    get_etiket_sablonu_repo,
    get_palet_etiket_repo,
    get_etiket_render_service,
    get_etiket_sablonlari_listele_uc,
    get_etiket_sablonu_getir_uc,
    get_etiket_sablonu_olustur_uc,
    get_etiket_sablonu_guncelle_uc,
    get_etiket_sablonu_sil_uc,
    get_palet_etiket_olustur_uc,
    get_palet_etiketleri_listele_uc,
    get_palet_etiket_yazdir_uc,
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

from app.infrastructure.di.modules.talep_tahmini_di import (  # noqa: F401
    get_talep_tahmini_repo,
    get_talep_tahmin_cache_repo,
    get_talep_tahmin_urunleri_listele_uc,
    get_talep_tahmini_getir_uc,
    get_talep_tahmin_predictor,
    get_talep_tahmin_predict_uc,
    get_riskli_urunler_listele_uc,
    get_backtest_ozet_getir_uc,
    get_parquet_backtest_uc,
    get_talep_tahmin_parquet_dir,
)

from app.infrastructure.di.modules.operator_performans_di import (  # noqa: F401
    get_gorev_performans_event_repo,
    get_operator_vardiya_metrikleri_repo,
    get_performans_event_publisher,
    get_operator_kpi_service,
    get_metrikler_aggregasyon_uc,
    get_operator_performans_sorgu_uc,
)
from app.infrastructure.di.modules.messaging_di import (  # noqa: F401
    get_rabbitmq_topology,
    get_rabbitmq_connection_factory,
    get_rabbitmq_performans_publisher,
    get_rabbitmq_outbox_relay_uc,
)
from app.infrastructure.di.modules.belge_taslagi import (  # noqa: F401
    get_belge_taslagi_repo,
    get_belge_taslagi_inceleme_kuyrugu_uc,
    get_belge_taslagi_listele_uc,
    get_belge_taslagi_getir_uc,
    get_belge_taslagi_olustur_uc,
    get_belge_taslagi_onayla_uc,
    get_belge_taslagi_reddet_uc,
    get_doc_ai_client,
)
from app.infrastructure.di.modules.asistan import (  # noqa: F401
    get_asistan_aksiyon_taslagi_repo,
    get_asistan_chat_proxy_uc,
    get_asistan_taslak_listele_uc,
    get_asistan_taslak_onayla_uc,
    get_asistan_taslak_reddet_uc,
    get_asistan_tool_registry,
    get_assistant_ai_client,
)
from app.infrastructure.di.modules.agv_di import (  # noqa: F401
    AGV_KULLANICI_ADI,
    get_agv_dispatcher,
    get_agv_kullanici_id,
    get_agv_yerlestirme_tamamla_uc,
    reset_agv_dispatcher_cache,
)
