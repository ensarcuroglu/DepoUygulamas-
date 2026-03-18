=========================== short test summary info ============================
FAILED tests/api/routers/test_auth_api.py::TestLoginEndpoint::test_basarili_login - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
FAILED tests/api/routers/test_auth_api.py::TestLoginEndpoint::test_yanlis_sifre - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
FAILED tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_create_stok_giris - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
FAILED tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_create_stok_cikis_fifo - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
FAILED tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_get_stok_hareketleri_filtre - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
FAILED tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_get_stok_hareketleri_urun_filtre - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
FAILED tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_create_urun - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
FAILED tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_update_urun - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
FAILED tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_delete_urun_soft_delete - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_auth_api.py::TestMeEndpoint::test_yetkili_erisim - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_auth_api.py::TestRegisterEndpoint::test_admin_kayit_olustur - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_auth_api.py::TestRegisterEndpoint::test_depocu_kayit_olusturamaz - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_auth_api.py::TestRegisterEndpoint::test_tekrar_eden_kullanici_adi - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_marka_listele - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_marka_olustur - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_depocu_erisim - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_urunler_api.py::TestUrunListele::test_bos_liste - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_urunler_api.py::TestUrunListele::test_urun_listeleme - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_urunler_api.py::TestUrunListele::test_arama_filtresi - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_urunler_api.py::TestUrunOlustur::test_basarili_olusturma - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_urunler_api.py::TestUrunOlustur::test_gecersiz_barkod - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_urunler_api.py::TestUrunGetir::test_basarili_getir - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
ERROR tests/api/routers/test_urunler_api.py::TestUrunGetir::test_olmayan_urun - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
============ 9 failed, 44 passed, 27 warnings, 14 errors in 21.64s =============
Error: Process completed with exit code 1.



Yeni hatalar:
=========================== short test summary info ============================
FAILED tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_marka_olustur - assert 201 == 200
 +  where 201 = <Response [201 Created]>.status_code
FAILED tests/api/routers/test_urunler_api.py::TestUrunOlustur::test_basarili_olusturma - assert 201 == 200
 +  where 201 = <Response [201 Created]>.status_code
FAILED tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_create_stok_cikis_fifo - sqlalchemy.exc.ProgrammingError: (pymysql.err.ProgrammingError) (1064, "You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'NULLS LAST, lotlar.uretim_tarihi ASC NULLS LAST, paletler.tarih ASC FOR UPDATE' at line 3")
[SQL: SELECT paletler.id AS paletler_id, paletler.lot_id AS paletler_lot_id, paletler.raf_id AS paletler_raf_id, paletler.palet_no AS paletler_palet_no, paletler.koli_adedi AS paletler_koli_adedi, paletler.palet_kg AS paletler_palet_kg, paletler.vardiya AS paletler_vardiya, paletler.tarih AS paletler_tarih, paletler.aktif AS paletler_aktif, paletler.olusturma_tarihi AS paletler_olusturma_tarihi 
FROM paletler INNER JOIN lotlar ON lotlar.id = paletler.lot_id 
WHERE lotlar.urun_id = %(urun_id_1)s AND lotlar.aktif = true AND paletler.aktif = true AND paletler.koli_adedi > %(koli_adedi_1)s ORDER BY lotlar.son_kullanma_tarihi ASC NULLS LAST, lotlar.uretim_tarihi ASC NULLS LAST, paletler.tarih ASC FOR UPDATE]
[parameters: {'urun_id_1': 1, 'koli_adedi_1': 0}]
(Background on this error at: https://sqlalche.me/e/20/f405)
FAILED tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_get_stok_hareketleri_urun_filtre - sqlalchemy.exc.IntegrityError: (pymysql.err.IntegrityError) (1062, "Duplicate entry 'OTM-20260318063506' for key 'paletler.palet_no'")
[SQL: INSERT INTO paletler (lot_id, raf_id, palet_no, koli_adedi, palet_kg, vardiya, tarih, aktif, olusturma_tarihi) VALUES (%(lot_id)s, %(raf_id)s, %(palet_no)s, %(koli_adedi)s, %(palet_kg)s, %(vardiya)s, %(tarih)s, %(aktif)s, %(olusturma_tarihi)s)]
[parameters: {'lot_id': 2, 'raf_id': 1, 'palet_no': 'OTM-20260318063506', 'koli_adedi': 20, 'palet_kg': None, 'vardiya': 'Hızlı Giriş', 'tarih': datetime.datetime(2026, 3, 18, 6, 35, 6, 823658), 'aktif': 1, 'olusturma_tarihi': datetime.datetime(2026, 3, 18, 6, 35, 6, 823661)}]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
================== 4 failed, 63 passed, 27 warnings in 16.25s ==================

