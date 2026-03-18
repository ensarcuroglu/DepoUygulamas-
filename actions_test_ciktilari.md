Run pytest --cov=. --cov-report=term-missing -v
  
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.2, pluggy-1.6.0 -- /opt/hostedtoolcache/Python/3.11.15/x64/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/DepoUygulamas-/DepoUygulamas-/BackendProje
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.12.1, cov-7.0.0, Faker-40.11.0
collecting ... collected 178 items
tests/api/routers/test_auth_api.py::TestLoginEndpoint::test_basarili_login PASSED [  0%]
tests/api/routers/test_auth_api.py::TestLoginEndpoint::test_yanlis_sifre PASSED [  1%]
tests/api/routers/test_auth_api.py::TestLoginEndpoint::test_olmayan_kullanici PASSED [  1%]
tests/api/routers/test_auth_api.py::TestMeEndpoint::test_yetkili_erisim PASSED [  2%]
tests/api/routers/test_auth_api.py::TestMeEndpoint::test_yetkisiz_erisim PASSED [  2%]
tests/api/routers/test_auth_api.py::TestRegisterEndpoint::test_admin_kayit_olustur PASSED [  3%]
tests/api/routers/test_auth_api.py::TestRegisterEndpoint::test_depocu_kayit_olusturamaz PASSED [  3%]
tests/api/routers/test_auth_api.py::TestRegisterEndpoint::test_tekrar_eden_kullanici_adi PASSED [  4%]
tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_marka_listele PASSED [  5%]
tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_marka_olustur PASSED [  5%]
tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_yetkisiz_erisim PASSED [  6%]
tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_depocu_erisim PASSED [  6%]
tests/api/routers/test_urunler_api.py::TestUrunListele::test_yetkisiz_erisim PASSED [  7%]
tests/api/routers/test_urunler_api.py::TestUrunListele::test_bos_liste PASSED [  7%]
tests/api/routers/test_urunler_api.py::TestUrunListele::test_urun_listeleme PASSED [  8%]
tests/api/routers/test_urunler_api.py::TestUrunListele::test_arama_filtresi PASSED [  8%]
tests/api/routers/test_urunler_api.py::TestUrunOlustur::test_basarili_olusturma PASSED [  9%]
tests/api/routers/test_urunler_api.py::TestUrunOlustur::test_gecersiz_barkod PASSED [ 10%]
tests/api/routers/test_urunler_api.py::TestUrunGetir::test_basarili_getir PASSED [ 10%]
tests/api/routers/test_urunler_api.py::TestUrunGetir::test_olmayan_urun PASSED [ 11%]
tests/integration/crud/test_depo_crud.py::TestDepoCrud::test_create_depo PASSED [ 11%]
tests/integration/crud/test_depo_crud.py::TestDepoCrud::test_create_depo_sistem_log PASSED [ 12%]
tests/integration/crud/test_depo_crud.py::TestDepoCrud::test_get_depolar PASSED [ 12%]
tests/integration/crud/test_depo_crud.py::TestDepoCrud::test_get_depolar_dahil_pasif PASSED [ 13%]
tests/integration/crud/test_depo_crud.py::TestDepoCrud::test_get_depo_by_id PASSED [ 14%]
tests/integration/crud/test_depo_crud.py::TestDepoCrud::test_get_depo_bulunamadi PASSED [ 14%]
tests/integration/crud/test_depo_crud.py::TestDepoCrud::test_update_depo PASSED [ 15%]
tests/integration/crud/test_depo_crud.py::TestDepoCrud::test_update_depo_bulunamadi PASSED [ 15%]
tests/integration/crud/test_depo_crud.py::TestDepoCrud::test_delete_depo_soft PASSED [ 16%]
tests/integration/crud/test_depo_crud.py::TestDepoCrud::test_delete_depo_bulunamadi PASSED [ 16%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_generate_irsaliye_no_ilk PASSED [ 17%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_generate_irsaliye_no_ardisik PASSED [ 17%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_create_irsaliye_basit PASSED [ 18%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_create_irsaliye_stok_cikisi PASSED [ 19%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_create_irsaliye_sevkiyat_varsa_stok_cikisi_yapilmaz PASSED [ 19%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_create_irsaliye_sistem_log PASSED [ 20%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_get_irsaliyeler PASSED [ 20%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_get_irsaliyeler_durum_filtre PASSED [ 21%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_get_irsaliye_by_id PASSED [ 21%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_get_irsaliye_bulunamadi PASSED [ 22%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_update_irsaliye_durum PASSED [ 23%]
tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_update_irsaliye_bulunamadi FAILED [ 23%]
tests/integration/crud/test_kategori_crud.py::TestKategoriCrud::test_create_kategori PASSED [ 24%]
tests/integration/crud/test_kategori_crud.py::TestKategoriCrud::test_create_kategori_sistem_log PASSED [ 24%]
tests/integration/crud/test_kategori_crud.py::TestKategoriCrud::test_get_kategoriler PASSED [ 25%]
tests/integration/crud/test_kategori_crud.py::TestKategoriCrud::test_get_kategoriler_dahil_pasif PASSED [ 25%]
tests/integration/crud/test_kategori_crud.py::TestKategoriCrud::test_get_kategori_by_id PASSED [ 26%]
tests/integration/crud/test_kategori_crud.py::TestKategoriCrud::test_get_kategori_bulunamadi PASSED [ 26%]
tests/integration/crud/test_kategori_crud.py::TestKategoriCrud::test_update_kategori PASSED [ 27%]
tests/integration/crud/test_kategori_crud.py::TestKategoriCrud::test_update_kategori_bulunamadi PASSED [ 28%]
tests/integration/crud/test_kategori_crud.py::TestKategoriCrud::test_delete_kategori_soft PASSED [ 28%]
tests/integration/crud/test_kategori_crud.py::TestKategoriCrud::test_delete_kategori_bulunamadi PASSED [ 29%]
tests/integration/crud/test_rapor_crud.py::TestRaporSablonuCrud::test_create_rapor_sablonu PASSED [ 29%]
tests/integration/crud/test_rapor_crud.py::TestRaporSablonuCrud::test_get_rapor_sablonlari PASSED [ 30%]
tests/integration/crud/test_rapor_crud.py::TestRaporSablonuCrud::test_get_rapor_sablonlari_tur_filtre PASSED [ 30%]
tests/integration/crud/test_rapor_crud.py::TestRaporSablonuCrud::test_get_rapor_sablonu_by_id PASSED [ 31%]
tests/integration/crud/test_rapor_crud.py::TestRaporSablonuCrud::test_update_rapor_sablonu PASSED [ 32%]
tests/integration/crud/test_rapor_crud.py::TestRaporSablonuCrud::test_update_rapor_sablonu_bulunamadi PASSED [ 32%]
tests/integration/crud/test_rapor_crud.py::TestRaporSablonuCrud::test_delete_rapor_sablonu_soft PASSED [ 33%]
tests/integration/crud/test_rapor_crud.py::TestRaporSablonuCrud::test_delete_rapor_sablonu_bulunamadi PASSED [ 33%]
tests/integration/crud/test_rapor_crud.py::TestRaporLoguCrud::test_create_rapor_logu PASSED [ 34%]
tests/integration/crud/test_rapor_crud.py::TestRaporLoguCrud::test_get_rapor_loglari PASSED [ 34%]
tests/integration/crud/test_rapor_crud.py::TestRaporLoguCrud::test_get_rapor_loglari_sablon_filtre PASSED [ 35%]
tests/integration/crud/test_rapor_crud.py::TestRaporScheduleCrud::test_create_rapor_schedule PASSED [ 35%]
tests/integration/crud/test_rapor_crud.py::TestRaporScheduleCrud::test_get_rapor_schedules PASSED [ 36%]
tests/integration/crud/test_rapor_crud.py::TestRaporScheduleCrud::test_update_rapor_schedule PASSED [ 37%]
tests/integration/crud/test_rapor_crud.py::TestRaporScheduleCrud::test_update_rapor_schedule_bulunamadi PASSED [ 37%]
tests/integration/crud/test_rapor_crud.py::TestRaporScheduleCrud::test_delete_rapor_schedule PASSED [ 38%]
tests/integration/crud/test_rapor_crud.py::TestRaporScheduleCrud::test_delete_rapor_schedule_bulunamadi PASSED [ 38%]
tests/integration/crud/test_rapor_crud.py::TestRaporVerileri::test_get_stok_raporu_verileri PASSED [ 39%]
tests/integration/crud/test_rapor_crud.py::TestRaporVerileri::test_get_stok_raporu_urun_filtre PASSED [ 39%]
tests/integration/crud/test_rapor_crud.py::TestRaporVerileri::test_get_kritik_stok_raporu PASSED [ 40%]
tests/integration/crud/test_rapor_crud.py::TestRaporVerileri::test_get_depo_doluluk PASSED [ 41%]
tests/integration/crud/test_rapor_crud.py::TestRaporVerileri::test_get_depo_doluluk_bos_raf PASSED [ 41%]
tests/integration/crud/test_rapor_crud.py::TestRaporVerileri::test_get_abc_analiz FAILED [ 42%]
tests/integration/crud/test_rapor_crud.py::TestRaporVerileri::test_get_abc_analiz_bos PASSED [ 42%]
tests/integration/crud/test_rapor_crud.py::TestRaporVerileri::test_get_skt_raporu PASSED [ 43%]
tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_create_sevkiyat_plani PASSED [ 43%]
tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_create_sevkiyat_sistem_log PASSED [ 44%]
tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_get_sevkiyat_planlari PASSED [ 44%]
tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_get_sevkiyat_planlari_durum_filtre PASSED [ 45%]
tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_get_sevkiyat_plani_by_id PASSED [ 46%]
tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_get_sevkiyat_plani_bulunamadi PASSED [ 46%]
tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_update_sevkiyat_plani_basit PASSED [ 47%]
tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_update_sevkiyat_yukleniyor_fifo_stok_cikis PASSED [ 47%]
tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_update_sevkiyat_bulunamadi FAILED [ 48%]
tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_delete_sevkiyat_plani PASSED [ 48%]
tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_delete_sevkiyat_bulunamadi PASSED [ 49%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_generate_siparis_no_ilk PASSED [ 50%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_generate_siparis_no_ardisik PASSED [ 50%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_create_siparis_tek_kalem PASSED [ 51%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_create_siparis_cok_kalem PASSED [ 51%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_create_siparis_sistem_log PASSED [ 52%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_get_siparisler PASSED [ 52%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_get_siparisler_durum_filtre PASSED [ 53%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_get_siparisler_arama PASSED [ 53%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_get_siparis_by_id PASSED [ 54%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_get_siparis_bulunamadi PASSED [ 55%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_update_siparis_durum PASSED [ 55%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_update_siparis_bulunamadi PASSED [ 56%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_delete_siparis_soft PASSED [ 56%]
tests/integration/crud/test_siparis_crud.py::TestSiparisCrud::test_delete_siparis_bulunamadi PASSED [ 57%]
tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_create_stok_giris PASSED [ 57%]
tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_create_stok_cikis_fifo PASSED [ 58%]
tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_get_stok_hareketleri_filtre PASSED [ 58%]
tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_get_stok_hareketleri_urun_filtre PASSED [ 59%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_create_urun PASSED [ 60%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_urun_by_id PASSED [ 60%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_urun_by_id_bulunamadi PASSED [ 61%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_urun_by_barkod PASSED [ 61%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_urunler_search PASSED [ 62%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_urunler_kategori_filtre PASSED [ 62%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_update_urun PASSED [ 63%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_delete_urun_soft_delete PASSED [ 64%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_kritik_urunler PASSED [ 64%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_get_kullanicilar PASSED [ 65%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_get_kullanici PASSED [ 65%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_get_kullanici_bulunamadi PASSED [ 66%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_update_kullanici_kendi_hesabi PASSED [ 66%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_update_kullanici_admin_baskasini_guncelleyebilir PASSED [ 67%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_update_kullanici_yetkisiz PASSED [ 67%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_update_kullanici_duplicate_username PASSED [ 68%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_update_kullanici_rol_degistirme_admin PASSED [ 69%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_update_kullanici_rol_degistirme_yetkisiz PASSED [ 69%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_update_kullanici_sifre PASSED [ 70%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_delete_kullanici PASSED [ 70%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_delete_kullanici_kendini_silemez PASSED [ 71%]
tests/integration/services/test_kullanici_service.py::TestKullaniciService::test_delete_kullanici_bulunamadi PASSED [ 71%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_basla PASSED [ 72%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_basla_bos_stok PASSED [ 73%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_kalem_kaydet_yeni PASSED [ 73%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_kalem_kaydet_upsert PASSED [ 74%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_kalem_kaydet_sayim_bulunamadi PASSED [ 74%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_kalem_kaydet_sayim_kapali PASSED [ 75%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_kalem_kaydet_urun_bulunamadi PASSED [ 75%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_varyans_hesapla_sapma_var PASSED [ 76%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_varyans_hesapla_sapma_yok PASSED [ 76%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_varyans_hesapla_sayim_bulunamadi PASSED [ 77%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_onayla PASSED [ 78%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_onayla_zaten_onayli PASSED [ 78%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_onayla_sayim_bulunamadi PASSED [ 79%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_get_sayimlar PASSED [ 79%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_get_sayim PASSED [ 80%]
tests/integration/services/test_stok_sayim_service.py::TestStokSayimService::test_get_sayim_bulunamadi PASSED [ 80%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_gecerli_urun PASSED [ 81%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_barkod_format_hatasi PASSED [ 82%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_ean_format_hatasi PASSED [ 82%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_gecerli_ean PASSED [ 83%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_fiyat_negatif_olamaz PASSED [ 83%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_ic_adet_sifir_olamaz PASSED [ 84%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_gecersiz_birim PASSED [ 84%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_gecerli_birimler PASSED [ 85%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_gecerli_kullanici PASSED [ 85%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_sifre_cok_kisa PASSED [ 86%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_sifre_buyuk_harf_yok PASSED [ 87%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_sifre_kucuk_harf_yok PASSED [ 87%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_sifre_rakam_yok PASSED [ 88%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_gecersiz_rol PASSED [ 88%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_gecerli_roller PASSED [ 89%]
tests/unit/entities/test_schemas.py::TestPaletCreateSchema::test_koli_adedi_pozitif_olmali PASSED [ 89%]
tests/unit/entities/test_schemas.py::TestPaletCreateSchema::test_koli_adedi_negatif_olamaz PASSED [ 90%]
tests/unit/entities/test_schemas.py::TestPaletCreateSchema::test_gecerli_palet PASSED [ 91%]
tests/unit/entities/test_schemas.py::TestRafBaseSchema::test_kapasite_pozitif_olmali PASSED [ 91%]
tests/unit/entities/test_schemas.py::TestRafBaseSchema::test_gecerli_raf PASSED [ 92%]
tests/unit/entities/test_schemas.py::TestStokHareketiSchema::test_gecerli_giris PASSED [ 92%]
tests/unit/entities/test_schemas.py::TestStokHareketiSchema::test_gecerli_cikis PASSED [ 93%]
tests/unit/entities/test_schemas.py::TestStokHareketiSchema::test_gecersiz_hareket_tipi PASSED [ 93%]
tests/unit/entities/test_schemas.py::TestLoginRequestSchema::test_kullanici_adi_cok_kisa PASSED [ 94%]
tests/unit/entities/test_schemas.py::TestLoginRequestSchema::test_gecerli_login PASSED [ 94%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunOlusturUseCase::test_basarili_olusturma PASSED [ 95%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunOlusturUseCase::test_barkod_cakismasi PASSED [ 96%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunGetirUseCase::test_basarili_getir PASSED [ 96%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunGetirUseCase::test_bulunamadi PASSED [ 97%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunGetirUseCase::test_barkod_ile_getir PASSED [ 97%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunListeleUseCase::test_bos_liste PASSED [ 98%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunListeleUseCase::test_filtreli_listeleme PASSED [ 98%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunSilUseCase::test_basarili_silme PASSED [ 99%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunSilUseCase::test_olmayan_urun_silme PASSED [100%]
=================================== FAILURES ===================================
_______________ TestIrsaliyeCrud.test_update_irsaliye_bulunamadi _______________
self = <tests.integration.crud.test_irsaliye_crud.TestIrsaliyeCrud object at 0x7fb65661b4d0>
db_session = <sqlalchemy.orm.session.Session object at 0x7fb657fc8350>
    def test_update_irsaliye_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
>       dto = IrsaliyeUpdate(durum="X")
              ^^^^^^^^^^^^^^^^^^^^^^^^^
E       pydantic_core._pydantic_core.ValidationError: 1 validation error for IrsaliyeUpdate
E       durum
E         Input should be 'Taslak', 'Kesildi' or 'Gonderildi' [type=literal_error, input_value='X', input_type=str]
E           For further information visit https://errors.pydantic.dev/2.12/v/literal_error
tests/integration/crud/test_irsaliye_crud.py:162: ValidationError
____________________ TestRaporVerileri.test_get_abc_analiz _____________________
self = <tests.integration.crud.test_rapor_crud.TestRaporVerileri object at 0x7fb6565945d0>
db_session = <sqlalchemy.orm.session.Session object at 0x7fb657d0cf10>
    def test_get_abc_analiz(self, db_session):
        """ABC analizi: yüksek değerli ürün A, düşük değerli C olmalı."""
        urun_a = UrunFactory.create(isim="Pahali Urun")
        urun_c = UrunFactory.create(isim="Ucuz Urun")
    
        siparis = SiparisFactory.create(durum="Bekleme")
        SiparisKalemiFactory.create(siparis=siparis, urun=urun_a, miktar=100, birim_fiyat=1000.0, toplam=100000.0)
        SiparisKalemiFactory.create(siparis=siparis, urun=urun_c, miktar=1, birim_fiyat=10.0, toplam=10.0)
    
        result = get_abc_analiz(db_session)
    
        assert len(result) == 2
        siniflar = {r["urun_isim"]: r["sinif"] for r in result}
>       assert siniflar["Pahali Urun"] == "A"
E       AssertionError: assert 'C' == 'A'
E         
E         - A
E         + C
tests/integration/crud/test_rapor_crud.py:301: AssertionError
_______________ TestSevkiyatCrud.test_update_sevkiyat_bulunamadi _______________
self = <tests.integration.crud.test_sevkiyat_crud.TestSevkiyatCrud object at 0x7fb65650c290>
db_session = <sqlalchemy.orm.session.Session object at 0x7fb657d478d0>
    def test_update_sevkiyat_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
>       dto = SevkiyatPlaniUpdate(durum="Yolda")
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       pydantic_core._pydantic_core.ValidationError: 1 validation error for SevkiyatPlaniUpdate
E       durum
E         Input should be 'Planlandi', 'Yukleniyor', 'Tamamlandi' or 'Iptal' [type=literal_error, input_value='Yolda', input_type=str]
E           For further information visit https://errors.pydantic.dev/2.12/v/literal_error
tests/integration/crud/test_sevkiyat_crud.py:134: ValidationError
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.11.15-final-0 _______________
Name                                                                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------------------------------------------
app/__init__.py                                                                   0      0   100%
app/api/__init__.py                                                               0      0   100%
app/api/v1/__init__.py                                                            0      0   100%
app/api/v1/routers/__init__.py                                                    4      0   100%
app/api/v1/routers/siparisler.py                                                 24      6    75%   54, 64, 74, 85, 95-96
app/api/v1/routers/stok_hareketleri.py                                           17      2    88%   50, 70
app/api/v1/routers/urunler.py                                                    38      5    87%   74, 86, 123, 135-136
app/application/__init__.py                                                       0      0   100%
app/application/dto/__init__.py                                                   4      0   100%
app/application/dto/siparis_dto.py                                               89     22    75%   25, 42-44, 49-51, 56-62, 81-86, 108, 140, 164-166
app/application/dto/stok_hareketi_dto.py                                         54     10    81%   46-50, 55-60, 97
app/application/dto/urun_dto.py                                                 108     10    91%   38, 46, 70-72, 77-81
app/application/use_cases/__init__.py                                             4      0   100%
app/application/use_cases/siparis_use_cases.py                                   83     57    31%   40, 49-52, 62, 65-68, 91-92, 100-133, 137-144, 166-167, 176-218, 240-241, 244-255
app/application/use_cases/stok_hareketi_use_cases.py                             70     45    36%   47, 57-63, 99-104, 113-157, 167-180, 186-211
app/application/use_cases/urun_use_cases.py                                      77     21    73%   75, 87, 90-91, 174-175, 184-218
app/core/__init__.py                                                              0      0   100%
app/core/entities/__init__.py                                                    18      0   100%
app/core/entities/depo.py                                                        16      2    88%   21, 24
app/core/entities/destek_talebi.py                                               35      8    77%   38-40, 44-47, 50
app/core/entities/irsaliye.py                                                    36      9    75%   38-41, 45-48, 52
app/core/entities/kategori.py                                                    19      5    74%   20, 23, 26-28
app/core/entities/kullanici.py                                                   33      5    85%   41, 45, 48-50
app/core/entities/lot.py                                                         30     11    63%   25, 29, 33-36, 40-44
app/core/entities/marka.py                                                       19      5    74%   21, 25, 28-30
app/core/entities/palet.py                                                       33     13    61%   30-40, 44-45, 48, 52
app/core/entities/raf.py                                                         19      3    84%   22, 25, 29
app/core/entities/rapor.py                                                       67     11    84%   41-42, 59-61, 64-65, 85-86, 89-90
app/core/entities/sevkiyat_plani.py                                              43     13    70%   22, 47-58, 61-66, 69
app/core/entities/siparis.py                                                     59     15    75%   25, 42-43, 70-75, 79, 83-85, 89-91, 94
app/core/entities/sistem_log.py                                                  21      0   100%
app/core/entities/stok_hareketi.py                                               34      8    76%   34, 37, 41-46
app/core/entities/stok_sayim.py                                                  56     16    71%   22, 39, 64-66, 70-73, 77-80, 83-85
app/core/entities/tedarikci.py                                                   19      2    89%   24, 27
app/core/entities/urun.py                                                        49     12    76%   48-50, 55, 58-61, 64-65, 69, 73
app/core/exceptions/__init__.py                                                   3      0   100%
app/core/repositories/__init__.py                                                18      0   100%
app/core/repositories/depo_repository.py                                          4      0   100%
app/core/repositories/destek_talebi_repository.py                                 4      0   100%
app/core/repositories/irsaliye_repository.py                                      6      0   100%
app/core/repositories/kategori_repository.py                                      4      0   100%
app/core/repositories/kullanici_repository.py                                     4      0   100%
app/core/repositories/lot_repository.py                                           6      0   100%
app/core/repositories/marka_repository.py                                         6      0   100%
app/core/repositories/palet_repository.py                                        10      0   100%
app/core/repositories/raf_repository.py                                           4      0   100%
app/core/repositories/rapor_repository.py                                         6      0   100%
app/core/repositories/sevkiyat_plani_repository.py                                5      0   100%
app/core/repositories/siparis_repository.py                                       8      0   100%
app/core/repositories/sistem_log_repository.py                                    4      0   100%
app/core/repositories/stok_hareketi_repository.py                                 4      0   100%
app/core/repositories/stok_sayim_repository.py                                    6      0   100%
app/core/repositories/tedarikci_repository.py                                     4      0   100%
app/core/repositories/urun_repository.py                                          6      0   100%
app/infrastructure/__init__.py                                                    0      0   100%
app/infrastructure/di/__init__.py                                                 0      0   100%
app/infrastructure/di/container.py                                               43     14    67%   56, 60, 64, 72, 94, 108, 115, 125, 136, 148, 154, 161, 168, 175
app/infrastructure/persistence/__init__.py                                        0      0   100%
app/infrastructure/persistence/database.py                                        2      2     0%   9-11
app/infrastructure/persistence/mappers.py                                       120     54    55%   62, 72, 86, 96, 110, 121, 136, 148, 164, 178, 243, 257, 275, 290, 309, 328, 351, 369, 421, 436, 455, 467, 479-486, 505-522, 530, 548, 570, 586, 606, 620, 638, 651, 668, 684, 704, 716, 728-735, 752-765
app/infrastructure/persistence/repositories/__init__.py                          18      0   100%
app/infrastructure/persistence/repositories/sa_depo_repository.py                42     29    31%   13, 16-19, 22-23, 26-31, 34-43, 46-51
app/infrastructure/persistence/repositories/sa_destek_talebi_repository.py       41     29    29%   13, 20-30, 33-36, 39-44, 47-59
app/infrastructure/persistence/repositories/sa_irsaliye_repository.py            56     41    27%   15, 22-40, 43-46, 49-54, 57-70, 73-88
app/infrastructure/persistence/repositories/sa_kategori_repository.py            41     28    32%   13, 16-19, 22-23, 26-31, 34-42, 45-50
app/infrastructure/persistence/repositories/sa_kullanici_repository.py           50     36    28%   13, 16-17, 20-21, 24-27, 30-35, 38-54, 57-62
app/infrastructure/persistence/repositories/sa_lot_repository.py                 60     44    27%   14, 20-26, 29-33, 36-40, 43-51, 54-69, 72-77, 80-88
app/infrastructure/persistence/repositories/sa_marka_repository.py               42     29    31%   13, 16-20, 23-24, 27-32, 35-43, 46-51
app/infrastructure/persistence/repositories/sa_palet_repository.py               71     52    27%   14, 22-33, 36-40, 43-47, 50-58, 61-76, 79-84, 87-90, 94, 108-109, 112-113
app/infrastructure/persistence/repositories/sa_raf_repository.py                 45     32    29%   13, 19-24, 27-28, 31-36, 39-49, 52-57
app/infrastructure/persistence/repositories/sa_rapor_repository.py              105     81    23%   27, 33-39, 42-43, 46-51, 54-65, 68-73, 83, 89-97, 100-105, 115, 121-129, 132-135, 138-143, 146-160, 163-168
app/infrastructure/persistence/repositories/sa_sevkiyat_plani_repository.py      55     41    25%   14, 22-36, 39-42, 45-50, 53-69, 72-77
app/infrastructure/persistence/repositories/sa_siparis_repository.py             65     49    25%   17, 24-43, 46-50, 53-72, 75-89, 92-97, 100-115
app/infrastructure/persistence/repositories/sa_sistem_log_repository.py          26      8    69%   20-26, 35
app/infrastructure/persistence/repositories/sa_stok_hareketi_repository.py       27     17    37%   13, 21-33, 36-44
app/infrastructure/persistence/repositories/sa_stok_sayim_repository.py          58     44    24%   16, 19-25, 28-33, 36-41, 44-58, 61-66, 69-82
app/infrastructure/persistence/repositories/sa_tedarikci_repository.py           45     32    29%   13, 16-19, 22-23, 26-31, 34-46, 49-54
app/infrastructure/persistence/repositories/sa_urun_repository.py                67     32    52%   42, 45, 75-94, 97-104, 107-114
auth.py                                                                          83     25    70%   30, 35, 61-62, 82, 118-143, 170, 174-176, 180
core/__init__.py                                                                  3      0   100%
core/api_exceptions.py                                                           67     15    78%   31, 56-57, 83, 117, 124-128, 139-140, 151-152, 177
core/exception_handlers.py                                                       14      4    71%   47-52
core/exceptions.py                                                                2      0   100%
crud/__init__.py                                                                 15      0   100%
crud/dashboard_crud.py                                                           11      6    45%   9-23
crud/depo_crud.py                                                                35      0   100%
crud/destek_crud.py                                                              35     27    23%   9-14, 17, 20-34, 37-58
crud/irsaliye_crud.py                                                            63      7    89%   24-25, 38, 93-100, 109
crud/kategori_crud.py                                                            40      0   100%
crud/lot_crud.py                                                                 40     29    28%   9-14, 17, 23, 29-33, 36-43, 46-51, 55-56
crud/marka_crud.py                                                               32     15    53%   13, 23-30, 33-38
crud/palet_crud.py                                                               43     33    23%   9-19, 22, 28, 34-38, 41-48, 52-57, 61-64
crud/raf_crud.py                                                                 34     26    24%   7-12, 15, 18-22, 25-32, 35-40
crud/rapor_crud.py                                                              138     16    88%   124, 204-219, 223-236, 295, 304, 306
crud/sevkiyat_crud.py                                                            59      6    90%   17, 20, 47, 81-88
crud/siparis_crud.py                                                             69      2    97%   22-23
crud/stok_hareketi_crud.py                                                       65     10    85%   19, 32, 35, 53, 55-57, 63, 72, 83
crud/tedarikci_crud.py                                                           32     24    25%   7-10, 13, 16-20, 23-30, 33-38
crud/urun_crud.py                                                                57      3    95%   34, 74, 102
database.py                                                                      15      4    73%   26-30
limiter.py                                                                        3      0   100%
main.py                                                                         132     61    54%   55-86, 90-129, 134-136, 179, 225, 238
models.py                                                                       304      6    98%   135-141
routers/__init__.py                                                               0      0   100%
routers/auth.py                                                                  56      9    84%   107-111, 134-147
routers/depolar.py                                                               24      6    75%   24, 33, 42, 52, 61-62
routers/destek.py                                                                21      4    81%   23, 32, 41, 52
routers/irsaliyeler.py                                                           24      5    79%   23, 32, 41, 51, 61
routers/kategoriler.py                                                           24      6    75%   20, 29, 38, 48, 57-58
routers/kullanicilar.py                                                          20      4    80%   20, 30, 43, 53
routers/lotlar.py                                                                28      7    75%   23, 33, 43, 53, 64, 74-75
routers/markalar.py                                                              24      4    83%   29, 48, 57-58
routers/paletler.py                                                              35     11    69%   25, 34, 44-47, 57, 67, 78, 88-89
routers/raflar.py                                                                25      6    76%   20, 31, 40, 50, 59-60
routers/raporlar.py                                                             122     69    43%   34, 43, 52, 62, 71-72, 85-87, 97-103, 113-119, 127-129, 138-140, 148-150, 158, 173-227, 236, 251, 265, 274, 283, 293, 302-303
routers/sevkiyat_planlama.py                                                     26      6    77%   25, 37, 46, 56, 65-66
routers/sistem_loglari.py                                                        14      2    86%   20, 30
routers/stok_sayim.py                                                            27      6    78%   20, 29, 39, 50, 60, 70
routers/tedarikciler.py                                                          24      6    75%   20, 29, 38, 48, 57-58
schemas.py                                                                      500      3    99%   376, 378, 380
services/__init__.py                                                             14      0   100%
services/depo_service.py                                                         61     33    46%   14, 18-21, 25, 29-30, 34-35, 42, 46-49, 54-61, 65-69, 73-78
services/destek_service.py                                                       29     14    52%   22-24, 32-37, 41, 45-50
services/irsaliye_service.py                                                     34     17    50%   21, 25-28, 32-35, 39-40, 45-71
services/kategori_service.py                                                     30     13    57%   14, 18-21, 25-28, 32-33, 37-38
services/kullanici_service.py                                                    49      2    96%   48, 64
services/lot_service.py                                                          36     17    53%   18-21, 31, 36, 45-61, 66-67, 72-73
services/marka_service.py                                                        30      9    70%   18-21, 27, 32-33, 37-38
services/palet_service.py                                                        40     19    52%   18-21, 26, 31, 42, 51-60, 65-66, 71-72
services/rapor_service.py                                                       102     53    48%   21, 25-28, 32, 36-39, 43-45, 51, 59, 67, 71-72, 76-77, 81, 85, 95-106, 118, 128, 134, 138-141, 145, 154-157, 161-163, 168-185
services/sevkiyat_service.py                                                     30     13    57%   22, 29-32, 36-39, 43-44, 48-49
services/sistem_log_service.py                                                   15      7    53%   13-19, 36-47
services/stok_sayim_service.py                                                   91      4    96%   15-16, 51, 138
services/tedarikci_service.py                                                    26     10    62%   13, 17-20, 24, 28-29, 33-34
tests/__init__.py                                                                 0      0   100%
tests/api/__init__.py                                                             0      0   100%
tests/api/conftest.py                                                             6      0   100%
tests/api/routers/__init__.py                                                     0      0   100%
tests/api/routers/test_auth_api.py                                               46      0   100%
tests/api/routers/test_markalar_api.py                                           20      0   100%
tests/api/routers/test_urunler_api.py                                            47      0   100%
tests/conftest.py                                                                67      1    99%   18
tests/factories/__init__.py                                                      17      0   100%
tests/factories/base_factory.py                                                   6      0   100%
tests/factories/depo_factory.py                                                  10      0   100%
tests/factories/irsaliye_factory.py                                              15      0   100%
tests/factories/kategori_factory.py                                               9      0   100%
tests/factories/kullanici_factory.py                                             11      0   100%
tests/factories/lot_factory.py                                                   11      0   100%
tests/factories/marka_factory.py                                                  9      0   100%
tests/factories/palet_factory.py                                                 14      0   100%
tests/factories/raf_factory.py                                                   12      0   100%
tests/factories/rapor_sablonu_factory.py                                         30      0   100%
tests/factories/sevkiyat_plani_factory.py                                        18      0   100%
tests/factories/siparis_factory.py                                               28      0   100%
tests/factories/stok_hareketi_factory.py                                         13      0   100%
tests/factories/stok_sayim_factory.py                                            22      0   100%
tests/factories/tedarikci_factory.py                                             10      0   100%
tests/factories/urun_factory.py                                                  16      0   100%
tests/integration/__init__.py                                                     0      0   100%
tests/integration/conftest.py                                                     6      0   100%
tests/integration/crud/__init__.py                                                0      0   100%
tests/integration/crud/test_depo_crud.py                                         60      0   100%
tests/integration/crud/test_irsaliye_crud.py                                     86      2    98%   164-166
tests/integration/crud/test_kategori_crud.py                                     63      0   100%
tests/integration/crud/test_rapor_crud.py                                       166      1    99%   302
tests/integration/crud/test_sevkiyat_crud.py                                     77      2    97%   136-138
tests/integration/crud/test_siparis_crud.py                                      95      0   100%
tests/integration/crud/test_stok_hareketi_crud.py                                48      0   100%
tests/integration/crud/test_urun_crud.py                                         69      0   100%
tests/integration/repositories/__init__.py                                        0      0   100%
tests/integration/services/test_kullanici_service.py                             73      0   100%
tests/integration/services/test_stok_sayim_service.py                           120      0   100%
tests/unit/__init__.py                                                            0      0   100%
tests/unit/entities/__init__.py                                                   0      0   100%
tests/unit/entities/test_schemas.py                                              92      0   100%
tests/unit/use_cases/__init__.py                                                  0      0   100%
tests/unit/use_cases/test_urun_use_cases.py                                      86      0   100%
-----------------------------------------------------------------------------------------------------------
TOTAL                                                                          6819   1700    75%
=========================== short test summary info ============================
FAILED tests/integration/crud/test_irsaliye_crud.py::TestIrsaliyeCrud::test_update_irsaliye_bulunamadi - pydantic_core._pydantic_core.ValidationError: 1 validation error for IrsaliyeUpdate
durum
  Input should be 'Taslak', 'Kesildi' or 'Gonderildi' [type=literal_error, input_value='X', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/literal_error
FAILED tests/integration/crud/test_rapor_crud.py::TestRaporVerileri::test_get_abc_analiz - AssertionError: assert 'C' == 'A'
  
  - A
  + C
FAILED tests/integration/crud/test_sevkiyat_crud.py::TestSevkiyatCrud::test_update_sevkiyat_bulunamadi - pydantic_core._pydantic_core.ValidationError: 1 validation error for SevkiyatPlaniUpdate
durum
  Input should be 'Planlandi', 'Yukleniyor', 'Tamamlandi' or 'Iptal' [type=literal_error, input_value='Yolda', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/literal_error
======================== 3 failed, 175 passed in 46.17s ========================
Error: Process completed with exit code 1.