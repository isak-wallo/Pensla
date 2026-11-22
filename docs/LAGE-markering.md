# Läge: hemlig markering (avbrutet 2026-11-22 ca 21:15, datorn startades om)

Isak ska kunna märka ut bilder som ska kontrolleras noggrannare: håll ◀, ▶
och FÄRGLÄGG samtidigt i 5 s (BÖRJA OM får inte hållas). Då visas texten
"Markera områden som ska ses över" högst upp och knapparna KLAR och AVBRYT.
Man målar grovt med fingret (flera drag, eget halvgenomskinligt lager i
magenta, det målade rörs inte). KLAR sparar/skickar, AVBRYT kastar, båda går
tillbaka till vanliga appen. Inga drag + KLAR = hela bilden.

Allt är bara lokalt: inget pushat, inget utlagt på test eller skarpt, inget
installerat, inga resurser skapade i Cloudflare.

## Format (samma i webb, native och mottagaren)

```
{"id":"16 hex","nr":22,"namn":"Ambulans","drag":[[x0,y0,x1,y1,...],...],
 "bredd":0.05,"tid":"2026-11-22T20:15:03Z","version":"v110-test","plattform":"webb"}
```

Punkter normerade 0–1 (x mot bildens bredd, y mot höjden), 3 decimaler,
`bredd` = penselbredd som andel av bildens höjd. Tak: 20 drag, 100 punkter
per drag, 600 punkter totalt (dragen förenklas med Ramer–Douglas–Peucker).

## Byggt

Pensla (webb), version v110-test i `sw.js`:
- `app.js`: gesten (`gestNer`, `gestUpp`, `gestFlytt`, `gestKoll`) och
  blocket "Hemlig markering" (läget, dragen, kön `pensla-markeringar` i
  localStorage, `skickaKo` vid start). `index.html` (`#mark-lage`) och
  `style.css`.
- `sw.js`: rör inte `/api/`.
- `worker/mottagare.js`: POST `/api/markering` till D1, strikt validering,
  10 kB, högst 60 per dygn och 500 totalt, ingen läsväg, svarshuvudet
  `X-Pensla-Markering: sparad|ogiltig|full|stangd`. Namnet tas ur bilder.js
  i mottagaren (det appen skickar sparas inte). Allt annat än `/api/*` går
  till de statiska filerna.
- `worker/schema.sql`: tabellen `markering`.
- `wrangler.jsonc`: `main` + assets-bindningen `ASSETS` +
  `run_worker_first: ["/api/*"]`. D1-bindningen står UTKOMMENTERAD (topp och
  env test), så publicering fungerar som förut innan databasen finns;
  mottagaren svarar då 503 "stangd" och appen behåller sin kö.
- I Capacitor-appen (`ANDROID_APP`) är `MARK_URL = null`: markeringarna
  blir liggande i kön i localStorage (öppen fråga till Isak).

Pensla N (`..\pensla-native`), versionCode 6 / `native-v6`:
- `Markering.kt` (ny): format, förenkling och filskrivning (append + sync).
- `PenslaVy.kt`: gest och markeringsläge (avsnittet "Hemlig markering").
- Filen: `/sdcard/Android/data/com.keiws.pensla.nativ/files/markeringar.jsonl`
  (appens externa filmapp, ingen behörighet i manifestet), hämtas med
  `adb pull` utan root. Reserv: appens interna mapp (kvittot säger då
  "Sparat ✓ (i appen)").
- APK byggd (inte installerad någonstans):
  `C:\Dropbox\Isak\Program\AI\Claude\keIWs\apk\Pensla-native-v6.apk`
  sha256 `24628281c4c8a15873cf1278c701242e85794f28ef5d077aa618e68b37f2c9ec`.
  `Pensla-native-v5.apk` ligger kvar bredvid (byggskriptet tog bort den,
  jag la tillbaka den eftersom v6 inte är provad på enhet).

## Provat

- `node --check` på `app.js` och `worker/mottagare.js`.
- Statiska filer med och utan worker, lokalt `wrangler dev`, miljöerna
  skarp och test, navigering och no-cors: 40 jämförelser, alla lika
  (status och Content-Type).
- Pensla N kompilerar och bygger med R8 (releasebygget ovan).
- Mottagaren (drag-versionen) mot lokal `wrangler dev` med lokal D1, 37
  fall, alla som väntat: giltig, dubblett, inga drag, native-version, tom
  version, utan namn, påhittat namn (sparas som bilder.js-namnet) och 20
  drag ger 204 "sparad"; okänt fält, fel id, okänd bild, nr som text, udda
  antal tal, tal över 1, text i drag, tomt drag, 21 drag, 101 punkter, över
  600 punkter, drag saknas, fel bredd, fel tid, fri text i version, fel
  plattform, lista, trasig JSON ger 400; 11 kB ger 413; annan eller ingen
  Origin 403; text/plain 415; GET 405; annan /api-väg 404; utan databas
  503 "stangd". Raderna lästes tillbaka ur databasen och såg rätt ut.

## INTE provat (viktigt)

- Webb: gesten och markeringsläget är INTE provade i en webbläsare efter
  omgörningen till frihandsdrag (Playwright med multi-touch var nästa
  steg): 5 s, att ingen bild byts netto, att inget färgläggs, KLAR/AVBRYT,
  kön offline och omsändning vid start, att sw.js inte stör POST.
- Mottagaren, dygnstaket: svaret 429 "full" är inte visat. Provskriptet
  räknade en rad fel (dubbletten ger ingen ny rad), så det stannade på
  exakt 60 rader, som alla sparades. Skicka en till för att se 429.
  Totaltaket 500 är inte heller provat.
- Pensla N: ingenting provat på emulator eller platta (emulatorn var
  upptagen). Inga enhetstester finns i repot (JUnit vore ett nytt bibliotek).
- Tre samtidiga fingrar är inte provat på någon riktig enhet.

## Återstår

1. Prova webben (se ovan) och mottagaren. Provmaterialet låg i sessionens
   scratchpad (`prov\prova_worker.py`, `med-db.json`, `utan-db.json`) och
   kan vara borta efter omstarten: starta då `wrangler dev` på nytt med en
   kopia av wrangler.jsonc där D1-bindningen är med (`--local`,
   `--persist-to`), kör `worker/schema.sql` med `d1 execute --local`.
2. `verktyg/markeringar.py` är INTE skrivet: ska läsa JSONL-filer
   (`--fil`), servern (`--server`, via `wrangler d1 execute ... --remote
   --json`) och gärna `--adb`, lista per bild och rita dragen
   halvgenomskinligt ovanpå `bilder/farg/FIL.jpg` i `granskning/markeringar/`.
3. Avsnitt "Hemlig markering" i CLAUDE.md i båda repona (wrangler.jsonc
   hänvisar dit).
4. Prova Pensla N v6 på emulator/platta innan den installeras.

Kända avvikelser från beställningen: den första pilen byter bild
kortvarigt innan den andra pilen går tillbaka (nettobyte noll); en pil som
trycks medan FÄRGLÄGG hålls avbryter hållningen.

## Cloudflare-steg (inget är kört)

```
npx wrangler@4 d1 create pensla-markeringar
```
Lägg det `database_id` som skrivs ut i `wrangler.jsonc` och ta bort
kommentartecknen runt `d1_databases` (både överst och i env `test`). Sedan:
```
npx wrangler@4 d1 execute pensla-markeringar --remote --file worker/schema.sql
```
och vanlig publicering (`git push origin main`, `python verktyg/slapp.py
--test`, skarpt först när Isak säger "släpp"). Läsa:
```
npx wrangler@4 d1 execute pensla-markeringar --remote --json --command "SELECT * FROM markering WHERE hanterad = 0 ORDER BY mottagen"
```
Markera som åtgärdad: `UPDATE markering SET hanterad = 1 WHERE id = '...'`;
rensa med `DELETE` (taket 500 räknar alla rader).

Varför D1 och inte KV: taken hålls atomiskt i samma INSERT som
skrivningen, allt läses med ett enda kommando, och Isak har redan D1 i
Tidkort. KV är eventuellt konsistent och svår att räkna tak i.

## Frågor till Isak (inte ställda än)

- Pilarna: godta att första pilen byter bild kortvarigt under gesten
  (rekommenderas), eller låta pilarna agera först när de släpps?
- Capacitor-appen: bara kö (som nu), eller skicka till pensla.keiws.com?
- Samma D1-databas för test och skarpt med kolumnen `miljo`
  (rekommenderas), eller två?
- Enhetstester i Pensla N kräver JUnit (nytt bibliotek): lägga till?
- ContentProvider (signature-behörighet) så att keIWs Fjärr kan hämta
  filen utan adb: bara ett förslag, inte byggt.
