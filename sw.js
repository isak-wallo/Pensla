// Höj VERSION (v1 -> v2 osv.) varje gång du laddar upp nya filer,
// så hämtas och cachas den nya versionen säkert.
const VERSION = 'v81';
const CACHE = 'pensla-' + VERSION;

const ASSETS = [
  './',
  './index.html',
  './style.css',
  './app.js',
  './keiws.js',
  './bilder.js',
  './bilder/farg/sopbil-snett.svg',
  './bilder/farg/sopbil-snett.jpg',
  './bilder/farg/flygplan.svg',
  './bilder/farg/flygplan.jpg',
  './bilder/farg/helikopter.svg',
  './bilder/farg/helikopter.jpg',
  './bilder/farg/tag.svg',
  './bilder/farg/tag.jpg',
  './bilder/farg/tag2.svg',
  './bilder/farg/tag2.jpg',
  './bilder/farg/bat2.svg',
  './bilder/farg/bat2.jpg',
  './bilder/farg/raket.svg',
  './bilder/farg/raket.jpg',
  './bilder/farg/segelbat.svg',
  './bilder/farg/segelbat.jpg',
  './bilder/farg/kranbil2.svg',
  './bilder/farg/kranbil2.jpg',
  './bilder/farg/buss.svg',
  './bilder/farg/buss.jpg',
  './bilder/farg/dumper.svg',
  './bilder/farg/dumper.jpg',
  './bilder/farg/dumper2.svg',
  './bilder/farg/dumper2.jpg',
  './bilder/farg/sopbil3.svg',
  './bilder/farg/sopbil3.jpg',
  './bilder/farg/gravare3.svg',
  './bilder/farg/gravare3.jpg',
  './bilder/farg/traktor8.svg',
  './bilder/farg/traktor8.jpg',
  './bilder/farg/traktor9.svg',
  './bilder/farg/traktor9.jpg',
  './bilder/farg/betongbil4.svg',
  './bilder/farg/betongbil4.jpg',
  './bilder/farg/flygplan-stort6.svg',
  './bilder/farg/flygplan-stort6.jpg',
  './bilder/farg/plogbil2.svg',
  './bilder/farg/plogbil2.jpg',
  './bilder/farg/plogbil3.svg',
  './bilder/farg/plogbil3.jpg',
  './bilder/farg/bargningsbil2.svg',
  './bilder/farg/bargningsbil2.jpg',
  './bilder/farg/bargningsbil3.svg',
  './bilder/farg/bargningsbil3.jpg',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
];

// Installera: cacha allt och ta över direkt
self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(ASSETS); })
      .then(function () { return self.skipWaiting(); })
  );
});

// Aktivera: radera gamla cache-versioner och ta kontroll över sidan
self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(
          keys.filter(function (k) { return k !== CACHE; })
              .map(function (k) { return caches.delete(k); })
        );
      })
      .then(function () { return self.clients.claim(); })
  );
});

// Hämta: cachen först (för blixtsnabb start), hämta sedan tyst i bakgrunden.
// Endast egna GET-anrop hanteras.
self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  // Galleriet (och dess bilder.js?farsk) hämtas alltid färskt från nätet,
  // så att det visar det senaste även där appen är installerad.
  if (url.pathname.endsWith('galleri.html') || url.search === '?farsk') return;

  e.respondWith(
    caches.match(req).then(function (cachedResponse) {
      if (cachedResponse) {
        e.waitUntil(
          fetch(req).then(function (res) {
            if (res && res.ok) {
              var copy = res.clone();
              caches.open(CACHE).then(function (c) { c.put(req, copy); }).catch(function () {});
            }
          }).catch(function () {})
        );
        return cachedResponse;
      }

      return fetch(req)
        .then(function (res) {
          if (res && res.ok) {
            var copy = res.clone();
            caches.open(CACHE).then(function (c) { c.put(req, copy); }).catch(function () {});
          }
          return res;
        })
        .catch(function () {
          return caches.match('./index.html');
        });
    })
  );
});
