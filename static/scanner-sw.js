// scanner-sw.js
// Service Worker for RFID Mobile Scanner
// Version: 2025-09-13-v1

const CACHE_NAME = 'rfid-scanner-v1';
const OFFLINE_URL = '/offline';

// Resources to cache for offline functionality
const CACHE_URLS = [
    '/',
    '/scan',
    '/static/scanner-manifest.json',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Install event - cache resources
self.addEventListener('install', event => {
    console.log('[ServiceWorker] Install');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[ServiceWorker] Pre-caching offline page');
                return cache.addAll(CACHE_URLS);
            })
            .then(() => {
                return self.skipWaiting();
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('[ServiceWorker] Activate');

    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[ServiceWorker] Removing old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
    console.log('[ServiceWorker] Fetch:', event.request.url);

    if (event.request.method !== 'GET') {
        return;
    }

    // Handle API requests
    if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    // If online, cache successful API responses
                    if (response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(event.request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // If offline, try to serve from cache
                    return caches.match(event.request)
                        .then(cachedResponse => {
                            if (cachedResponse) {
                                return cachedResponse;
                            }
                            // Return offline API response
                            return new Response(
                                JSON.stringify({
                                    success: false,
                                    message: 'Offline - data not available',
                                    offline: true
                                }),
                                {
                                    status: 503,
                                    statusText: 'Service Unavailable',
                                    headers: { 'Content-Type': 'application/json' }
                                }
                            );
                        });
                })
        );
        return;
    }

    // Handle page requests
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version or fetch from network
                return response || fetch(event.request);
            })
            .catch(() => {
                // If both cache and network fail, show offline page
                if (event.request.destination === 'document') {
                    return caches.match(OFFLINE_URL);
                }
            })
    );
});

// Background sync for offline scans
self.addEventListener('sync', event => {
    if (event.tag === 'offline-scans') {
        console.log('[ServiceWorker] Background sync: offline-scans');
        event.waitUntil(syncOfflineScans());
    }
});

// Sync offline scans when connection is restored
async function syncOfflineScans() {
    try {
        // Get offline scans from IndexedDB
        const offlineScans = await getOfflineScans();

        for (const scan of offlineScans) {
            try {
                const response = await fetch('/api/sync/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(scan)
                });

                if (response.ok) {
                    await removeOfflineScan(scan.id);
                    console.log('[ServiceWorker] Synced offline scan:', scan.id);
                }
            } catch (error) {
                console.error('[ServiceWorker] Failed to sync scan:', scan.id, error);
            }
        }

        // Notify app of sync completion
        self.clients.matchAll().then(clients => {
            clients.forEach(client => {
                client.postMessage({
                    type: 'SYNC_COMPLETE',
                    synced: offlineScans.length
                });
            });
        });

    } catch (error) {
        console.error('[ServiceWorker] Background sync failed:', error);
    }
}

// IndexedDB helpers for offline storage
async function getOfflineScans() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('RFIDScanner', 1);

        request.onerror = () => reject(request.error);

        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['offlineScans'], 'readonly');
            const store = transaction.objectStore('offlineScans');
            const getAllRequest = store.getAll();

            getAllRequest.onsuccess = () => resolve(getAllRequest.result);
            getAllRequest.onerror = () => reject(getAllRequest.error);
        };

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('offlineScans')) {
                const store = db.createObjectStore('offlineScans', { keyPath: 'id' });
                store.createIndex('timestamp', 'timestamp', { unique: false });
            }
        };
    });
}

async function removeOfflineScan(scanId) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('RFIDScanner', 1);

        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['offlineScans'], 'readwrite');
            const store = transaction.objectStore('offlineScans');
            const deleteRequest = store.delete(scanId);

            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = () => reject(deleteRequest.error);
        };
    });
}

// Push notifications for scan alerts
self.addEventListener('push', event => {
    console.log('[ServiceWorker] Push received');

    if (!event.data) {
        return;
    }

    const data = event.data.json();

    const options = {
        body: data.body || 'New scan notification',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: data.data || {},
        actions: [
            {
                action: 'view',
                title: 'View Details',
                icon: '/static/icons/view-action.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/icons/dismiss-action.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'RFID Scanner', options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
    console.log('[ServiceWorker] Notification click received');

    event.notification.close();

    if (event.action === 'view') {
        // Open the app to view details
        event.waitUntil(
            clients.openWindow('/scan')
        );
    }
});

// Message handling for communication with main app
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

console.log('[ServiceWorker] Loaded');