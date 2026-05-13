# RabbitMQ Operasyon Runbook'u

LMS Operatör Performans event hattı (Faz 1–4) için günlük operasyon, sorun giderme ve rollback rehberi.

## Mimari Özet

```
yerlestirme/toplama use case
        │
        ▼
DbOutboxPerformansEventPublisher  ── INSERT (auto_commit=False)
        │ outer tx COMMIT
        ▼
gorev_performans_eventleri (transactional outbox)
        │
        │  ┌─ APScheduler relay job (her 10 sn, RABBITMQ_ENABLED=true)
        ▼  ▼
RabbitMqOutboxRelayUseCase ── publish (persistent, confirm) ──▶ depo.events (topic exchange)
                                                                       │
                                                              binding lms.gorev_performans.*
                                                                       ▼
                                                       depo.lms.operator_metrikleri (queue)
                                                                       │
                                                                       ▼
                                            OperatorPerformansConsumer (backend-worker)
                                                                       │
                                                                       ▼
                                            MetriklerAggregasyonUseCase.eventleri_isle
                                                                       │
                                                                       ▼
                                                       operator_vardiya_metrikleri
```

## Çalıştırma Modları

| `RABBITMQ_ENABLED` | Davranış |
|---|---|
| `false` (default) | Eski Faz 1 akışı: APScheduler her 5dk DB polling aggregator çalıştırır. Relay ve consumer devre dışı. `backend-worker` container çalışsa bile boş döngüde bekler. |
| `true` | Faz 4 akışı: `backend` içinde relay job (10 sn), `backend-worker` consumer worker. DB polling aggregator job kayıt edilmez. |

Mod değiştirme için `infra/env/dev.env` veya `BackendProje/.env` içinde `RABBITMQ_ENABLED` değerini güncelle ve `docker compose up -d backend backend-worker` ile recreate et.

## Local Başlatma

```bash
# Sıfırdan başlatma
cd "/mnt/d/Ensar Dosya/DepoUygulamasi"
docker compose up -d                              # mysql + rabbitmq + backend + diğerleri

# Sadece RabbitMQ akışını test edeceksen
docker compose up -d rabbitmq backend backend-worker

# Backend image güncellendiyse (requirements.txt değişti)
docker compose build backend
docker compose up -d backend backend-worker
```

Servisler:
- Backend API → `http://localhost:8000`
- RabbitMQ AMQP → `localhost:5672`
- RabbitMQ Management UI → `http://localhost:15672` (kullanıcı/şifre: `guest` / `guest`)

## Management UI ile İnceleme

| Hedef | URL |
|---|---|
| Exchange listesi | `http://localhost:15672/#/exchanges` |
| Queue listesi + mesaj sayısı | `http://localhost:15672/#/queues` |
| Belirli queue içeriği (get message) | `Queues → depo.lms.operator_metrikleri → Get messages` |
| Connection / Channel sağlığı | `http://localhost:15672/#/connections` |
| DLQ izleme | `Queues → depo.lms.operator_metrikleri.dlq` |

## CLI ile İnceleme

```bash
# Exchange, queue, binding listesi
docker compose exec rabbitmq rabbitmqctl list_exchanges name type durable
docker compose exec rabbitmq rabbitmqctl list_queues name messages durable
docker compose exec rabbitmq rabbitmqctl list_bindings source_name routing_key destination_name

# Mesajın içeriğini peek + requeue (consumer'a dokunmadan)
docker compose exec rabbitmq rabbitmqadmin --username=guest --password=guest \
  get queue=depo.lms.operator_metrikleri count=1 ackmode=ack_requeue_true

# Queue'yu temizle (test verisi sonrası)
docker compose exec rabbitmq rabbitmqctl purge_queue depo.lms.operator_metrikleri
docker compose exec rabbitmq rabbitmqctl purge_queue depo.lms.operator_metrikleri.dlq
```

## Topoloji Referansı

| Bileşen | Değer | Notlar |
|---|---|---|
| Exchange | `depo.events` | topic, durable |
| Queue | `depo.lms.operator_metrikleri` | durable, `x-dead-letter-exchange=depo.events.dlx` |
| Routing key (publish) | `lms.gorev_performans.<event_tipi>` | örn. `lms.gorev_performans.GOREV_TAMAMLANDI` |
| Queue binding | `lms.gorev_performans.*` | wildcard |
| DLX | `depo.events.dlx` | topic, durable |
| DLQ | `depo.lms.operator_metrikleri.dlq` | durable |
| Mesaj | persistent (`delivery_mode=2`) + publisher confirm + mandatory |
| Şema | `schema_version=1` JSON; bkz. `app/infrastructure/messaging/serializer.py` |

## DLQ Yönetimi

DLQ'ya mesaj düşmesinin 3 nedeni:

1. **Parse hatası** — payload JSON değil veya `schema_version` desteklenmiyor. Consumer `basic_nack(requeue=False)` ile DLQ'ya yollar.
2. **Event DB'de bulunamadı** — Mesajdaki `event_id` `gorev_performans_eventleri`'nde yok (örn. ortam temizlenmiş, eski mesaj döngüde). Consumer bunu sonsuz requeue etmemek için DLQ'ya yollar.
3. **TTL/queue-length aşımı** — Şu an queue'da `x-message-ttl` yok; bu durum tetiklenmez. Production'da TTL eklenirse oluşabilir.

**DLQ inceleme akışı:**

```bash
# DLQ derinliği
docker compose exec rabbitmq rabbitmqctl list_queues name messages | grep dlq

# Bir DLQ mesajını oku ve sebebini gör (payload + headers)
docker compose exec rabbitmq rabbitmqadmin --username=guest --password=guest \
  get queue=depo.lms.operator_metrikleri.dlq count=5 ackmode=ack_requeue_true
```

**Manuel re-publish (yeni event_id eklendikten sonra DLQ mesajını yeniden işleme):**

DLQ mesajını ack'leyip ana exchange'e yeniden publish et:

```bash
# Mesajı al + ack (silinir)
docker compose exec rabbitmq rabbitmqadmin --username=guest --password=guest \
  get queue=depo.lms.operator_metrikleri.dlq count=1 ackmode=ack_requeue_false

# Payload'ı not alıp ana exchange'e yeniden publish et
docker compose exec rabbitmq rabbitmqadmin --username=guest --password=guest publish \
  exchange=depo.events \
  routing_key=lms.gorev_performans.GOREV_TAMAMLANDI \
  payload='<DLQ mesajından kopyala>' \
  properties='{"content_type":"application/json","delivery_mode":2}'
```

> Production'da bunun yerine küçük bir admin CLI/endpoint yazılması önerilir; bu fazda manuel kabul edilmiştir.

## Broker Down/Up Davranışı

| Senaryo | Beklenen |
|---|---|
| Broker stopped, görev tamamlandı | Event DB'ye yazılır (`rabbitmq_yayinlandi=0`). Relay her 10sn'de "broker kapalı, batch atlanıyor" log'lar. Hiçbir event kaybolmaz. |
| Broker tekrar başladı | İlk relay tetiklemesinde bekleyen tüm event'ler publish edilir; consumer worker da otomatik reconnect (5sn aralık) ile queue'ya geri döner. |
| Publish denemesi sırasında broker düştü | Mevcut event için `rabbitmq_deneme_sayisi += 1`, `rabbitmq_son_hata` yazılır. Batch kesilir, sonraki tetiklemede tekrar denenir. |
| Connection acılış başarısız (broker kapalı) | Hiçbir publish denemesi yapılmadı sayılır; `deneme_sayisi` artmaz, log seviyesinde sadece WARNING. |
| Consumer DB hatası (transient) | Mesaj `basic_nack(requeue=True)` ile queue'ya iade edilir. Sürekli fail eden mesajlar için TTL/retry header'ları Faz 6+'da düşünülebilir. |

## Rollback (RabbitMQ'yu Devre Dışı Bırakma)

```bash
# 1. dev.env / .env içinde
RABBITMQ_ENABLED=false

# 2. Recreate
docker compose up -d backend
docker compose stop backend-worker   # opsiyonel; kalsa bile boş döngüde bekler

# 3. Eski APScheduler aggregator otomatik aktifleşir (her 5dk)
#    Bekleyen rabbitmq_yayinlandi=0 event'ler artık relay'e gitmez ama
#    DB polling aggregator onları aggregate_edildi=True yapacak şekilde
#    işlemeye devam eder (operator_metrik_aggregator_job).
```

Şema geri çekilmez — Faz 2 migration (`a1b2c3d4e5f6`) kolonları kalır ama `RABBITMQ_ENABLED=false` ile yazılmaya devam etmez (sadece `event_uuid` üretimi yeni event'lerde devam eder — bu zararsızdır).

## Test

```bash
cd BackendProje

# Unit testler (RabbitMQ gerekmez)
pytest -m unit

# Broker gerektiren testler (varsa) — manuel çalıştır
docker compose up -d rabbitmq
pytest -m rabbitmq

# Integration (DB gerekir, RabbitMQ gerekmez)
pytest -m integration
```

> `@pytest.mark.rabbitmq` ile işaretli testler default `pytest` çağrılarında çalışmaz; bilinçli olarak `-m rabbitmq` ile veya CI'da broker servisi varken tetiklenir.

## Production Readiness Checklist

İlk production geçişinden önce **mutlaka netleştirilmesi gereken** kararlar:

- [ ] **Broker seçimi**: managed RabbitMQ (CloudAMQP, AWS MQ) > HA cluster > tek node. Tek node yalnızca pilot/staging için.
- [ ] **HA / failover**: cluster'da queue mirroring (`x-queue-type: quorum` veya classic mirror) yapılandırması.
- [ ] **Mesaj kalıcılığı**: queue + mesaj durable (zaten kod tarafında açık), disk yedekleme stratejisi.
- [ ] **Monitoring**: Prometheus exporter (`rabbitmq_prometheus` plugin) + Grafana panelleri (queue depth, consumer lag, publish/ack hızı, connection count).
- [ ] **Alert kuralları**: DLQ derinliği > 0, queue derinliği > eşik, consumer kapalı kalma süresi, publish confirm hata oranı.
- [ ] **Backup / restore**: queue tanımları + policy'ler için `rabbitmqctl export_definitions`, periyodik snapshot.
- [ ] **TLS**: amqps + management UI'da HTTPS; client sertifikası opsiyonel.
- [ ] **Kimlik**: `guest/guest` yerine her servis için ayrı user + minimum vhost izinleri.
- [ ] **Network**: backend ↔ broker yalnızca dahili VPC üzerinden; mgmt UI yalnızca VPN arkasından.
- [ ] **TTL / queue length**: aşırı birikme durumunda `x-message-ttl` veya `x-max-length` politikası.
- [ ] **Schema evolution**: `schema_version=1` → 2 geçişi için consumer tarafında forward-compat plan (bilinmeyen alanları ignore et, kritik alanlar zorunlu).
- [ ] **Worker ölçekleme**: `backend-worker` replica sayısı (queue derinliğine göre). Birden fazla replica varken `prefetch` ayarı tekrar değerlendirilmeli.
- [ ] **Idempotency garantileri**: aggregate işlemi şu an DB'de `aggregate_edildi=True` ile single-source-of-truth; consumer scale-out'ta `SELECT … FOR UPDATE` lock pattern'i değişmez ama hot-row contention'ı izlenmeli.
- [ ] **DLQ replay tooling**: admin endpoint veya CLI script (manuel rabbitmqadmin publish production'a uygun değil).
- [ ] **Migration uygulama**: `compose.yml`'deki `backend-init` `alembic stamp head` kullanıyor; production deploy script'inde `alembic upgrade head` çağırılmalı, aksi takdirde yeni migration'lar schema'ya uygulanmaz.

## Sık Karşılaşılan Sorunlar

| Belirti | Olası neden | Çözüm |
|---|---|---|
| `rabbitmq_yayinlandi` her event için 0 kalıyor | `RABBITMQ_ENABLED=false` veya backend recreate edilmemiş | `dev.env` kontrolü; `docker compose up -d backend` |
| Worker logunda sürekli `RabbitMQ bağlanılamadı` | RabbitMQ servisi down veya URL yanlış | `docker compose ps rabbitmq`; `RABBITMQ_URL` ortam değişkeni |
| Queue dolu, consumer boşaltmıyor | `backend-worker` down veya `RABBITMQ_ENABLED=false` | `docker compose ps backend-worker`; logları kontrol |
| Aynı event iki kez işleniyor gibi | Vardiya metrikleri sayaçları beklenenden yüksek; consumer log'unda "DB'de zaten aggregate" yoksa lock kaçışı olabilir | DB'de `gorev_performans_eventleri.aggregate_edildi` değerlerini doğrula; consumer FOR UPDATE pattern'i çalışıyor mu |
| DLQ büyüyor | Parse hatası veya silinmiş event'ler için mesaj geliyor | `rabbitmqadmin get queue=...dlq` ile sebep tespit; gerekirse purge |
| Backend yeni dependency için pika `ModuleNotFoundError` | `requirements.txt` değişti ama image rebuild edilmedi | `docker compose build backend backend-worker` |
