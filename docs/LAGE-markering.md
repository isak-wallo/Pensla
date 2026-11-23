# Läge: hemlig markering (uppdaterat 2026-11-23)

Isak ska kunna märka ut bilder som ska kontrolleras noggrannare: håll ◀, ▶
och FÄRGLÄGG samtidigt i 3 s (5 s före v116; BÖRJA OM får inte hållas). Då visas texten
"Markera områden som ska ses över" högst upp och knapparna KLAR och AVBRYT.
Man målar grovt med fingret (flera drag, eget halvgenomskinligt lager i
magenta, det målade rörs inte). KLAR sparar/skickar, AVBRYT kastar, båda går
tillbaka till vanliga appen. Inga drag + KLAR = hela bilden.

Beskrivningen (gest, format, mottagare, tak, Cloudflare-steg, verktyg) står
nu i CLAUDE.md, avsnittet "Hemlig markering", i båda repona. Den här filen
är bara läget.

Allt är bara lokalt: inget pushat, inget utlagt på test eller skarpt, inget
installerat, inga resurser skapade i Cloudflare.

## v116-test (2026-11-23): gesten 3 s

Isaks val: gesten (◀, ▶ och FÄRGLÄGG samtidigt) öppnar markeringen efter
3 s i stället för 5 s (`GEST_MS` i app.js). Tipset (5 s) och FÄRGLÄGG:s
1,5 s är som förut. Samma ändring i Pensla N v11.

- Provet (`verktyg/prov_markering.py`, lokalt): 690 kontroller i 71 fall,
  0 fel. Tiderna i provet är anpassade till 3 s, och två nya gränsfall:
  alla tre i 2,7 s och släpp (öppnar inte, inte öppet efter 2,5 s) och
  öppnar mellan 2,8 och 3,2 s.

## v115-test (2026-11-23): FÄRGLÄGG som förut

Isaks svar på v114: FÄRGLÄGG ska vara som förut, inte vid släpp. Hålls
FÄRGLÄGG ensam i 1,5 s färgläggs bilden medan fingret ligger kvar. Trycks
en annan knapp före 1,5 s, eller glider fingret av, försvinner fyllningen
och inget färgläggs (0 pixlar). Kort tryck och släpp före 1,5 s ger tipset.
Trycks en annan knapp efter att färgläggningen startat är den gjord, och
den andra knappen är smittad (en pil byter inte bild). Pilarna är som i
v114 (vid släpp). BÖRJA OM:s hållning tas inte över av FÄRGLÄGG: "Ja,
okej". Samma regler i Pensla N v10.

- Provet (`verktyg/prov_markering.py`, lokalt): 677 kontroller i 69 fall,
  0 fel. Fallen där FÄRGLÄGG hålls ensam först i mer än 1,5 s kontrollerar
  nu att bilden färgläggs och att pilarna inte byter bild; nya fall:
  FÄRGLÄGG + pil eller BÖRJA OM före 1,5 s (0 pixlar även när FÄRGLÄGG
  hålls kvar till 3 s), pil efter att färgläggningen startat, FÄRGLÄGG
  som glider av före 1,5 s.

## v114-test (2026-11-23): knapptryck vid släpp

Isaks beslut: gesten ska aldrig ge vanliga effekter. Pushat och utlagt på
https://test.pensla.keiws.com (inte på den skarpa sidan). Samma regler i
Pensla N v9.

- **Pilarna:** byter bild först när fingret SLÄPPS på pilen, och bara om
  ingen annan knapp (pil, FÄRGLÄGG, BÖRJA OM) har hållits någon gång under
  samma tryck. Ingen hålltid. Glider fingret av pilen (`GEST_SLACK`) byts
  inget. Två fingrar på samma pil = ett tryck (ett steg när det sista
  släpps). Tillbakagången `foreBild` är borttagen.
- **FÄRGLÄGG:** verkar också vid släpp (valt framför att ångra en påbörjad
  färgläggning pixel för pixel, som hade krävt att masken, figurerna,
  animationen och det sparade i IndexedDB återställdes). Fyllningen växer i
  knappen som förut; släpps den efter 1,5 s färgläggs bilden, släpps den
  tidigare kommer tipset. Har en annan knapp hållits under trycket
  försvinner fyllningen och inget händer vid släpp (varken tips eller
  färgläggning). Det barnet märker: färgen sveps fram när fingret lyfts i
  stället för medan det hålls; den som håller kvar ser fyllningen stå full
  tills fingret lyfts.
- **BÖRJA OM** och gesten/läget i övrigt oförändrade. Följd av att
  FÄRGLÄGG inte längre använder den gemensamma hålltimern: trycks
  FÄRGLÄGG medan BÖRJA OM hålls fortsätter BÖRJA OM:s hållning (förut tog
  FÄRGLÄGG över den).
- Mus: klick på pilarna (vid släpp, som förut), FÄRGLÄGG som med fingret.
  Härmade musklick inom 1 s efter ett finger på en knapp räknas inte.
- **Provet:** `verktyg/prov_markering.py`, 644 kontroller i 66 fall, alla
  som väntat (39 nya fall: ◀ ▶ FÄRGLÄGG i alla sex ordningar långsamt och
  snabbt, öppnat och avbrutet med släpp i olika ordning, FÄRGLÄGG ensam
  först, alla tre i samma ögonblick; pil ensam, pil + annan knapp,
  FÄRGLÄGG + annan knapp, FÄRGLÄGG ensam, mus). Alla avbrutna gester: 0
  pixlars skillnad på bilden som visas och båda grannarna, inget tips.
  Provet fäller v113 (FÄRGLÄGG först i 2 s + pilarna: 233 564 pixlar
  färglagda; ▶ hålls: bilden byts direkt).
- Skärmbilder: `C:\Dropbox\Isak\Program\AI\Claude\keIWspk\Pensla-markering-skarmbilder\webb-v114\`.

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
- Lyft ett finger och sätt ner det igen: tiden börjar om (3 s från att alla
  tre åter hålls).
- Ett finger glider av sin knapp: inget öppnas, samma bild.
- Kvar som det är: trycks FÄRGLÄGG FÖRST och hålls ensam i 1,5 s färgläggs
  bilden som visas (det går inte att skilja från en vanlig färgläggning).
  Börja gesten med en pil. (I v114 färglades inget; sedan v115 är det som
  här igen, Isaks val.)

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

Kända avvikelser från beställningen (v113, åtgärdade i v114 och Pensla N
v9 genom att pilarna och FÄRGLÄGG verkar vid släpp): den första pilen bytte
bild kortvarigt innan den andra pilen gick tillbaka; FÄRGLÄGG ensam först
färglade bilden.

## Frågor till Isak

- Enhetstester i Pensla N kräver JUnit (nytt bibliotek): lägga till?
- ContentProvider (signature-behörighet) så att keIWs Fjärr kan hämta
  filen utan adb: bara ett förslag, inte byggt.
