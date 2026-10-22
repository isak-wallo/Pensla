// Höj VERSION (v1 -> v2 osv.) varje gång du laddar upp nya filer,
// så hämtas och cachas den nya versionen säkert.
const VERSION = 'v77';
const CACHE = 'pensla-' + VERSION;

const ASSETS = [
  './',
  './index.html',
  './style.css',
  './app.js',
  './keiws.js',
  './bilder.js',
  './bilder/farg/traktor.svg',
  './bilder/farg/traktor.jpg',
  './bilder/farg/gravare.svg',
  './bilder/farg/gravare.jpg',
  './bilder/farg/sopbil.svg',
  './bilder/farg/sopbil.jpg',
  './bilder/farg/sopbil-snett.svg',
  './bilder/farg/sopbil-snett.jpg',
  './bilder/farg/traktor2.svg',
  './bilder/farg/traktor2.jpg',
  './bilder/farg/flygplan.svg',
  './bilder/farg/flygplan.jpg',
  './bilder/farg/flygplan2.svg',
  './bilder/farg/flygplan2.jpg',
  './bilder/farg/helikopter.svg',
  './bilder/farg/helikopter.jpg',
  './bilder/farg/helikopter2.svg',
  './bilder/farg/helikopter2.jpg',
  './bilder/farg/tag.svg',
  './bilder/farg/tag.jpg',
  './bilder/farg/tag2.svg',
  './bilder/farg/tag2.jpg',
  './bilder/farg/bat.svg',
  './bilder/farg/bat.jpg',
  './bilder/farg/bat2.svg',
  './bilder/farg/bat2.jpg',
  './bilder/farg/flygplan-stort.svg',
  './bilder/farg/flygplan-stort.jpg',
  './bilder/farg/flygplan-stort2.svg',
  './bilder/farg/flygplan-stort2.jpg',
  './bilder/farg/raket.svg',
  './bilder/farg/raket.jpg',
  './bilder/farg/segelbat.svg',
  './bilder/farg/segelbat.jpg',
  './bilder/farg/segelbat2.svg',
  './bilder/farg/segelbat2.jpg',
  './bilder/farg/polisbil2.svg',
  './bilder/farg/polisbil2.jpg',
  './bilder/farg/polisbil3.svg',
  './bilder/farg/polisbil3.jpg',
  './bilder/farg/ambulans.svg',
  './bilder/farg/ambulans.jpg',
  './bilder/farg/betongbil2.svg',
  './bilder/farg/betongbil2.jpg',
  './bilder/farg/kranbil.svg',
  './bilder/farg/kranbil.jpg',
  './bilder/farg/kranbil2.svg',
  './bilder/farg/kranbil2.jpg',
  './bilder/farg/buss.svg',
  './bilder/farg/buss.jpg',
  './bilder/farg/buss2.svg',
  './bilder/farg/buss2.jpg',
  './bilder/farg/brandbil2.svg',
  './bilder/farg/brandbil2.jpg',
  './bilder/farg/dumper.svg',
  './bilder/farg/dumper.jpg',
  './bilder/farg/dumper2.svg',
  './bilder/farg/dumper2.jpg',
  './bilder/farg/flygplan-stort3.svg',
  './bilder/farg/flygplan-stort3.jpg',
  './bilder/farg/flygplan-stort4.svg',
  './bilder/farg/flygplan-stort4.jpg',
  './bilder/farg/sopbil3.svg',
  './bilder/farg/sopbil3.jpg',
  './bilder/farg/sopbil4.svg',
  './bilder/farg/sopbil4.jpg',
  './bilder/farg/flygplan3.svg',
  './bilder/farg/flygplan3.jpg',
  './bilder/farg/flygplan4.svg',
  './bilder/farg/flygplan4.jpg',
  './bilder/farg/flygplan5.svg',
  './bilder/farg/flygplan5.jpg',
  './bilder/farg/gravare2.svg',
  './bilder/farg/gravare2.jpg',
  './bilder/farg/gravare3.svg',
  './bilder/farg/gravare3.jpg',
  './bilder/farg/traktor3.svg',
  './bilder/farg/traktor3.jpg',
  './bilder/farg/traktor4.svg',
  './bilder/farg/traktor4.jpg',
  './bilder/farg/raket2.svg',
  './bilder/farg/raket2.jpg',
  './bilder/farg/raket3.svg',
  './bilder/farg/raket3.jpg',
  './bilder/farg/gravare5.svg',
  './bilder/farg/gravare5.jpg',
  './bilder/farg/flygplan6.svg',
  './bilder/farg/flygplan6.jpg',
  './bilder/farg/raddningsbat.svg',
  './bilder/farg/raddningsbat.jpg',
  './bilder/farg/traktor8.svg',
  './bilder/farg/traktor8.jpg',
  './bilder/farg/traktor9.svg',
  './bilder/farg/traktor9.jpg',
  './bilder/farg/traktor10.svg',
  './bilder/farg/traktor10.jpg',
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
  if (new URL(req.url).origin !== self.location.origin) return;

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
