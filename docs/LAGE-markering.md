# Läge: hemlig markering (uppdaterat 2026-11-23)

Isak ska kunna märka ut bilder som ska kontrolleras noggrannare: håll ◀, ▶
och FÄRGLÄGG samtidigt i 5 s (BÖRJA OM får inte hållas). Då visas texten
"Markera områden som ska ses över" högst upp och knapparna KLAR och AVBRYT.
Man målar grovt med fingret (flera drag, eget halvgenomskinligt lager i
magenta, det målade rörs inte). KLAR sparar/skickar, AVBRYT kastar, båda går
tillbaka till vanliga appen. Inga drag + KLAR = hela bilden.

Beskrivningen (gest, format, mottagare, tak, Cloudflare-steg, verktyg) står
nu i CLAUDE.md, avsnittet "Hemlig markering", i båda repona. Den här filen
är bara läget.

Allt är bara lokalt: inget pushat, inget utlagt på test eller skarpt, inget
installerat, inga resurser skapade i Cloudflare.

## v113-test (2026-11-23): långsam gest och skylten utanför bilden

Pushat och utlagt på https://test.pensla.keiws.com (inte på den skarpa
sidan). Databasen finns sedan 2026-11-23 (commit a189fe3), så raderna
"allt är bara lokalt" och "databasen finns inte" längre ner gäller inte nu.

- **Långsam gest:** gjordes gesten långsamt (en pil, FÄRGLÄGG, den andra
  pilen först efter mer än 1,5 s) öppnades läget rätt, men GRANNBILDEN (den
  som den första pilen bläddrade till) färglades helt: FÄRGLÄGG-knappens
  hållning startade fast en pil hölls. Nu startar FÄRGLÄGG ingen hållning
  medan en pil hålls (samma regel som i Pensla N v7, `ner()` i PenslaVy.kt).
  Återskapat i v112 (grannbilden 447 137 pixlar ändrade) och borta i v113
  (0 pixlar).
- **Tappat släpp:** knapparna som hålls rensas mot fingrarna som faktiskt
  är nere (`nereKnappar(e)`), så att en pil inte kan se ut att hållas för
  alltid om ett `touchend` skulle utebli (då hade FÄRGLÄGG tystnat).
- **Skylten:** texten "Markera områden som ska ses över" står nu överst i
  panelen med KLAR och AVBRYT under (stående: texten på en rad, knapparna
  bredvid varandra under). Inget ligger över bilden. Kvittot visas på
  textens plats.
- **`/index.html` + service workern = ERR_FAILED (utrett och rättat):** där
  servern skickar `/index.html` vidare till `/` (den skarpa sidan, och
  `wrangler dev` utan `html_handling: none`) sparar `cache.addAll` filen
  `./index.html` som ett omdirigerat svar (`redirected` = true). En
  sidladdning får inte besvaras med ett sådant, så webbläsaren gav
  ERR_FAILED för `/index.html` så fort service workern styrde sidan (även
  utan nät, där reserven är just `./index.html`). `sw.js` packar nu om
  svaret (`utanOmdirigering`). Provat lokalt med en server som omdirigerar
  som Cloudflare: före ERR_FAILED, efter 200 med och utan nät. Testmiljön
  omdirigerar inte och berördes aldrig; den skarpa får rättningen vid nästa
  släpp.
- **Provet ligger nu i repot:** `python verktyg/prov_markering.py` (se
  CLAUDE.md). Senaste körningen mot arbetskopian: 402 kontroller i 27 fall,
  alla som väntat (17 gestfall, 1 fall "som förut", 9 lägen i 6
  skärmstorlekar varav två med Android-UA). Mottagaren och kön provas inte
  av det (oförändrade sedan v112).
- Skärmbilder: `C:\Dropbox\Isak\Program\AI\Claude\keIWspk\Pensla-markering-skarmbilder\webb-v113\`.

Så beter sig gesten när den avbryts (provat, alla med 0 pixlars skillnad på
bilden som visas och på båda grannbilderna):

- Alla tre i 2 s eller 4 s och släpp: inget öppnas, samma bild.
- Bara pilarna i 6 s: inget öppnas, samma bild.
- En pil och FÄRGLÄGG (i vilken ordning som helst), utan den andra pilen:
  inget öppnas och inget färgläggs, men pilen har bläddrat ett steg som ett
  vanligt piltryck.
- Lyft ett finger och sätt ner det igen: tiden börjar om (5 s från att alla
  tre åter hålls).
- Ett finger glider av sin knapp: inget öppnas, samma bild.
- Kvar som det är: trycks FÄRGLÄGG FÖRST och hålls ensam i 1,5 s färgläggs
  bilden som visas (det går inte att skilja från en vanlig färgläggning).
  Börja gesten med en pil.

## Klart

- Webben (v112-test): gest, markeringsläge, kö, mottagare. Provat i
  Chromium, se nedan.
- `verktyg/markeringar.py`: läser `--fil` (JSONL från plattan), `--lokal`
  (lokal D1), `--server` (D1 på Cloudflare) och `--adb`; listar per bild och
  ritar översiktsbilder i `granskning/markeringar/`.
- CLAUDE.md i båda repona.
- Pensla N (versionCode 6, `native-v6`): genomgången mot webben utan
  ändringar i källan (samma text, knappar, format, tak). APK oförändrad:
  `C:\Dropbox\Isak\Program\AI\Claude\keIWs\apk\Pensla-native-v6.apk`,
  sha256 `24628281c4c8a15873cf1278c701242e85794f28ef5d077aa618e68b37f2c9ec`
  (v5 ligger kvar bredvid).

## Ändrat i webben efter provet (v110-test → v111-test)

Provet visade att `touchstart` på knapparna inte går att avbryta i headless
Chromium (`cancelable` = false; likadant i v109, alltså inget nytt med
markeringen). Webbläsaren skickar då också mus-händelser och ett klick
efter ett tryck med fingret. Om det är likadant på en riktig platta är inte
känt. Följderna, och rättningarna:

- Ett tryck på en pil bytte två bilder (touchstart + klick). Nu räknas inte
  ett klick på en pil inom 1 s efter ett tryck med fingret (`PIL_KLICK_MS`).
- Ett tryck i markeringslagret gav två drag (fingret + den härmade musen).
  Nu räknas inte musen inom 1 s efter ett finger.
- KLAR och AVBRYT väntade på webbläsarens klick, som uteblev efter snabba
  drag. Nu agerar de när fingret släpps på knappen (som i Pensla N), och
  glider fingret av händer inget. Klicket är kvar för mus.
- Efter AVBRYT ligger lagret kvar osynligt i 0,35 s, så att ett sent klick
  inte hamnar på knappen under.

## Den äldre Android-appen borttagen (v112-test)

På Isaks besked 2026-11-22, i en egen commit: `android/` (40 filer, bl.a.
SparaPlugin.java), `verktyg/bygg_apk.py`, `capacitor.config.json`,
`package.json`, `package-lock.json` (bara Capacitor stod i dem),
`ANDROID_APP`-grenarna i `app.js` och raderna för `node_modules/` och
`app-webb/` i `.gitignore`. Kvar: `native/bilder/` (vektorbilderna till
Pensla N, inte Capacitor). Hela provet kördes om efteråt.

## Provat (2026-11-22)

Webben i headless Chromium (Playwright) med riktiga flerfingerhändelser
(CDP `Input.dispatchTouchEvent`) mot lokal `wrangler dev` (4.166.0) med
lokal D1, ingenting mot Cloudflare-kontot. Sista körningarna (v111-test,
och v112-test efter att den äldre Android-appen tagits bort): 118 fall, 118
som väntat (108 liggande 1280×800, 10 stående 800×1280). Körningarna innan
föll på de fyra felen ovan och på fel i själva provet.

- Gesten: öppnar efter 5 s i tre ordningsföljder (5,3–5,4 s uppmätt från
  första fingret); 4,3 s öppnar inte; alla fyra knapparna öppnar inte;
  BÖRJA OM tryckt efter 2 s nollställer tiden; FÄRGLÄGG släppt efter 3 s,
  finger som glider av ▶, bara pilarna och FÄRGLÄGG + en pil öppnar inte.
  Samma bild efteråt och inget färglagt (bildens pixlar jämförda) i alla
  fallen. FÄRGLÄGG ensam, kort tryck (tipset), ◀ ▶ med finger (ett steg per
  tryck) och med mus fungerar som förut.
- Läget: texten, var den står, panelen täcker knapparna, KLAR och AVBRYT
  syns, tryck på panelen byter inte bild. Drag ritas under fingret, två
  fingrar samtidigt, mus. Barnets bild orörd av dragen. AVBRYT: inget
  sparat, inget skickat. KLAR utan drag: `drag: []`. KLAR med drag: hörnen
  i datat stämmer med bilden inom 0,003 (liggande och stående, där bilden
  är roterad). 22 drag ger 20; 700 rörelser ger 69 punkter.
- Barnets målning: det sparade (mask och hittade figurer i IndexedDB) är
  bit för bit detsamma före och efter en markering och efter omladdning,
  och penseln fungerar efteråt. Bilden på skärmen skilde bara där en hittad
  figur vinkar.
- Kön: utan nät ("Sparat ✓ Skickas senare", ligger kvar efter omstart utan
  nät, skickas när nätet är tillbaka); mottagaren utan databas (503
  `stangd`, kön behålls även efter omstart, två i kön); dygnstaket (60
  rader, 429 `full`, kön behålls); totaltaket (500 rader, 429 `full`; en
  dubblett av en sparad ger ändå 204); efter rensning skickas kön (3 st) i
  ordning vid nästa start; en ogiltig i kön kastas (400) och nästa skickas.
- Service workern: styr sidan, 175 filer i cachen, inget under `/api/` i
  cachen, inget `/api`-svar kom via den, GET `/api/finns-inte` ger 404 från
  mottagaren och GET `/api/markering` 405.
- Raderna i den lokala databasen lästa tillbaka: namn ur bilder.js, miljö
  `skarp`, dragen som JSON.
- Mottagaren för sig (föregående omgång): 37 fall med giltiga och ogiltiga
  anrop, alla som väntat.
- `verktyg/markeringar.py`: en provfil (5 rader + en trasig + en dubblett +
  ett okänt bildnummer) och den lokala databasen efter provet (11 rader):
  listan och översiktsbilderna granskade för ögat. `--server` och `--adb`
  är inte körda.

Skärmbilder av läget:
`C:\Dropbox\Isak\Program\AI\Claude\keIWs\apk\Pensla-markering-skarmbilder\`
(`markering-liggande.png`, `markering-staende.png`).

Provskripten låg i sessionens scratchpad och kan vara borta. Återskapa:
kopiera appens filer till en mapp `webb`, gör en wrangler-fil med `main`
(worker/mottagare.js), `assets` (`./webb`, bindning `ASSETS`,
`run_worker_first: ["/api/*"]`) och `d1_databases` (bindning `DB`, valfritt
id), kör `worker/schema.sql` med `d1 execute --local --persist-to`, starta
`wrangler dev --persist-to`. Öppna `/` (inte `/index.html`, som
omdirigeras och sedan inte går att ladda om genom service workern). CDP:
`touchStart` tar alla fingrar som är nere, `touchEnd` bara dem som släpps.

## INTE provat

- Ingen riktig enhet: varken webben på en platta eller tre riktiga fingrar.
- Pensla N: ingenting på emulator eller platta (emulatorn var upptagen):
  gesten, läget, filskrivningen, `adb pull`. Inga enhetstester finns
  (JUnit vore ett nytt bibliotek).
- Mot Cloudflare: ingenting (databasen finns inte). `markeringar.py
  --server` och `--adb` är skrivna men inte körda.
- Om `touchstart` går att avbryta på plattans Chrome (se ovan).

## Återstår

1. Granskning, sedan D1-databasen (en annan session): stegen står i
   CLAUDE.md. Isak valde 2026-11-22 EN databas för test och skarpt
   (kolumnen `miljo`).
2. Prova Pensla N v6 på emulator/platta innan den installeras.
3. Push, `slapp.py --test`, prov på plattan.

Kända avvikelser från beställningen: den första pilen byter bild
kortvarigt innan den andra pilen går tillbaka (nettobyte noll); en pil som
trycks medan FÄRGLÄGG hålls avbryter hållningen. Att låta pilarna agera
först vid släpp är inte gjort: då händer inget medan ett barn håller kvar
fingret, och inget alls om fingret glider av, och det måste göras och
provas i båda apparna.

## Frågor till Isak

- Pilarna: godta blinkningen (som nu), eller låta pilarna agera vid släpp?
- Enhetstester i Pensla N kräver JUnit (nytt bibliotek): lägga till?
- ContentProvider (signature-behörighet) så att keIWs Fjärr kan hämta
  filen utan adb: bara ett förslag, inte byggt.
