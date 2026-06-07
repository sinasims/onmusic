const CACHE_NAME = 'onritm2-cache-v1';
const OFFLINE_URL = '/offline/';

const PRECACHE_URLS = [
  '/',
  OFFLINE_URL,
  '/static/css/tailwind.css?v=2',
  '/static/css/style.css?v=2',
  '/static/js/script-django.js',
  '/static/aos.js',
  '/static/lucide.js',
  '/static/aos.css',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request).catch(() => {
      if (event.request.destination === 'image') return caches.match('/static/images/placeholder.svg');
    }))
  );
});
