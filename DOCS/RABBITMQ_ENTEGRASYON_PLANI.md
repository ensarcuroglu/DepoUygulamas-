# RabbitMQ Entegrasyon Uygulama Planı

**Tarih:** 2026-05-12  
**Revizyon tarihi:** 2026-05-13  
**Hedef uygulama:** Depo Yönetim Sistemi (WMS)  
**İlk entegrasyon alanı:** Operatör Performans (LMS) görev event hattı

## Approach

RabbitMQ, ilk fazda operatör performans event'lerini asenkron taşımak için kullanılmalı; mevcut DB tabanlı transactional outbox korunmalıdır. Use case'ler yine `IPerformansEventPublisher` üzerinden event üretir, event önce veritabanına commit edilir, ardından ayrı bir outbox relay RabbitMQ'ya kalıcı mesaj yayınlar ve consumer bu mesajları idempotent şekilde KPI aggregasyonuna işler.

Bu yaklaşım, request transaction'ı ile broker yayınını birbirine kilitlemeden güvenilirlik sağlar. RabbitMQ kapalıysa event kaybolmaz; mevcut APScheduler tabanlı DB polling hattı kontrollü fallback olarak tutulabilir.

## Mevcut Tespitler

| Tespit | Kanıt | Güven |
|---|---|---|
| LMS event yayını zaten arayüz üzerinden soyutlanmış. | `BackendProje/app/core/services/performans_event_publisher.py` içinde `IPerformansEventPublisher` var. | High |
| Mevcut implementasyon transactional outbox olarak DB'ye yazıyor. | `db_outbox_performans_event_publisher.py`, `gorev_performans_eventleri` tablosuna `auto_commit=False` insert ediyor. | High |
| Aggregator DB outbox'tan okuyup KPI tablosunu güncelliyor. | `MetriklerAggregasyonUseCase`, `aggregate_edildi=False` eventleri okuyup `operator_vardiya_metrikleri` tablosuna upsert ediyor. | High |
| Scheduler altyapısı hazır. | `operator_metrik_aggregator_job.py` ve `scheduler/__init__.py`, 5 dakikalık APScheduler job kullanıyor. | High |
| RabbitMQ şu anda stack'te yok. | `compose.yml`, `infra/env/dev.env`, `BackendProje/requirements.txt` içinde RabbitMQ servisi veya client dependency yok. | High |
| Doğrudan use case içinde RabbitMQ publish etmek riskli olur. | Broker publish işlemi DB transaction rollback'iyle atomik değildir; mevcut outbox deseni bu problemi çözmek için doğru başlangıç noktasıdır. | Medium |

## Scope

- **In:**
  - Faz 1'de yalnızca `BackendProje` içindeki LMS Operatör Performans event hattı için RabbitMQ outbox relay ve consumer.
  - `compose.yml` içine local RabbitMQ servisi ve kalıcı mimariyi temsil eden ayrı `backend-worker` süreci.
  - `Settings`, `.env.example`, `infra/env/dev.env` RabbitMQ ayarları.
  - Event payload şeması, durable exchange/queue/DLQ topolojisi.
  - Idempotent consumer, retry/DLQ davranışı ve DB fallback.
  - Unit/integration testleri ve kısa operasyon notları.

- **Out:**
  - İlk fazda tüm uygulama eventlerini RabbitMQ'ya taşımak.
  - MySQL transactional outbox'ı tamamen kaldırmak.
  - Frontend değişikliği yapmak.
  - WmsAiService, DocAiService, AgvSimService veya diğer servis eventlerini bu fazda RabbitMQ'ya bağlamak; bunlar sonraki fazlara bırakılır.
  - Production cluster/HA RabbitMQ kurulumunu repo içinde otomatikleştirmek.

## Önerilen RabbitMQ Topolojisi

| Bileşen | Öneri |
|---|---|
| Exchange | `depo.events`, type `topic`, durable |
| Routing key | `lms.gorev_performans.<event_tipi>` |
| Queue | `depo.lms.operator_metrikleri`, durable |
| Dead-letter exchange | `depo.events.dlx`, durable |
| Dead-letter queue | `depo.lms.operator_metrikleri.dlq`, durable |
| Mesaj modu | Persistent message, publisher confirm açık |
| Consumer modeli | At-least-once delivery + DB tarafında idempotency |

Önerilen payload:

```json
{
  "schema_version": 1,
  "event_id": 123,
  "event_tipi": "GOREV_TAMAMLANDI",
  "gorev_tipi": "yerlestirme",
  "gorev_id": 456,
  "kullanici_id": 7,
  "depo_id": 1,
  "sure_saniye": 320,
  "iptal_nedeni": null,
  "payload": {},
  "olusturma_tarihi": "2026-05-12T10:00:00Z"
}
```

## Action Items

- [ ] **Add RabbitMQ runtime configuration.** `BackendProje/app/core/config.py`, `BackendProje/.env.example`, `infra/env/dev.env` içine `RABBITMQ_ENABLED`, `RABBITMQ_URL`, `RABBITMQ_EXCHANGE`, `RABBITMQ_QUEUE`, `RABBITMQ_DLX`, `RABBITMQ_PREFETCH`, `RABBITMQ_RELAY_BATCH_SIZE` alanlarını ekle.

- [ ] **Add broker dependency and local infrastructure.** `BackendProje/requirements.txt` içine sync yapı ile uyumlu `pika` ekle; `compose.yml` içine `rabbitmq:3-management` servisi, `5672` ve `15672` portları, healthcheck ve volume tanımla.

- [ ] **Extend the outbox schema safely.** `GorevPerformansEvent` için Alembic migration ile `event_uuid`, `rabbitmq_yayinlandi`, `rabbitmq_yayin_tarihi`, `rabbitmq_deneme_sayisi`, `rabbitmq_son_hata` alanlarını ekle; model, entity, mapper ve repository katmanlarını senkron güncelle.

- [ ] **Create messaging infrastructure.** `BackendProje/app/infrastructure/messaging/` altında RabbitMQ connection factory, topology declarer, JSON serializer ve publisher sınıflarını oluştur; publisher confirm kullan ve mesajları persistent gönder.

- [ ] **Implement the outbox relay.** `gorev_performans_eventleri` içinden commit edilmiş ama `rabbitmq_yayinlandi=False` eventleri batch halinde oku, RabbitMQ'ya yayınla, broker confirm sonrası `rabbitmq_yayinlandi=True` olarak işaretle; hatalarda deneme sayısı ve son hata bilgisini kaydet.

- [ ] **Refactor aggregation for consumer reuse.** `MetriklerAggregasyonUseCase` içindeki event işleme çekirdeğini `eventleri_isle(eventler)` gibi tekrar kullanılabilir bir metoda ayır; mevcut APScheduler DB polling davranışını koru.

- [ ] **Implement the RabbitMQ consumer worker.** `BackendProje/app/infrastructure/messaging/operator_performans_consumer.py` içinde queue tüketimi yap; mesajdan `event_id` al, DB'den event'i kilitleyerek oku, `aggregate_edildi=True` ise ack ile geç, değilse aggregasyonu çalıştırıp commit sonrası ack ver.

- [ ] **Wire the runtime modes.** `RABBITMQ_ENABLED=false` iken mevcut APScheduler aggregator çalışmaya devam etsin; `true` iken relay job + consumer worker aktif olsun. Kalıcı mimaride consumer ve relay işleri API sürecinden ayrılmış `backend-worker` sürecinde çalışsın; local geliştirmede geçici olarak API içinde background worker kabul edilebilir. Local compose için ayrı `backend-worker` servisi ekle ve komutu `python -m app.infrastructure.messaging.operator_performans_consumer` yap.

- [ ] **Add focused tests.** Serializer, topology, relay retry, idempotent consumer ve aggregation reuse için unit test yaz; mevcut `test_lms_publisher_hook_e2e.py` ve `test_lms_aggregator.py` testlerini koru; RabbitMQ gerektiren testleri ayrı marker ile opsiyonel çalıştır.

- [ ] **Document rollout and fallback.** `CLAUDE.md` veya ayrı kısa runbook'a local RabbitMQ başlatma, management UI, env ayarları, DLQ kontrolü, broker kapalıyken fallback ve rollback adımlarını ekle.

## Validation

- [ ] `cd BackendProje && ruff check .`
- [ ] `cd BackendProje && pytest -m unit`
- [ ] `cd BackendProje && pytest tests/integration/test_lms_aggregator.py tests/integration/test_lms_publisher_hook_e2e.py`
- [ ] `docker compose up -d rabbitmq backend backend-worker`
- [ ] RabbitMQ UI: `http://localhost:15672` üzerinden `depo.events` exchange'i, `depo.lms.operator_metrikleri` queue'su ve DLQ görünür olmalı.
- [ ] Manuel akış: bir yerleştirme/toplama görevi başlat-tamamla; event DB outbox'a yazılmalı, relay mesajı yayınlamalı, consumer queue'yu boşaltmalı ve `operator_vardiya_metrikleri` güncellenmeli.
- [ ] Dayanıklılık akışı: RabbitMQ kapalıyken görev tamamla; event DB'de beklemeli. RabbitMQ tekrar açılınca relay event'i yayınlamalı ve KPI aggregasyon tamamlanmalı.
- [ ] Production readiness: managed broker/HA cluster seçimi, monitoring, backup, failover, DLQ izleme ve mesaj kalıcılığı stratejisi production geçişinden önce netleştirilmeli.

## Mimari Kararlar

- **Faz 1 kapsamı:** İlk canlı kullanım yalnızca LMS Operatör Performans event hattı ile sınırlı kalacaktır. RabbitMQ entegrasyonu düşük kapsamlı ve ölçülebilir bir alanda doğrulandıktan sonra DocAi, AGV ve diğer servis eventleri sonraki fazlarda aynı exchange mimarisine dahil edilebilir.
- **Production broker stratejisi:** İlk production geçişinde tercih sırası managed RabbitMQ/broker, ardından HA destekli RabbitMQ cluster olmalıdır. Tek node RabbitMQ yalnızca geliştirme, test veya düşük riskli pilot ortamlar için uygun kabul edilir.
- **Worker ayrımı:** Consumer ve relay işleri kalıcı mimaride ayrı `backend-worker` süreci olarak deploy edilmelidir. Bu ayrım ölçekleme, hata izolasyonu ve operasyonel takip için ana tasarım kararıdır; local geliştirme ortamında geçici olarak backend içinde background worker kabul edilebilir.
