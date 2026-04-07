// Service Worker — Offline fallback only
const CACHE_NAME = 'depo-terminal-v1';

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      cache.addAll(['/terminal/gorevler'])
    ).catch(() => {}) // Offline fallback cache failure is OK
  );
  self.skipWaiting();
});

self.addEventListener('activate', () => self.clients.claim());

self.addEventListener('fetch', (e) => {
  // API isteklerini cache'leme — her zaman network'ten al
  if (e.request.url.includes('/api/')) return;

  e.respondWith(
    fetch(e.request).catch(() =>
      caches.match(e.request).then((cached) => {
        if (cached) return cached;

        // HTML fallback'i yalnızca sayfa navigasyonu isteklerine döndür.
        // JS/CSS/font gibi asset isteklerine HTML dönerse tarayıcı
        // içerik tipi uyuşmazlığı nedeniyle uygulamayı açamaz.
        if (e.request.mode === 'navigate') {
          return new Response(
            '<html><body><h2>Bağlantı yok. Lütfen internete bağlanın.</h2></body></html>',
            { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
          );
        }

        // Asset isteği başarısız oldu — SW müdahale etmez, tarayıcı kendi hata akışını yönetir.
        return Response.error();
      })
    )
  );
});
