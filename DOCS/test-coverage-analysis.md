# Test Coverage Analizi

## Çalıştırılan Komut

```bash
pytest --cov=app --cov-report=term --disable-warnings -q --tb=short

Not
Aşağıdaki çıktı önceki test çalıştırmasına aittir. 1 failed problemi çözülmüştür; coverage analizi için tablo dikkate alınmalıdır.

(.venv) PS D:\Ensar Dosya\DepoUygulaması\BackendProje> pytest --cov=app --cov-report=term --disable-warnings -q --tb=short
................................................................................................... [ 12%]
................................................................................................... [ 25%]
................................................................................................... [ 37%]
........................................F.......................................................... [ 50%]
................................................................................................... [ 63%]
................................................................................................... [ 75%]
................................................................................................... [ 88%]
.........................................................................................           [100%]
================================================ FAILURES ================================================
____________________ TestUretimSeriNoConcurrency.test_tc001_10_thread_unique_seri_no _____________________
tests\integration\test_uretim_palet_concurrency.py:167: in test_tc001_10_thread_unique_seri_no
    assert len(hatalar) == 0, f"Beklenmedik hatalar: {hatalar}"
E   AssertionError: Beklenmedik hatalar: ["OperationalError: (pymysql.err.OperationalError) (1213, 'Deadlock found when trying to get lock; try restarting transaction')\n[SQL: INSERT INTO uretim_seri_sayac (tarih, son_seri_no) VALUES (%(tarih)s, %(son_seri_no)s)]\n[parameters: {'tarih': datetime.date(2025, 4, 16), 'son_seri_no': 1}]\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", "OperationalError: (pymysql.err.OperationalError) (1213, 'Deadlock found when trying to get lock; try restarting transaction')\n[SQL: INSERT INTO uretim_seri_sayac (tarih, son_seri_no) VALUES (%(tarih)s, %(son_seri_no)s)]\n[parameters: {'tarih': datetime.date(2025, 4, 16), 'son_seri_no': 1}]\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", "OperationalError: (pymysql.err.OperationalError) (1213, 'Deadlock found when trying to get lock; try restarting transaction')\n[SQL: INSERT INTO uretim_seri_sayac (tarih, son_seri_no) VALUES (%(tarih)s, %(son_seri_no)s)]\n[parameters: {'tarih': datetime.date(2025, 4, 16), 'son_seri_no': 1}]\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", "OperationalError: (pymysql.err.OperationalError) (1213, 'Deadlock found when trying to get lock; try restarting transaction')\n[SQL: INSERT INTO uretim_seri_sayac (tarih, son_seri_no) VALUES (%(tarih)s, %(son_seri_no)s)]\n[parameters: {'tarih': datetime.date(2025, 4, 16), 'son_seri_no': 1}]\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", "OperationalError: (pymysql.err.OperationalError) (1213, 'Deadlock found when trying to get lock; try restarting transaction')\n[SQL: INSERT INTO uretim_seri_sayac (tarih, son_seri_no) VALUES (%(tarih)s, %(son_seri_no)s)]\n[parameters: {'tarih': datetime.date(2025, 4, 16), 'son_seri_no': 1}]\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", "OperationalError: (pymysql.err.OperationalError) (1213, 'Deadlock found when trying to get lock; try restarting transaction')\n[SQL: INSERT INTO uretim_seri_sayac (tarih, son_seri_no) VALUES (%(tarih)s, %(son_seri_no)s)]\n[parameters: {'tarih': datetime.date(2025, 4, 16), 'son_seri_no': 1}]\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", "OperationalError: (pymysql.err.OperationalError) (1213, 'Deadlock found when trying to get lock; try restarting transaction')\n[SQL: INSERT INTO uretim_seri_sayac (tarih, son_seri_no) VALUES (%(tarih)s, %(son_seri_no)s)]\n[parameters: {'tarih': datetime.date(2025, 4, 16), 'son_seri_no': 1}]\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", "OperationalError: (pymysql.err.OperationalError) (1213, 'Deadlock found when trying to get lock; try restarting transaction')\n[SQL: INSERT INTO uretim_seri_sayac (tarih, son_seri_no) VALUES (%(tarih)s, %(son_seri_no)s)]\n[parameters: {'tarih': datetime.date(2025, 4, 16), 'son_seri_no': 1}]\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", "OperationalError: (pymysql.err.OperationalError) (1213, 'Deadlock found when trying to get lock; try restarting transaction')\n[SQL: INSERT INTO uretim_seri_sayac (tarih, son_seri_no) VALUES (%(tarih)s, %(son_seri_no)s)]\n[parameters: {'tarih': datetime.date(2025, 4, 16), 'son_seri_no': 1}]\n(Background on this error at: https://sqlalche.me/e/20/e3q8)"]
E   assert 9 == 0
E    +  where 9 = len(["OperationalError: (pymysql.err.OperationalError) (1213, 'Deadlock found when trying to get lock; try restarting tran...h': datetime.date(2025, 4, 16), 'son_seri_no': 1}]\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", ...])
============================================= tests coverage =============================================
____________________________ coverage: platform win32, python 3.14.3-final-0 _____________________________

Name                                                                              Stmts   Miss  Cover
-----------------------------------------------------------------------------------------------------
app\__init__.py                                                                       0      0   100%
app\api\__init__.py                                                                   0      0   100%
app\api\v1\__init__.py                                                                0      0   100%
app\api\v1\routers\__init__.py                                                       29      0   100%
app\api\v1\routers\auth.py                                                           94      3    97%
app\api\v1\routers\dashboard.py                                                      10      1    90%
app\api\v1\routers\depolar.py                                                        30      0   100%
app\api\v1\routers\destek.py                                                         25      4    84%
app\api\v1\routers\etiket_sablonlari.py                                              31      6    81%
app\api\v1\routers\irsaliyeler.py                                                    23      5    78%
app\api\v1\routers\kategoriler.py                                                    30      0   100%
app\api\v1\routers\kullanicilar.py                                                   26      0   100%
app\api\v1\routers\lotlar.py                                                         36      0   100%
app\api\v1\routers\mal_kabul_irsaliyeleri.py                                         44     15    66%
app\api\v1\routers\markalar.py                                                       30      4    87%
app\api\v1\routers\mobil_terminal.py                                                140     80    43%
app\api\v1\routers\palet_rezervasyonlari.py                                          39     18    54%
app\api\v1\routers\paletler.py                                                       38      8    79%
app\api\v1\routers\raflar.py                                                         30      0   100%
app\api\v1\routers\raporlar.py                                                      125     48    62%
app\api\v1\routers\sevkiyat_planlama.py                                              28      1    96%
app\api\v1\routers\siparisler.py                                                     24      0   100%
app\api\v1\routers\sistem_loglari.py                                                 17      2    88%
app\api\v1\routers\stok_hareketleri.py                                               17      2    88%
app\api\v1\routers\stok_islemleri.py                                                106     52    51%
app\api\v1\routers\stok_sayim.py                                                     28      0   100%
app\api\v1\routers\tedarikciler.py                                                   30      6    80%
app\api\v1\routers\toplama_gorevleri.py                                              73     21    71%
app\api\v1\routers\uretim_paletleri.py                                               96      3    97%
app\api\v1\routers\urunler.py                                                        51     11    78%
app\api\v1\routers\yerlestirme_gorevleri.py                                          92     10    89%
app\api\v1\routers\zonlar.py                                                         30      0   100%
app\application\__init__.py                                                           0      0   100%
app\application\dto\__init__.py                                                      19      0   100%
app\application\dto\auth_dto.py                                                      52      3    94%
app\application\dto\dashboard_dto.py                                                 17      2    88%
app\application\dto\depo_dto.py                                                      39      3    92%
app\application\dto\destek_talebi_dto.py                                             31      3    90%
app\application\dto\etiket_dto.py                                                    52      2    96%
app\application\dto\irsaliye_dto.py                                                  84      9    89%
app\application\dto\kategori_dto.py                                                  39      3    92%
app\application\dto\kullanici_dto.py                                                 48      9    81%
app\application\dto\lot_dto.py                                                       48      1    98%
app\application\dto\mal_kabul_irsaliye_dto.py                                       143      7    95%
app\application\dto\marka_dto.py                                                     36      5    86%
app\application\dto\palet_bilgi_dto.py                                               26      0   100%
app\application\dto\palet_dto.py                                                     65     12    82%
app\application\dto\palet_rezervasyonu_dto.py                                        35      1    97%
app\application\dto\raf_dto.py                                                       57      5    91%
app\application\dto\rapor_dto.py                                                     78      6    92%
app\application\dto\sevkiyat_plani_dto.py                                            87      2    98%
app\application\dto\siparis_dto.py                                                   88      3    97%
app\application\dto\sistem_log_dto.py                                                31      1    97%
app\application\dto\stok_hareketi_dto.py                                             60      0   100%
app\application\dto\stok_islemleri_dto.py                                            79     15    81%
app\application\dto\stok_sayim_dto.py                                                59      1    98%
app\application\dto\tedarikci_dto.py                                                 48      9    81%
app\application\dto\toplama_gorevi_dto.py                                            44      0   100%
app\application\dto\uretim_paleti_dto.py                                             65      0   100%
app\application\dto\urun_dto.py                                                     197     28    86%
app\application\dto\yerlestirme_gorevi_dto.py                                        84      4    95%
app\application\dto\zon_dto.py                                                       78     16    79%
app\application\helpers.py                                                            3      0   100%
app\application\use_cases\__init__.py                                                24      0   100%
app\application\use_cases\dashboard_use_cases.py                                      9      3    67%
app\application\use_cases\depo_use_cases.py                                          56      2    96%
app\application\use_cases\destek_talebi_use_cases.py                                 60     38    37%
app\application\use_cases\etiket_sablonu_use_cases.py                                67     45    33%
app\application\use_cases\inbound_kpi_use_cases.py                                   33     23    30%
app\application\use_cases\irsaliye_use_cases.py                                     101     26    74%
app\application\use_cases\kategori_use_cases.py                                      64      4    94%
app\application\use_cases\kullanici_use_cases.py                                    100     21    79%
app\application\use_cases\lot_use_cases.py                                           98     17    83%
app\application\use_cases\mal_kabul_irsaliye_use_cases.py                           199     85    57%
app\application\use_cases\marka_use_cases.py                                         64     30    53%
app\application\use_cases\palet_etiket_use_cases.py                                  71     53    25%
app\application\use_cases\palet_rezervasyonu_use_cases.py                           108     53    51%
app\application\use_cases\palet_use_cases.py                                         82     51    38%
app\application\use_cases\raf_use_cases.py                                           82     13    84%
app\application\use_cases\rapor_use_cases.py                                        204    136    33%
app\application\use_cases\sevkiyat_plani_use_cases.py                               158     19    88%
app\application\use_cases\siparis_use_cases.py                                       87      3    97%
app\application\use_cases\sistem_log_use_cases.py                                    19      8    58%
app\application\use_cases\stok_hareketi_use_cases.py                                 69     27    61%
app\application\use_cases\stok_sayim_use_cases.py                                   127     36    72%
app\application\use_cases\tedarikci_use_cases.py                                     56     33    41%
app\application\use_cases\toplama_gorevi_use_cases.py                               174     77    56%
app\application\use_cases\uretim_paleti_use_cases.py                                245     28    89%
app\application\use_cases\urun_use_cases.py                                          85     10    88%
app\application\use_cases\yerlestirme_gorevi_use_cases.py                           356    224    37%
app\application\use_cases\zon_use_cases.py                                           75     11    85%
app\core\__init__.py                                                                  0      0   100%
app\core\auth.py                                                                     95     28    71%
app\core\config.py                                                                   31      0   100%
app\core\constants.py                                                                14      1    93%
app\core\entities\__init__.py                                                        25      0   100%
app\core\entities\depo.py                                                            16      2    88%
app\core\entities\destek_talebi.py                                                   35      8    77%
app\core\entities\etiket_sablonu.py                                                  22      6    73%
app\core\entities\irsaliye.py                                                        36      9    75%
app\core\entities\kategori.py                                                        20      5    75%
app\core\entities\kullanici.py                                                       43      4    91%
app\core\entities\lot.py                                                             33     11    67%
app\core\entities\mal_kabul_irsaliye.py                                             105     14    87%
app\core\entities\marka.py                                                           19      5    74%
app\core\entities\palet.py                                                          124      5    96%
app\core\entities\palet_durum_log.py                                                 13      0   100%
app\core\entities\palet_etiket.py                                                    22      2    91%
app\core\entities\palet_rezervasyonu.py                                              40      9    78%
app\core\entities\raf.py                                                             42      8    81%
app\core\entities\rapor.py                                                           67     11    84%
app\core\entities\sevkiyat_plani.py                                                  59     12    80%
app\core\entities\siparis.py                                                         61      6    90%
app\core\entities\sistem_log.py                                                      32      0   100%
app\core\entities\stok_hareketi.py                                                   38      5    87%
app\core\entities\stok_sayim.py                                                      56      6    89%
app\core\entities\tedarikci.py                                                       19      2    89%
app\core\entities\toplama_gorevi.py                                                  61     10    84%
app\core\entities\urun.py                                                            64     16    75%
app\core\entities\yerlestirme_gorevi.py                                              85      5    94%
app\core\entities\zon.py                                                             40      4    90%
app\core\exceptions\__init__.py                                                       3      0   100%
app\core\idempotency.py                                                              22      0   100%
app\core\repositories\__init__.py                                                    25      0   100%
app\core\repositories\dashboard_repository.py                                         8      0   100%
app\core\repositories\depo_repository.py                                              4      0   100%
app\core\repositories\destek_talebi_repository.py                                     4      0   100%
app\core\repositories\etiket_sablonu_repository.py                                    6      0   100%
app\core\repositories\irsaliye_repository.py                                          8      0   100%
app\core\repositories\kategori_repository.py                                          6      0   100%
app\core\repositories\kullanici_repository.py                                         4      0   100%
app\core\repositories\lot_repository.py                                               6      0   100%
app\core\repositories\mal_kabul_irsaliye_repository.py                               12      0   100%
app\core\repositories\marka_repository.py                                             8      0   100%
app\core\repositories\palet_durum_log_repository.py                                   3      0   100%
app\core\repositories\palet_etiket_repository.py                                      4      0   100%
app\core\repositories\palet_repository.py                                            12      0   100%
app\core\repositories\palet_rezervasyonu_repository.py                               12      0   100%
app\core\repositories\raf_repository.py                                               8      0   100%
app\core\repositories\rapor_repository.py                                             8      0   100%
app\core\repositories\sevkiyat_plani_repository.py                                    9      0   100%
app\core\repositories\siparis_repository.py                                           8      0   100%
app\core\repositories\sistem_log_repository.py                                        4      0   100%
app\core\repositories\stok_hareketi_repository.py                                    10      0   100%
app\core\repositories\stok_sayim_repository.py                                       12      0   100%
app\core\repositories\tedarikci_repository.py                                         4      0   100%
app\core\repositories\toplama_gorevi_repository.py                                    8      0   100%
app\core\repositories\uretim_seri_sayac_repository.py                                 5      0   100%
app\core\repositories\urun_repository.py                                              6      0   100%
app\core\repositories\yerlestirme_gorevi_repository.py                               10      0   100%
app\core\repositories\zon_repository.py                                               4      0   100%
app\core\services\__init__.py                                                         9      0   100%
app\core\services\etiket_render_service.py                                           20     12    40%
app\core\services\fefo_secim_servisi.py                                              30      2    93%
app\core\services\kapasite_dogrulama_servisi.py                                      44      9    80%
app\core\services\palet_bazli_stok_domain_service.py                                 34      2    94%
app\core\services\palet_cikis_service.py                                             81     27    67%
app\core\services\palet_giris_service.py                                             86     17    80%
app\core\services\palet_veri_kaynagi_service.py                                       8      0   100%
app\core\services\siparis_durum_orchestrator.py                                      44      2    95%
app\core\services\stok_cikis_domain_service.py                                       38      2    95%
app\core\services\uretim_palet_service.py                                            44      0   100%
app\core\services\uretim_seri_no_uretici.py                                           5      0   100%
app\core\services\yerlestirme_algoritmasi.py                                         85      2    98%
app\core\services\zon_uyumluluk_servisi.py                                           28      0   100%
app\infrastructure\__init__.py                                                        0      0   100%
app\infrastructure\config\__init__.py                                                 0      0   100%
app\infrastructure\config\erp_config.py                                              25      0   100%
app\infrastructure\di\__init__.py                                                     0      0   100%
app\infrastructure\di\container.py                                                    9      0   100%
app\infrastructure\di\modules\__init__.py                                             0      0   100%
app\infrastructure\di\modules\depo_envanter_di.py                                   141     24    83%
app\infrastructure\di\modules\etiket_di.py                                           32     11    66%
app\infrastructure\di\modules\katalog_di.py                                          42      9    79%
app\infrastructure\di\modules\kullanici_destek_di.py                                 34      7    79%
app\infrastructure\di\modules\rapor_dashboard_di.py                                  49     21    57%
app\infrastructure\di\modules\siparis_lojistik_di.py                                110     26    76%
app\infrastructure\di\modules\stok_di.py                                             28      2    93%
app\infrastructure\di\modules\uretim_di.py                                           38      0   100%
app\infrastructure\di\modules\urun_di.py                                             20      2    90%
app\infrastructure\persistence\__init__.py                                            0      0   100%
app\infrastructure\persistence\database.py                                            2      2     0%
app\infrastructure\persistence\mappers\__init__.py                                    8      0   100%
app\infrastructure\persistence\mappers\depo_envanter_mapper.py                       44      1    98%
app\infrastructure\persistence\mappers\katalog_mapper.py                             17      0   100%
app\infrastructure\persistence\mappers\kullanici_destek_mapper.py                    17      0   100%
app\infrastructure\persistence\mappers\rapor_mapper.py                               35     15    57%
app\infrastructure\persistence\mappers\siparis_lojistik_mapper.py                    40      5    88%
app\infrastructure\persistence\mappers\stok_sayim_mal_kabul_mapper.py                32      3    91%
app\infrastructure\persistence\mappers\urun_mapper.py                                12      0   100%
app\infrastructure\persistence\mappers\yerlestirme_mapper.py                          7      0   100%
app\infrastructure\persistence\repositories\__init__.py                              26      0   100%
app\infrastructure\persistence\repositories\sa_dashboard_repository.py               28     20    29%
app\infrastructure\persistence\repositories\sa_depo_repository.py                    42      2    95%
app\infrastructure\persistence\repositories\sa_destek_talebi_repository.py           41     29    29%
app\infrastructure\persistence\repositories\sa_etiket_sablonu_repository.py          60     44    27%
app\infrastructure\persistence\repositories\sa_irsaliye_repository.py                63     16    75%
app\infrastructure\persistence\repositories\sa_kategori_repository.py                45      2    96%
app\infrastructure\persistence\repositories\sa_kullanici_repository.py               52     10    81%
app\infrastructure\persistence\repositories\sa_lot_repository.py                     69      5    93%
app\infrastructure\persistence\repositories\sa_mal_kabul_irsaliye_repository.py     150     58    61%
app\infrastructure\persistence\repositories\sa_marka_repository.py                   45     17    62%
app\infrastructure\persistence\repositories\sa_palet_durum_log_repository.py         16      2    88%
app\infrastructure\persistence\repositories\sa_palet_etiket_repository.py            37     25    32%
app\infrastructure\persistence\repositories\sa_palet_repository.py                   89     18    80%
app\infrastructure\persistence\repositories\sa_palet_rezervasyonu_repository.py      77     31    60%
app\infrastructure\persistence\repositories\sa_raf_repository.py                     58      3    95%
app\infrastructure\persistence\repositories\sa_rapor_repository.py                  160    125    22%
app\infrastructure\persistence\repositories\sa_sevkiyat_plani_repository.py          70      9    87%
app\infrastructure\persistence\repositories\sa_siparis_repository.py                 67      8    88%
app\infrastructure\persistence\repositories\sa_sistem_log_repository.py              26      7    73%
app\infrastructure\persistence\repositories\sa_stok_hareketi_repository.py           39     14    64%
app\infrastructure\persistence\repositories\sa_stok_sayim_repository.py              67     13    81%
app\infrastructure\persistence\repositories\sa_tedarikci_repository.py               45     32    29%
app\infrastructure\persistence\repositories\sa_toplama_gorevi_repository.py          88     19    78%
app\infrastructure\persistence\repositories\sa_uretim_seri_sayac_repository.py       17      3    82%
app\infrastructure\persistence\repositories\sa_urun_repository.py                    71     13    82%
app\infrastructure\persistence\repositories\sa_yerlestirme_gorevi_repository.py      99     18    82%
app\infrastructure\persistence\repositories\sa_zon_repository.py                     52      4    92%
app\infrastructure\scheduler\__init__.py                                             28      3    89%
app\infrastructure\scheduler\rapor_scheduler.py                                      68     57    16%
app\infrastructure\scheduler\staging_uyari_job.py                                    30     23    23%
app\infrastructure\services\__init__.py                                               3      0   100%
app\infrastructure\services\erp_palet_veri_kaynagi_service.py                        88     12    86%
app\infrastructure\services\irsaliye_palet_veri_kaynagi_service.py                   60      6    90%
app\infrastructure\services\mock_erp_palet_veri_kaynagi_service.py                   21      0   100%
app\infrastructure\services\palet_sorgulama_service.py                               32      0   100%
app\infrastructure\services\sql_uretim_seri_no_uretici.py                             9      0   100%
-----------------------------------------------------------------------------------------------------
TOTAL                                                                             10933   2571    76%
======================================== short test summary info =========================================
FAILED tests/integration/test_uretim_palet_concurrency.py::TestUretimSeriNoConcurrency::test_tc001_10_thread_unique_seri_no - AssertionError: Beklenmedik hatalar: ["OperationalError: (pymysql.err.OperationalError) (1213, 'Deadlo...
1 failed, 781 passed, 4077 warnings in 485.08s (0:08:05)