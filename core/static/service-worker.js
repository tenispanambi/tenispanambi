const CACHE = "tenis-panambi-v1";

const FILES = [
    "/",
    "/ranking/",
    "/calendario/",
    "/torneios-historico/",
    "/estatisticas-championship/",
    "/champ-duplas/selos/",
    "/static/manifest.json",
    "/static/img/logo.png",
    "/static/img/pwa/icon-192.png",
    "/static/img/pwa/icon-512.png"
];

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE).then(cache => cache.addAll(FILES))
    );
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys
                    .filter(key => key !== CACHE)
                    .map(key => caches.delete(key))
            );
        })
    );
});

self.addEventListener("fetch", event => {
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});