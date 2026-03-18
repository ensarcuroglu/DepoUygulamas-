Run pytest --cov=. --cov-report=term-missing -v
  pytest --cov=. --cov-report=term-missing -v
  shell: /usr/bin/bash -e {0}
  env:
    pythonLocation: /opt/hostedtoolcache/Python/3.11.15/x64
    PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.15/x64/lib/pkgconfig
    Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.15/x64
    Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.15/x64
    Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.15/x64
    LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.15/x64/lib
    DB_USER: root
    DB_PASSWORD: testpass
    DB_HOST: 127.0.0.1
    DB_PORT: 3306
    DB_NAME: depo_db_test
    JWT_SECRET_KEY: ci-test-secret-key-minimum-32-karakter-uzunlugunda
  
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.2, pluggy-1.6.0 -- /opt/hostedtoolcache/Python/3.11.15/x64/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/DepoUygulamas-/DepoUygulamas-/BackendProje
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.12.1, cov-7.0.0, Faker-40.11.0
collecting ... collected 67 items

tests/api/routers/test_auth_api.py::TestLoginEndpoint::test_basarili_login PASSED [  1%]
tests/api/routers/test_auth_api.py::TestLoginEndpoint::test_yanlis_sifre PASSED [  2%]
tests/api/routers/test_auth_api.py::TestLoginEndpoint::test_olmayan_kullanici PASSED [  4%]
tests/api/routers/test_auth_api.py::TestMeEndpoint::test_yetkili_erisim PASSED [  5%]
tests/api/routers/test_auth_api.py::TestMeEndpoint::test_yetkisiz_erisim PASSED [  7%]
tests/api/routers/test_auth_api.py::TestRegisterEndpoint::test_admin_kayit_olustur PASSED [  8%]
tests/api/routers/test_auth_api.py::TestRegisterEndpoint::test_depocu_kayit_olusturamaz PASSED [ 10%]
tests/api/routers/test_auth_api.py::TestRegisterEndpoint::test_tekrar_eden_kullanici_adi PASSED [ 11%]
tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_marka_listele PASSED [ 13%]
tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_marka_olustur PASSED [ 14%]
tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_yetkisiz_erisim PASSED [ 16%]
tests/api/routers/test_markalar_api.py::TestMarkaEndpoints::test_depocu_erisim PASSED [ 17%]
tests/api/routers/test_urunler_api.py::TestUrunListele::test_yetkisiz_erisim PASSED [ 19%]
tests/api/routers/test_urunler_api.py::TestUrunListele::test_bos_liste PASSED [ 20%]
tests/api/routers/test_urunler_api.py::TestUrunListele::test_urun_listeleme PASSED [ 22%]
tests/api/routers/test_urunler_api.py::TestUrunListele::test_arama_filtresi PASSED [ 23%]
tests/api/routers/test_urunler_api.py::TestUrunOlustur::test_basarili_olusturma PASSED [ 25%]
tests/api/routers/test_urunler_api.py::TestUrunOlustur::test_gecersiz_barkod PASSED [ 26%]
tests/api/routers/test_urunler_api.py::TestUrunGetir::test_basarili_getir PASSED [ 28%]
tests/api/routers/test_urunler_api.py::TestUrunGetir::test_olmayan_urun PASSED [ 29%]
tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_create_stok_giris PASSED [ 31%]
tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_create_stok_cikis_fifo PASSED [ 32%]
tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_get_stok_hareketleri_filtre PASSED [ 34%]
tests/integration/crud/test_stok_hareketi_crud.py::TestStokHareketiCrud::test_get_stok_hareketleri_urun_filtre PASSED [ 35%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_create_urun PASSED [ 37%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_urun_by_id PASSED [ 38%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_urun_by_id_bulunamadi PASSED [ 40%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_urun_by_barkod PASSED [ 41%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_urunler_search PASSED [ 43%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_urunler_kategori_filtre PASSED [ 44%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_update_urun PASSED [ 46%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_delete_urun_soft_delete PASSED [ 47%]
tests/integration/crud/test_urun_crud.py::TestUrunCrud::test_get_kritik_urunler PASSED [ 49%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_gecerli_urun PASSED [ 50%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_barkod_format_hatasi PASSED [ 52%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_ean_format_hatasi PASSED [ 53%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_gecerli_ean PASSED [ 55%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_fiyat_negatif_olamaz PASSED [ 56%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_ic_adet_sifir_olamaz PASSED [ 58%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_gecersiz_birim PASSED [ 59%]
tests/unit/entities/test_schemas.py::TestUrunCreateSchema::test_gecerli_birimler PASSED [ 61%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_gecerli_kullanici PASSED [ 62%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_sifre_cok_kisa PASSED [ 64%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_sifre_buyuk_harf_yok PASSED [ 65%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_sifre_kucuk_harf_yok PASSED [ 67%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_sifre_rakam_yok PASSED [ 68%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_gecersiz_rol PASSED [ 70%]
tests/unit/entities/test_schemas.py::TestKullaniciCreateSchema::test_gecerli_roller PASSED [ 71%]
tests/unit/entities/test_schemas.py::TestPaletCreateSchema::test_koli_adedi_pozitif_olmali PASSED [ 73%]
tests/unit/entities/test_schemas.py::TestPaletCreateSchema::test_koli_adedi_negatif_olamaz PASSED [ 74%]
tests/unit/entities/test_schemas.py::TestPaletCreateSchema::test_gecerli_palet PASSED [ 76%]
tests/unit/entities/test_schemas.py::TestRafBaseSchema::test_kapasite_pozitif_olmali PASSED [ 77%]
tests/unit/entities/test_schemas.py::TestRafBaseSchema::test_gecerli_raf PASSED [ 79%]
tests/unit/entities/test_schemas.py::TestStokHareketiSchema::test_gecerli_giris PASSED [ 80%]
tests/unit/entities/test_schemas.py::TestStokHareketiSchema::test_gecerli_cikis PASSED [ 82%]
tests/unit/entities/test_schemas.py::TestStokHareketiSchema::test_gecersiz_hareket_tipi PASSED [ 83%]
tests/unit/entities/test_schemas.py::TestLoginRequestSchema::test_kullanici_adi_cok_kisa PASSED [ 85%]
tests/unit/entities/test_schemas.py::TestLoginRequestSchema::test_gecerli_login PASSED [ 86%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunOlusturUseCase::test_basarili_olusturma PASSED [ 88%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunOlusturUseCase::test_barkod_cakismasi PASSED [ 89%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunGetirUseCase::test_basarili_getir PASSED [ 91%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunGetirUseCase::test_bulunamadi PASSED [ 92%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunGetirUseCase::test_barkod_ile_getir PASSED [ 94%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunListeleUseCase::test_bos_liste PASSED [ 95%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunListeleUseCase::test_filtreli_listeleme PASSED [ 97%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunSilUseCase::test_basarili_silme PASSED [ 98%]
tests/unit/use_cases/test_urun_use_cases.py::TestUrunSilUseCase::test_olmayan_urun_silme PASSED [100%]

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
core/api_exceptions.py                                                           67     21    69%   31, 42-43, 56-57, 64-65, 76, 83, 90, 117, 124-128, 139-140, 151-152, 177
core/exception_handlers.py                                                       14      4    71%   47-52
core/exceptions.py                                                                2      0   100%
crud/__init__.py                                                                 15      0   100%
crud/dashboard_crud.py                                                           11      6    45%   9-23
crud/depo_crud.py                                                                35     27    23%   7-10, 13, 16-30, 33-40, 43-48
crud/destek_crud.py                                                              35     27    23%   9-14, 17, 20-34, 37-58
crud/irsaliye_crud.py                                                            63     51    19%   13-29, 32-45, 48, 51-104, 107-127
crud/kategori_crud.py                                                            40     32    20%   7-10, 13, 16-30, 33-50, 53-67
crud/lot_crud.py                                                                 40     29    28%   9-14, 17, 23, 29-33, 36-43, 46-51, 55-56
crud/marka_crud.py                                                               32     15    53%   13, 23-30, 33-38
crud/palet_crud.py                                                               43     33    23%   9-19, 22, 28, 34-38, 41-48, 52-57, 61-64
crud/raf_crud.py                                                                 34     26    24%   7-12, 15, 18-22, 25-32, 35-40
crud/rapor_crud.py                                                              138    114    17%   22-27, 30, 33-50, 53-70, 73-88, 96-99, 102-110, 118-121, 124, 127-141, 144-161, 164-179, 188-200, 204-219, 223-236, 241, 256-257, 278-317, 322-336
crud/sevkiyat_crud.py                                                            59     48    19%   11-22, 25, 28-42, 45-92, 95-110
crud/siparis_crud.py                                                             69     58    16%   11-27, 30-46, 49, 55-93, 96-115, 118-133
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
schemas.py                                                                      500      8    98%   374-381
services/__init__.py                                                             14      0   100%
services/depo_service.py                                                         61     33    46%   14, 18-21, 25, 29-30, 34-35, 42, 46-49, 54-61, 65-69, 73-78
services/destek_service.py                                                       29     14    52%   22-24, 32-37, 41, 45-50
services/irsaliye_service.py                                                     34     17    50%   21, 25-28, 32-35, 39-40, 45-71
services/kategori_service.py                                                     30     13    57%   14, 18-21, 25-28, 32-33, 37-38
services/kullanici_service.py                                                    49     34    31%   17, 21-24, 34-68, 72-78
services/lot_service.py                                                          36     17    53%   18-21, 31, 36, 45-61, 66-67, 72-73
services/marka_service.py                                                        30      9    70%   18-21, 27, 32-33, 37-38
services/palet_service.py                                                        40     19    52%   18-21, 26, 31, 42, 51-60, 65-66, 71-72
services/rapor_service.py                                                       102     53    48%   21, 25-28, 32, 36-39, 43-45, 51, 59, 67, 71-72, 76-77, 81, 85, 95-106, 118, 128, 134, 138-141, 145, 154-157, 161-163, 168-185
services/sevkiyat_service.py                                                     30     13    57%   22, 29-32, 36-39, 43-44, 48-49
services/sistem_log_service.py                                                   15      7    53%   13-19, 36-47
services/stok_sayim_service.py                                                   91     70    23%   14-17, 24-30, 34-37, 46-79, 89-125, 133-172, 186-196
services/tedarikci_service.py                                                    26     10    62%   13, 17-20, 24, 28-29, 33-34
tests/__init__.py                                                                 0      0   100%
tests/api/__init__.py                                                             0      0   100%
tests/api/conftest.py                                                             6      0   100%
tests/api/routers/__init__.py                                                     0      0   100%
tests/api/routers/test_auth_api.py                                               46      0   100%
tests/api/routers/test_markalar_api.py                                           20      0   100%
tests/api/routers/test_urunler_api.py                                            47      0   100%
tests/conftest.py                                                                67      1    99%   18
tests/factories/__init__.py                                                      12      0   100%
tests/factories/base_factory.py                                                   6      0   100%
tests/factories/depo_factory.py                                                  10      0   100%
tests/factories/kategori_factory.py                                               9      0   100%
tests/factories/kullanici_factory.py                                             11      0   100%
tests/factories/lot_factory.py                                                   11      0   100%
tests/factories/marka_factory.py                                                  9      0   100%
tests/factories/palet_factory.py                                                 14      0   100%
tests/factories/raf_factory.py                                                   12      0   100%
tests/factories/stok_hareketi_factory.py                                         13      0   100%
tests/factories/tedarikci_factory.py                                             10      0   100%
tests/factories/urun_factory.py                                                  16      0   100%
tests/integration/__init__.py                                                     0      0   100%
tests/integration/conftest.py                                                     6      0   100%
tests/integration/crud/__init__.py                                                0      0   100%
tests/integration/crud/test_stok_hareketi_crud.py                                48      0   100%
tests/integration/crud/test_urun_crud.py                                         69      0   100%
tests/integration/repositories/__init__.py                                        0      0   100%
tests/unit/__init__.py                                                            0      0   100%
tests/unit/entities/__init__.py                                                   0      0   100%
tests/unit/entities/test_schemas.py                                              92      0   100%
tests/unit/use_cases/__init__.py                                                  0      0   100%
tests/unit/use_cases/test_urun_use_cases.py                                      86      0   100%
-----------------------------------------------------------------------------------------------------------
TOTAL                                                                          5961   2103    65%
============================= 67 passed in 14.28s ==============================