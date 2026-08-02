// LCE - Leader Chiffre Entreprise - Service Worker
const CACHE_NAME = 'lce-cache-v2';
const STATIC_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/admin/css/style.css',
  '/static/js/main.js',
  '/static/admin/js/main.js',
  '/static/images/lc.JPG',
  '/static/manifest.json',
  '/offline',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.css',
  'https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.js',
];

// Installation - Mise en cache
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activation - Nettoyage anciens caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// Stratégie Network First + Cache Fallback
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/admin') || event.request.url.includes('/api/')) {
    // Admin = réseau uniquement
    event.respondWith(fetch(event.request).catch(() => caches.match('/offline')));
    return;
  }
  event.respondWith(
    fetch(event.request).then((response) => {
      const clone = response.clone();
      caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
      return response;
    }).catch(() => {
      return caches.match(event.request).then((cached) => cached || caches.match('/offline'));
    })
  );
});

// ========== NOTIFICATIONS PUSH ==========

self.addEventListener('push', (event) => {
  if (!event.data) return;
  try {
    const data = event.data.json();
    const options = {
      body: data.body || '',
      icon: data.icon || '/static/images/lc.JPG',
      badge: data.badge || '/static/images/lc.JPG',
      vibrate: data.vibrate || [200, 100, 200],
      tag: data.tag || 'lce-notification',
      renotify: data.renotify || false,
      requireInteraction: data.requireInteraction || true,
      silent: false,
      data: {
        url: data.url || '/admin/inscriptions',
        type: data.type || 'inscription',
      },
      actions: data.actions || [
        { action: 'view', title: 'Voir l\'inscription' },
        { action: 'close', title: 'Fermer' },
      ],
    };
    event.waitUntil(self.registration.showNotification(data.title || 'LCE Notification', options));
  } catch (e) {
    console.error('[SW] Push error:', e);
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action === 'close') return;
  const url = event.notification.data?.url || '/admin/inscriptions';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(url) && 'focus' in client) {
          return client.focus();
        }
      }
      return clients.openWindow(url);
    })
  );
});

// Notification de souscription réussie
self.addEventListener('pushsubscriptionchange', () => {
  // Géré par le backend
});