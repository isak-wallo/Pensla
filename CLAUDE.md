# Pensla — magisk målarbok för barn

En enkel färgläggningsapp (PWA) för en gammal Android-platta. Syskon till
Kludda (fri ritning, https://github.com/isak-wallo/Kludda) och bygger på samma
skal. Språk i appen och i koden (kommentarer, knappnamn) är **svenska**.

## Vad appen gör

Lugn ton som syskonet Poppa (https://github.com/isak-wallo/Poppa): mjuka
färger, inga ljud, inga poäng, inga val att göra.

- Man ser bara konturerna av en tecknad bild. Penseln **trollar fram själva
  färgbilden** där man målar (alla fingrar, `PENSEL` (28) = radie i
  bildpixlar). Bara det som målas blir målat: inget fylls i av sig självt
  (ägarens val i v49; ifyllnaden med `FYLL_ANDEL`/`startFade` finns i
  git-historiken). Det enda som händer av sig självt är keIWs.
- Panelen har fyra lika stora knappar (sedan v117, ägarens val
  2026-11-25; BÖRJA OM var lite mindre förut), till höger i liggande läge
  (en rad nederst i stående): **◀** föregående bild, **▶** nästa bild
  (byter när fingret SLÄPPS, sedan v114; hålls pilen ensam i 0,7 s byts
  bilden direkt, sedan v117, se nedan), **FÄRGLÄGG** (håll 1,5 s → hela färgbilden
  sveps fram från vänster medan fingret ligger kvar och keIWs poppar upp,
  `fargaHela`; BÖRJA OM ångrar) och **BÖRJA OM** (håll 1 s → bilden töms direkt; sedan
  står "HÅLL INNE LÄNGE FÖR ATT NOLLSTÄLLA ALLA BILDER" i 4 s, och håller
  man då i 4 s töms alla bilder, `glomAllt`; `startHold`/`holdEnd`). Ett
  för kort tryck visar "HÅLL INNE FÖR ATT …" i 5 s, som i Kludda.
  **Knapptrycken (v114, FÄRGLÄGG v115):** ett tryck där en annan knapp
  (pil, FÄRGLÄGG, BÖRJA OM) hållits någon gång är smittat och gör inget
  (`tryck`, `smittad`, `tryckSlut` i app.js). ◀ ▶ byter bild först när
  fingret släpps. FÄRGLÄGG (ägarens val 2026-11-23, som före v114):
  hålls den ensam i 1,5 s färgläggs bilden medan fingret ligger kvar
  (`fargaStartaTid`, `gjord`); kommer en annan knapp före dess, eller
  glider fingret av, försvinner fyllningen och inget färgläggs; släpps den
  tidigare visas tipset. Kommer en annan knapp efter färgläggningen är den
  gjord och den andra knappen smittad (en pil byter inte bild). Glider
  fingret av (`GEST_SLACK`) händer inget. BÖRJA OM är som förut.
  **En pil som hålls (v117, ägarens val 2026-11-25):** ligger pilens
  finger ensamt på HELA skärmen i `PIL_HALL_MS` (0,7 s) byts bilden
  direkt medan fingret ligger kvar, och släppet gör sedan inget mer (`gjord`,
  en bild per hållning, ingen upprepning). En diskret fyllning växer i
  pilen under tiden (samma som FÄRGLÄGG:s, klassen `holding`). Hållningen
  startar bara om inget annat finger finns på skärmen, och varje nytt
  finger var som helst (annan knapp, samma pil, bilden, markeringslagret)
  avbryter den (`pilHallStart`/`pilHallStopp`, en `touchstart`-lyssnare med
  capture på fönstret), liksom ett finger som glider av (`GEST_SLACK`).
  Avbruten hållning = trycket gäller som vanligt: byte vid släpp, om det
  inte är smittat av en annan knapp. Ett finger på bilden smittar alltså
  inte trycket (en hand som vilar på bilden ska inte stoppa pilarna), det
  avbryter bara hållningen. Musen (dator) byter som förut vid klick.
- **Bildbanken:** alla bilder står med fast löpnummer i `bilder.js`
  (`ALLA_BILDER`), men bara de vars nummer står i `AKTIVA` visas och cachas
  (sedan 2026-10-31 vill ägaren ha så många aktiva som möjligt, inte
  runt 20 som förut; nya bilder läggs ändå in inaktiva tills ägaren valt). Alla bilder, även inaktiva,
  får keIWs och testas när de läggs in, så vilken som helst kan aktiveras.
  Ägaren väljer på `galleri.html`
  (https://test.pensla.keiws.com/galleri.html, bara i testmiljön, inte i `ASSETS`):
  konturer och färgbild visas bredvid varandra, kryssa i de aktiva och
  skriv en kommentar vid bilder som behöver kontrolleras; ägaren skickar
  listan (AKTIVA + KONTROLLERA + TA BORT + TA TILLBAKA). Bilder under TA
  BORT förs in i `BORTTAGNA` i `bilder.js` (filerna och numret ligger kvar
  i repot, numret återanvänds aldrig); TA TILLBAKA tas ur `BORTTAGNA`.
  Galleriet har tre flikar efter hur bilden står i appen just nu: Aktiva,
  Inaktiva och Borttagna (v80). Sedan v85 ritas keIWs och kompisarna in i
  färgbilden i galleriet (maskade till sina ytor som i appen,
  `ritaKompisar`), så att ägaren kan granska gömställena där. Ett tryck
  på ett par visar det i helskärm (v86, `visaStor`; ◀ ▶, piltangenter eller
  svep bläddrar i fliken; figurerna ritas in innan bilden visas, v89
  `ritaInKompisar`). En bild som ändras stannar i sin flik med
  en etikett ("blir aktiv", "tas bort" ...) tills listan är införd.
  Galleriet är ett levande dokument: allt i `ALLA_BILDER` visas, grupperat
  i kategorier (`KATEGORIER` i `galleri.html`, t.ex. Båtar, Flygplan,
  Bygge; en ny sort som inte står där blir en egen grupp sist, så lägg in
  den), så nya bilder dyker upp där av sig själva. Ändras `AKTIVA` eller `BORTTAGNA` börjar
  galleriets kryss om från appens lista (gamla sparade val gäller inte
  längre). v77: 63 bilder borttagna (bl.a. alla Copilot-bilder och arkivet),
  alla 54 som blev kvar är aktiva. v62: de gamla
  bilderna i `arkiv/` ligger i banken som nr 75–105 (`verktyg/arkivbild.py`
  skriver `bilder/farg/arkiv-NN-namn.svg/.jpg`). 16 av dem har bara
  konturer (`utanFarg: true`): de syns i galleriet men kan inte väljas, och
  `aktiva.py` vägrar ta med dem. Får en av dem en färgbild senare: lägg den
  som `forlagor/arkiv-NN-namn.jpg`, kör `fargbild.py` på den (troligen med
  `FARGKANTER`), byt `utanFarg` mot en `keiws`-post och behåll numret. För in den i `AKTIVA` och kör
  `python verktyg/aktiva.py`.
  Om ytor-punkten hamnar på en linje (t.ex. efter omspårning) syns inte
  keIWs: ge då flera punkter inne i rutan.
- Bildernas ordning blandas varje gång appen startar (v87, i `PICTURES`)
  men ligger fast medan den är igång, så ◀ ▶ går fram och tillbaka.
- **Det målade sparas i plattan** (v104), även när appen stängs eller en
  ny version laddas. Det målade är alltid färgbildens egna pixlar, så
  varje bild minns bara VILKA pixlar som är målade: en bit per pixel
  (`mask`, 135 kB per bild) och vilka kompisar som är hittade. Allt ligger
  i `sparade` (nyckel = bildens fasta nr) och skrivs till IndexedDB
  (databasen `pensla`, lagret `bilder`) en stund efter en ändring
  (`sparaSnart`, inte mitt i ett penseldrag) och direkt när appen döljs
  eller man byter bild (`sparaNu`). `loadPicture` lägger tillbaka det
  sparade ur färgbilden. BÖRJA OM tar bort bildens minne, nollställ alla
  tar bort allt (`glomAllt`). Appen börjar på bilden som visades sist om
  den är målad (`pensla-senast` i localStorage), annars på en slumpad som
  förut. Första bilden visas när det sparade är inläst (`lasSparat`,
  väntar högst `DB_VANTA_MS`). Utan IndexedDB fungerar appen som förut
  (minns så länge den är öppen).
- **Ny version** (v104, som i Kludda): appen letar efter en ny version när
  man kommer tillbaka till den och var tionde minut (`UPPDATERA_VAR`), men
  laddar inte om mitt i målandet utan när appen döljs eller startskärmen
  visas, och sparar det målade först (`nyVersion`/`laddaOmOmNy`).
  `sw.js` hämtar inte med `cache: 'reload'` vid installationen: Cloudflare
  svarar med `max-age=0, must-revalidate`, så filerna kontrolleras ändå
  mot servern, och med 168 bildfiler vore det dyrt att hämta om allt.
  På den skarpa sidan skickar Cloudflare `/index.html` vidare till `/`, så
  `./index.html` sparas i cachen som ett omdirigerat svar. Ett sådant får
  inte lämnas till en sidladdning (webbläsaren ger ERR_FAILED), så `sw.js`
  packar om det först (`utanOmdirigering`, v113). Testmiljön omdirigerar
  inte (`html_handling: none`).
- **keIWs** (den lilla blå klossfiguren) gömmer sig i varje bild, som krypet
  i Richard Scarrys böcker. Han syns inte från början; när man målat
  `KEIWS_TRAFF` pixlar där han är poppar han upp
  med en liten studs, vinkar, blinkar och blir kvar. BÖRJA OM gömmer honom
  igen. Sedan v83 har han två kompisar, exakta kopior i mintgrönt och
  korallrött (`KOMPISAR` i `app.js`), gömda på andra ställen i bilden. Var
  och en poppar för sig; när barnet målat fram alla tre vinkar de en gång
  till tillsammans (`festTid`). FÄRGLÄGG tar fram alla tre utan fest.
- **Namn:** appen hette Färga fram till v49; repot döptes om till Pensla i
  v50 (den gamla Pages-adressen /Farga/ slutade då fungera). Den lokala
  mappen heter `Pensla` sedan 2026-10-28 (förut `Farga`).
- Bilder (oktober 2026, ny uppsättning): traktor, grävare, sopbil från sidan,
  sopbil snett, traktor 2, två flygplan och två helikoptrar; i v52 kom två
  tåg, två båtar och två stora flygplan (lite mer 3D, se promptmallen); i v55
  raket, två segelbåtar, tre polisbilar och två var av ambulans, betongbil,
  kranbil, buss, brandbil och dumper (33 bilder); i v57 nr 34–47
  (nya 3D-versioner av traktor, grävare, litet flygplan och sopbil, två
  stora flygplan och två raketer), inaktiva tills ägaren valt i galleriet.
  v58: nr 48–74, 27 bilder från Copilot (Designer, 1536×1024, mer
  detaljerade och mättade färger; beskärs till 4:3). De saknar konturer
  runt moln, sol, ränder och kors, så i v61 tas deras konturer även från
  färgkanterna (`FARGKANTER` i `fargbild.py`, se nedan); i v70 spårades de
  om med färgområden (`FARGOMRADEN`, se nedan) eftersom de var hackiga i
  svartvitt. v61: ägaren valde
  47 aktiva bilder i galleriet. v63: nr 106–108, traktorer mellan tecknat
  och verkligt (106–107 Gemini, 108 ChatGPT, se "Mellanstil" nedan), aktiva
  direkt eftersom ägaren valde dem. De gamla svartvita bilderna (kodritade, spårade
  och rena sidor med färgpunkter) och all kod för dem togs bort i v47 —
  finns i git-historiken, och som PNG i `arkiv/` (se `arkiv/README.md`).
  När en bild byts ut flyttas den gamla till `arkiv/` (inte i `ASSETS`).
- Landskapslås, fullscreen, layoutlås/dö-yta, back-fälla och offline-SW är
  kopierade från Kludda — se Kluddas CLAUDE.md för detaljerna.
- Ikonen (`icon-192.png`, `icon-512.png`, maskable) är dumpern ur en av de
  gamla bilderna, på himmelsblått. I `ikoner/` finns fler gamla ikoner
  (inte i `ASSETS`). Byts gärna mot något ur de nya bilderna.

### Hosting (sedan 2026-10-31, som Flappy keIWs)
Repot ligger kvar på GitHub, men GitHub Pages är avstängt (2026-10-31).
- **Test:** https://test.pensla.keiws.com (Cloudflare, env `test` i
  `wrangler.jsonc`, utan sökmotorer). `python verktyg/slapp.py --test`
  **efter varje push** (tar den pushade koden, VERSION som den står i
  `sw.js`). Där ligger också galleriet
  (https://test.pensla.keiws.com/galleri.html) med alla bilder i banken.
  Testversionen heter "Pensla test" (`slapp.py` byter namnet i
  manifest.json och index.html), så att båda går att installera.
- **Skarpt:** https://pensla.keiws.com (`wrangler.jsonc`) byts bara när
  ägaren säger "släpp": `python verktyg/slapp.py --skarpt` (ASSETS från
  origin/main, egna versionsnummer v1, v2 ... i den släppta sw.js, tagg
  `slapp-N`). Inget galleri där. Utan flagga visar skriptet vad som är
  släppt och vad som är nytt.

### Ingen Android-app i det här repot (sedan v112)
Den äldre Android-appen (Capacitor, `com.keiws.pensla`, v90–v111) togs bort
ur repot 2026-11-22 på ägarens besked: `android/`, `verktyg/bygg_apk.py`,
`capacitor.config.json`, `package.json`/`package-lock.json` och
`ANDROID_APP`-grenarna i `app.js`. Den finns i git-historiken (sista commit
med appen: v111-test). Android-appen är Pensla N (repot pensla-native).

### Vektorbilderna till Pensla N (sedan v108)
Pensla N (native-appen, repot pensla-native som bara finns lokalt hos
keIWs) ritar bilderna som vektorer i JSON (format 1, beskrivet överst i
`verktyg/vektorbild.py`). Alla aktiva bilder ligger i `native/bilder/NAMN.json`
(kopieras till pensla-native/app/src/main/assets/bilder/).
- `python verktyg/vektorbild.py --gor NAMN ...` gör JSON-filen (ca 0,5–2 min
  per bild), `--figurer` skriver bara om figurerna, `--kontroll` kontrollerar
  (inga fria ändar, inga luckor, ΔE mot färgbilden, figurerna). Förvald mapp
  är `native/bilder`.
- Figurerna: `GOMSTALLEN` (valda för hand) eller annars webbens platser ur
  bilder.js, som `justera` flyttar upp eller ner (högst 40 px, samma yta)
  så att kroppen syns till 65–80 % (`KROPP_MAL`) och armen till minst 90 %
  (`ARM_MIN`, även ett fel i kontrollen). `python verktyg/matt_figurer.py`
  mäter dem.
- Plattan har 2 GB minne: håll koll på storleken (rapporten
  `docs/utredningar/vektor_v108.md`).

### Arbetsflöde: bara `main`
Jobba direkt på `main` (inga sidgrenar). Commit-meddelanden på svenska.
När en ändring är klar: bumpa VERSION, commit, `git push origin main` och
`python verktyg/slapp.py --test` direkt; ägaren testar på
https://test.pensla.keiws.com och förväntar sig att nya versioner ligger
där.

### VIKTIGT vid uppdatering: bumpa SW-versionen
`sw.js` har `const VERSION = 'vNN'`. Höj den varje gång filer ändras och
pushas, annars fastnar plattan på gammal cache.

## Hemlig markering (v111–v117)

Ägaren märker ut bilder som ska ses över, direkt i appen. Barnets målning
rörs aldrig. Koden: `app.js` (blocket "Hemlig markering"), `index.html`
(`#mark-lage`), `style.css`, `worker/mottagare.js`, `worker/schema.sql`.
Samma funktion finns i Pensla N (se CLAUDE.md där).

- **Gesten:** håll ◀, ▶ och FÄRGLÄGG samtidigt i 3 s (`GEST_MS`; 5 s före
  v116, ägarens val 2026-11-23), utan att
  BÖRJA OM hålls (en hand över hela panelen ger alltså inget). Ordningen
  spelar ingen roll. Lyfts ett finger, glider det av sin knapp (`GEST_SLACK`)
  eller trycks BÖRJA OM börjar tiden om. Sedan v114 byter gesten aldrig
  bild (inte ens kortvarigt), i vilken ordning den än görs och även när
  den avbryts (se "Knapptrycken" ovan). Undantag sedan v117: börjar man
  med en pil och håller den ensam i 0,7 s innan nästa finger kommer, byts
  bilden en gång (pilhållningen). Kommer nästa finger inom 0,7 s (som när
  man sätter ner tre fingrar), eller börjar man med FÄRGLÄGG, byts ingen
  bild hur långsamt resten av gesten än görs. Inget färgläggs,
  utom om FÄRGLÄGG trycks först och hålls ensam i 1,5 s (v115, ägarens
  val; i v114 färglades inget alls). (v111–v113 bytte den första pilen
  bild direkt och den andra gick tillbaka, `foreBild`; det är borttaget.)
- **Läget:** texten "Markera områden som ska ses över" överst i panelen och
  knapparna KLAR och AVBRYT under den (`#mark-panel` ligger precis över
  knapp-panelen; stående: texten på en rad och knapparna bredvid varandra).
  Inget ligger över bilden, så hela bilden går att markera (v113; förut låg
  texten över bildens överkant). Kvittot visas på textens plats. Man målar grovt med fingret
  (flera drag, flera fingrar) i ett eget halvgenomskinligt lager
  (`markCanvas`, magenta). KLAR sparar och skickar, AVBRYT kastar, och båda
  går tillbaka till den vanliga appen. KLAR utan drag = hela bilden. Läget
  stänger sig självt efter 90 s utan beröring och när appen döljs. KLAR och
  AVBRYT agerar när fingret släpps på knappen.
- **Format** (samma i webben, Pensla N och mottagaren):
  ```
  {"id":"16 hex","nr":22,"namn":"Ambulans","drag":[[x0,y0,x1,y1,...],...],
   "bredd":0.05,"tid":"2026-11-22T20:15:03Z","version":"v110-test","plattform":"webb"}
  ```
  Punkterna är normerade 0–1 i bildens koordinater (x mot bredden, y mot
  höjden; i stående vy är bilden roterad men koordinaterna desamma), 3
  decimaler. `bredd` = penselns bredd som andel av bildens höjd. Tak: 20
  drag, 100 punkter per drag, 600 punkter sammanlagt (dragen förenklas med
  Ramer–Douglas–Peucker). `version` tas ur cachens namn (sw.js).
- **Kön:** KLAR lägger markeringen i `pensla-markeringar` i localStorage
  (högst 50) och skickar kön med POST till `api/markering` på samma adress.
  En markering tas ur kön först när mottagaren svarat `sparad` eller
  `ogiltig` (svarshuvudet `X-Pensla-Markering`); annars (inget nät, `stangd`,
  `full`) ligger den kvar och skickas när appen startas nästa gång eller
  nätet kommer tillbaka. Kvittot: "Skickat ✓" eller "Sparat ✓ Skickas senare".
  `sw.js` rör inget under `/api/` och bara GET.
- **Mottagaren** (`worker/mottagare.js`, Worker framför de statiska filerna,
  körs bara för `/api/*`): bara POST med JSON från sidans egen adress
  (Origin), högst 10 kB, bara kända fält, bildnummer som finns i bilder.js,
  namnet slås upp i mottagaren (appens text sparas inte), inget om
  avsändaren sparas. Sparar i D1-tabellen `markering` (kolumnen `miljo` =
  `skarp` eller `test` efter värdnamnet, `hanterad` = 0). Tak: 60 nya per
  dygn och 500 rader sammanlagt, sedan 429 `full` tills någon rensat. Det
  finns ingen adress att läsa på. Svar: 204 `sparad` (även för en dubblett),
  400/403/405/413/415 `ogiltig`, 429 `full`, 503 `stangd` (ingen databas).
- **Databasen** (ägarens val 2026-11-22: EN databas för test och skarpt,
  `miljo` skiljer dem åt). Tills den finns står `d1_databases` som kommentar
  i `wrangler.jsonc`, mottagaren svarar `stangd` och apparna behåller kön.
  Stegen (körs av den som har kontot, inte av verktygen här):
  ```
  npx wrangler@4 d1 create pensla-markeringar
  ```
  Lägg det `database_id` som skrivs ut på BÅDA ställena i `wrangler.jsonc`
  (överst och i env `test`, samma id) och ta bort kommentartecknen runt
  `d1_databases`. Sedan en gång:
  ```
  npx wrangler@4 d1 execute pensla-markeringar --remote --file worker/schema.sql
  ```
  och vanlig publicering (`python verktyg/slapp.py --test`, skarpt när ägaren
  säger "släpp"). Markera som åtgärdad eller rensa (taket 500 räknar alla
  rader):
  ```
  npx wrangler@4 d1 execute pensla-markeringar --remote --command "UPDATE markering SET hanterad = 1 WHERE id = '...'"
  npx wrangler@4 d1 execute pensla-markeringar --remote --command "DELETE FROM markering WHERE hanterad = 1"
  ```
- **Läsa:** `python verktyg/markeringar.py` listar markeringarna per bild och
  ritar en översiktsbild per bild med dragen ovanpå färgbilden i
  `granskning/markeringar/NR-FIL.png` (en markering utan drag ritas som en
  ram). Källor: `--server` (D1 på Cloudflare via `wrangler --remote`, bara
  ohanterade; `--alla` tar alla), `--fil FIL.jsonl` (plattans fil från
  Pensla N), `--adb` (hämtar plattans fil med `adb pull`), `--lokal MAPP
  --konfig FIL` (lokal D1 från `wrangler dev --persist-to`, för prov).
- **Prova lokalt:** kopiera appens filer till en mapp, gör en wrangler-fil
  med `main`, `assets` och `d1_databases` (valfritt id), kör
  `npx wrangler d1 execute pensla-markeringar --local --persist-to MAPP -c FIL
  --file worker/schema.sql` och `npx wrangler dev -c FIL --persist-to MAPP`.
  Med Playwright: riktiga flerfingerhändelser via CDP
  `Input.dispatchTouchEvent` (`touchStart` tar alla fingrar som är nere,
  `touchEnd` bara dem som SLÄPPS). Provet 2026-11-22 står i
  `docs/LAGE-markering.md`.
- **Provet i repot:** `python verktyg/prov_markering.py` (Playwright, riktiga
  flerfingerhändelser, egen liten filserver, inget skickas: anropen till
  `api/markering` fångas i webbläsaren). Provar gesten i olika ordning och
  långsamt, de avbrutna gesterna (bilden som visas och båda grannbilderna
  ska ha 0 pixlars skillnad mot före), läget i sex skärmstorlekar (inget
  över bilden, markering i bildens överkant, KLAR, AVBRYT). `--adress
  https://test.pensla.keiws.com/index.html` provar testmiljön, `--bilder MAPP`
  sparar skärmbilder, `--mapp` provar en annan kopia av appen. Kör det när
  gesten, läget eller knapparnas håll-logik ändras. Mottagaren och kön
  provas inte av det. Sedan v114 provar det också reglerna för knapparna:
  ◀ ▶ FÄRGLÄGG i alla sex ordningar (långsamt, snabbt, öppnat och avbrutet,
  släpp i olika ordning), pil ensam (byter vid släpp, glider av, två
  fingrar), pil eller FÄRGLÄGG + annan knapp (inget händer), FÄRGLÄGG
  ensam (tips, färgläggning vid 1,5 s medan fingret hålls, glider av),
  pil efter att färgläggningen startat (byter inte) och samma med mus
  (`--grupp tre regler`). v115: 677 kontroller i 69 fall; v116 (gesten 3 s,
  med gränsfallen 2,7 s och 2,8–3,2 s): 690 kontroller i 71 fall.
  v117: gruppen `pilhall` (pil som hålls ensam 0,7 s, avbruten av knapp,
  samma pil, finger på bilden före och under, glid av, efter bytet, och
  gesten med tre fingrar inom 0,5 s); de långsamma "tre"-fallen som börjar
  med en pil väntar ett byte till grannbilden, de öppnande långsamma tar
  nästa finger efter 0,5 s.
- I headless Chromium går `touchstart` på knapparna inte att avbryta
  (`cancelable` = false), så webbläsaren skickar också mus-händelser och ett
  klick efter ett tryck. Därför räknas inte ett klick på en pil inom
  `PIL_KLICK_MS` efter ett tryck med fingret (annars byttes två bilder), och
  musdrag i markeringslagret direkt efter ett finger räknas inte.

## Arkitektur (`app.js`)

- **Lager** i bildens storlek (900 px hög, oftast 1200 bred; `setPaperSize`
  byter bredd när en bild i annat format laddas): `lineCanvas` (konturerna, SVG:n), `colorCanvas`
  (facit: färgbilden, syns aldrig), `fillCanvas` (det barnet målat fram,
  vitt annars) och synliga `viewCanvas` som ritar fill + pågående toningar
  + linjer. Bilden passas in utan beskärning; i stående vy roteras den 90°
  (`updateTransform`/`getPaperCoords`).
- **Områden** numreras en gång vid laddning (`labelRegions`, scanline-flood,
  4-grannar). `labels[i]` = områdesnummer (0 = linje). Pixlar med alpha <
  `LINE_ALPHA` räknas som yta så färgen går in under linjens anti-aliasade
  kant. Ytorna behövs bara för keIWs-masken; färgen tas alltid pixel för
  pixel ur färgbilden (`facitPx`, `franFargbild`).
- **Måla**: `stamp`/`stroke` skriver färgbildens pixlar i `fillPx` där
  penseln går, och räknar träffar på keIWs och kompisarna. `checkTouched`
  (`kollaKompisar`) poppar den som nått `KEIWS_TRAFF`. Ritning sker en gång per frame (`requestRender`,
  `dirty`).

## keIWs (`ritaKeiws`, `prepKeiws`, `renderKeiws`)
- Ritas av sina klossar från `keiws.js` (`KEIWS`: stilla, blink och
  vinka-animationen, rektanglar relativt kroppens hörn; kroppen 160 × 160,
  fötterna på y = 204), skalad med `s`. Måtten är kopierade från figurens
  export, ändra dem inte för hand.
- Varje bild i `PICTURES` har `keiws: { x, y, s, ytor }`: (x, y) = mitt under
  fötterna, `ytor` = punkter i de ytor han syns i. Han ritas bara på de
  ytornas pixlar (mask), ovanpå färgen men under linjerna — så det som
  ligger framför (fönsterkarmen, ratten) skymmer honom och han ser ut att
  titta fram bakom det. Stora hyttfönster är bra gömställen, men i små
  fönster (tornfönster, runda ventiler, små hytter) syns han för dåligt —
  flytta då ut honom.
- Vinkarmen (uppe till höger om kroppen, topp på y − 252s) maskas som
  kroppen, så den får inte hamna bakom karm, moln eller tak. Kolla med
  `python verktyg/vinkarm.py [NR...]` (KLIPPS = under 90 % syns);
  `--forslag` föreslår mindre `s`/liten flytt, `--ark FIL.json` ritar
  före/efter-ark i `granskning/granskare/vinka/`. Kroppen ska ändå skymmas
  en bit (ca 65–80 % synlig), annars ser figuren ut att sväva.
- Fötterna: `vinkarm.py` och `verktyg/figurgranskning.py` mäter också hur
  stor del av fötterna som syns och varnar SVÄVAR över 50 % (`FOT_MAX`):
  då står inget framför fötterna och figuren hänger fritt, t.ex. mitt i en
  framruta. Sänk den då så att fönsterkanten, instrumentbrädan eller taket
  döljer fötterna, eller flytta ut den. `python verktyg/figurgranskning.py
  --par` ritar alla aktiva bilder (stilla och vinkande, mått per figur i
  `matt.json`) och listar alla varningar (KLIPPS och SVÄVAR) sist;
  `--forslag FIL.json` ritar föreslagna platser utan att ändra bilder.js.
  Granskningarna: `docs/utredningar/figurgranskning_v107.md` och
  `figurer_v108.md` (v108: 27 figurer flyttade, en SVÄVAR kvar).
  Skripten hittar Chromium själva (`chromium()` i vinkarm.py: Playwrights
  egen, annars `PENSLA_CHROME` eller /opt/pw-browsers) och går på Linux.
- Bildöversynen: `python verktyg/bildoversyn.py [NR...]` räknar glapp,
  lösa streck, små ytor (under 60 px), remsor (dubbla/fransiga konturer)
  och linjeandel per bild och ritar `granskning/oversyn/NAMN.png`
  (`docs/utredningar/bildoversyn.md`, `bilder_v108.md`).
- Kompisarna står i `gron` och `rod` med samma mått (saknas de har bilden
  bara keIWs). De ska titta fram *bakom något*: kroppen i en bakgrundsyta
  (himmel, ruta, kulle, vägg) och fötterna bakom ett riktigt föremål med
  mörk kontur (tak, buske, rotor, stjärtfena, bom, träd) — inte vid en
  godtycklig färgskarv mellan två fält. Undvik grön på grönt och röd på rött.
  `verktyg/gomstallen.py` gör det i två steg:
  1. `python verktyg/gomstallen.py --kandidater NR...` ritar numrerade
     kandidater i `granskning/kompisar/kand-FIL.png` (sparas i
     `kandidater.json`). Titta på dem.
  2. `python verktyg/gomstallen.py --valj NR:keiws=3,gron=7,rod=1 ...`
     skriver valen i bilder.js. `-` behåller platsen, `B` tar keIWs
     nuvarande plats och `@x,y,s` är en egen plats. `OBS … lik ytan i
     färg` betyder dålig kontrast (himlen ger ofta falsklarm, titta själv).
  3. `python verktyg/gomstallen.py --rita NR...` ger förhandsbilder i
     `granskning/kompisar/FIL.png`. Granska dem innan push.
  Gör det för varje ny bild. Alla 62 aktiva gicks igenom för hand i v89.
  Skriptet serverar repots filer direkt till Chrome (ingen http-server).
  `python verktyg/granska_figurer.py webb NR...` ritar granskningsark i
  `granskning/granskare/webb/` (svartvitt | maskat | original) och skriver
  hur stor del av varje figur som syns. Kontrollera att saken framför är en
  egen yta: har busken, trädet eller molnet ett glapp i konturen hänger den
  ihop med himlen och fötterna syns rakt igenom (96–100 % synligt). Moln
  och tak är oftast säkra. v106: 25 figurer flyttades efter granskningen
  i `docs/utredningar/granskning_figurer.md` (hytt bakom ratten, grön på
  grönt, framför motivet).

## Lägga till en ny bild (`verktyg/fargbild.py`)
1. Be Gemini om en tecknad, lekfull färgbild (4:3, wider than tall) med
   mörka konturer runt varje form, där bara konturerna är svarta (däck och
   mörka delar mellangrå), mjuka färger, ingen text eller ram, inga
   personer eller djur. Gemini-chatten räcker, ingen negativ prompt behövs.
   Prompterna ägaren använt finns i "Promptmall" nedan.
2. Lägg den i `forlagor/NAMN.jpg` och kör
   `python verktyg/fargbild.py forlagor/NAMN.jpg` (Pillow, numpy, scipy,
   potrace: `pip install potracer`):
   - Konturerna = pixlar som är tydligt mörkare än sin omgivning (`MORKARE`
     inom `OMGIVNING` px), så även de ljusare linjerna runt moln och sol
     kommer med men inte skuggor och glans inne i ytorna. En linjepixel ska
     också vara nästan det mörkaste inom `NARA` px, annars blir skuggor som
     ligger an mot en linje svarta klumpar. Spåras med potrace till
     `bilder/farg/NAMN.svg`. Färgbilden sparas som `bilder/farg/NAMN.jpg`
     (900 px hög). Från v69 behåller bilden sitt format, t.ex. 16:10 ->
     1440 × 900, och appen tar bredden ur färgbilden. Nästan 4:3 (Geminis
     2400 × 1792) och de äldre 3:2-bilderna i `BESKAR_4_3` beskärs mitt på
     till 4:3 = 1200 × 900, så att deras keIWs-mått stämmer. Klipper
     beskärningen av fordonet: ta bilden ur `BESKAR_4_3`, kör om
     `fargbild.py` (samma förlaga ger samma SVG) och flytta figurerna
     (3:2 → +75 px i x), som för flygplan6, flygplan-stort5, skordetroska
     och traktor7 i v108.
   - Glapp i konturerna gör inget (färgen tas ändå ur färgbilden).
   - Bilder där viktiga former saknar mörk kontur (båten, traktor8–10,
     betongbil4–5, ambulans4–5) står i `FARGKANTER`: där läggs färgkanter
     (Canny i Lab, `KANT_LAG`/`KANT_HOG`) till de mörka linjerna, och
     förlagan skalas först upp till 1800 px hög. Kräver
     `pip install opencv-python-headless`.
   - Copilot-bilderna (nr 48–74) står i `FARGOMRADEN` (v70,
     `omradeslinjer`): mörka linjer med hysteres (`MORK_HOG`/`MORK_LAG`,
     så att linjerna blir hela) plus gränserna mellan färgområden (mean
     shift + k-means, sedan slås grannar ihop så länge Lab-skillnaden är
     under `OMRADE_SKILLNAD` eller området är mindre än `OMRADE_MIN`).
     Ger hela konturer runt ränder, kors, moln och sol. Bra för detaljerade
     bilder med mättade färger där Canny blir hackigt; prova den för nya
     sådana bilder.
   - `TECKNING` (v71, `teckning`; sedan v73 alla Copilot-bilder, före
     `FARGOMRADEN` i main):
     linjer = det som är mörkare än båda sidor (`dalar`, `DAL_HOG`/
     `DAL_LAG`), färgområdena räknas på en bild där linjerna målats bort,
     och allt tunnas till ett skelett som ritas om med jämn bredd
     (`LINJE_BREDD`). Ger jämna linjer, färre skuggstreck och konturer runt
     färgfält som ränder och kors. Tar ~20 s per bild. v72: breda dalar
     (`BRED_DAL`) räknas bara där det är mörkt, så att tjocka fönsterramar
     blir en linje; små hål fylls (`HAL_MAX`) och korta sporrar tas bort
     (`SPORRE`) innan/efter tunningen; små mörka bitar (`LINJE_MIN`) och
     svaga färgskillnader (`TECKNING_SKILLNAD`) räknas som skugga. v74:
     bara smala hål fylls (`HAL_BREDD`, så att små fönster blir kvar), och
     dalar från radie `FARG_DAL` räknas bara där färgen är gråaktig
     (`GRA_MAX`), så att färgade ränder inte blir dubbla linjer.
   - Glans- och skuggstreck som ändå blir kvar tas bort för hand med `BORT`
     i skriptet: `'NAMN': [(x, y), ...]` i 1200-skala; den lilla biten
     (under `BORT_MAX` px) närmast varje punkt tas bort. Skriptet säger till
     om det inte hittar någon bit vid en punkt.
3. Titta på SVG:n (t.ex. öppna den i Playwright och ta en skärmbild).
4. Lägg en post sist i `ALLA_BILDER` i `bilder.js` med nästa lediga
   löpnummer: `{ nr, namn, fil: 'NAMN', keiws: {...} }`. Numren är fasta och
   återanvänds aldrig. Lägg numret i `AKTIVA` om bilden ska synas och kör
   `python verktyg/aktiva.py` (skriver de aktiva bildernas filer i `ASSETS`
   i `sw.js` och bumpar `VERSION`; en ändelse behålls: v108-test → v109-test).
5. Granska: `granskning/` (inte i git) har ett par per bild, konturer och
   färgbild bredvid varandra, så ägaren kan markera det som ska justeras.
6. Testa: måla över bilden i sicksack med Playwright (▶ med `click`, inte
   både touchstart och click — då hoppar den två bilder) och titta på
   skärmbilden: färgen ska komma fram och keIWs kika fram.

### Promptmall
```
A playful cartoon picture-book illustration for small children: <FORDON>
in <MILJÖ>, seen from the side. Landscape format 4:3, wider than tall, the
whole <fordon> visible with space around it.

Style rules (important):
- Bold, clean, smooth outlines in near-black around EVERY shape, all about
  the same thickness. Every area must be fully closed by outlines, no gaps.
- Only the outlines are black. All fill colors are lighter: tires and dark
  parts are medium gray, never black.
- Soft, friendly, slightly muted colors (pastel-like). Gentle soft shading
  inside shapes is fine, but colors never cross an outline, and no dark
  shadows along the outlines.
  (Från v52, lite mer 3D, ersätter raden ovan: "A soft, rounded 3D toy
  look: gentle light gradients and soft highlights give the shapes volume,
  but colors stay light, never cross an outline, and there are no dark
  shadows or dark bands along the outlines." Bilden ses då "from the side
  at a slight three-quarter angle".)
- Cute rounded shapes, cartoon proportions, a bit of detail (windows,
  doors, lights) but no tiny enclosed areas.
- Background: <BAKGRUND>.
- No people, no animals, no text, no frame, no signature, no paper texture.
```

### Mellanstil (v63)
Mittemellan Geminis leksaksstil och Copilots mer verkliga bilder. Ägaren
testade den i flera AI:er 2026-10-21: Gemini gav renast konturer och är
förstahandsval, ChatGPT är alternativet för en lite mer verklig stil.
Blir den för tecknad, byt "halfway between" mot "a bit closer to a
realistic drawing"; blir den för verklig, ta bort "(not chubby, not a toy)".
```
A friendly picture-book illustration for small children, halfway between a
cartoon and a realistic drawing: a modern red farm tractor with a cab, big
back wheels and smaller front wheels, on a dirt road between green fields,
seen from the side at a slight three-quarter angle. Landscape format 4:3,
wider than tall, the whole tractor visible with space around it.

Style rules (important):
- Proportions close to a real modern tractor (not chubby, not a toy), but
  simplified and friendly: smooth rounded edges, clean shapes, no small
  mechanical clutter.
- Bold, clean, smooth outlines in near-black around EVERY shape, all about
  the same thickness. Every area must be fully closed by outlines, no gaps.
  Also outline the clouds, the sun, stripes and any color change.
- Only the outlines are black. All fill colors are lighter: tires and dark
  parts are medium gray, never black.
- A soft 3D look: gentle light gradients and soft highlights give the
  shapes volume, but colors stay light, never cross an outline, and there
  are no dark shadows or dark bands along the outlines. No reflections or
  glare lines on the windows, just a soft light blue.
- A moderate amount of detail (cab windows with a seat and steering wheel,
  exhaust pipe, lights, a step, a grille with a few wide slots, tire treads
  with a few large blocks) but no tiny enclosed areas.
- Background: rolling green hills, a few round trees, a small red barn, a
  wooden fence, light blue sky with a few outlined clouds and an outlined sun.
- No people, no animals, no text, no letters, no logos, no frame, no
  signature, no paper texture.
```

### GPT-stilen (v75–v76), ägarens val för att göra om alla sorter
GPT via Copilot med prompten nedan (här bärgningsbilen; byt fordon och
miljö). Bilderna blir 3:2 (1080 × 720) fast prompten säger 16:10, och de
behåller sitt format i appen (1350 × 900). Spåras med `TECKNING` (lägg
namnet i `FARGOMRADEN`). Nr 113–117 är gjorda så och spårades rent.
Snöbilder: be om ljusblåvit snö med egna konturer, annars försvinner den
mot himlen. Be inte om rutor/plattor i marken (blir linjer).
Alla sorter i den här stilen står i `verktyg/promptdokument.py`, som
skriver `promptar/bilder.md` (till Gemini i Antigravity: agenten sparar
bilderna i `inkorg/`, som git ignorerar) och `promptar/bilder.docx` (till
en chatt). Hjullastare står i `KATEGORIER` (Bygge). Nr 118–124 (v84, ägarens egna:
tre traktorer med höbalsvagn och fyra hjullastare) spårades med `TECKNING`;
keIWs i framrutan, kompisarna från `gomstallen.py`, inaktiva.
```
A playful but slightly more realistic picture-book illustration for small children: a big tow truck driving along a street in a small town, towing a small broken-down car behind it on its lifting arm, seen from the side at a slight three-quarter angle. Realistic proportions: a truck cab with a big windshield and side window, a flat rear deck with a crane boom, a hook and a tow arm, big wheels, but still friendly and softly rounded, not a toy. Landscape format 16:10, wider than tall, the whole truck and the towed car visible with space around them.

Style rules (important):
- Bold, clean, smooth outlines in near-black around EVERY shape, all the same thickness, in the foreground AND the background: houses, trees, street, curb, road markings, clouds, the sun and each sun ray all get the same bold outline. No thin, light or colored lines anywhere.
- Every area must be fully closed by outlines, no gaps. Stripes and warning patterns on the truck are separate areas with their own outlines.
- Only the outlines are black. All fill colors are lighter: tires, the crane boom's dark parts and the grille are medium gray, never black or dark navy.
- Mostly flat colors: each area has one main color with at most a very soft, light highlight. No strong gradients, no shading bands, no dark shadows along outlines, no shadows on the ground under the vehicles.
- A bit more detail than a toy (a roof light bar, side mirrors, headlights, a door, a colored stripe along the cab, the crane boom with a hook and a chain), but no tiny enclosed areas. No grilles with many slots, no ribbed or accordion details, no panel lines, bolts or rivets, no tiny chain links.
- The street is one plain area with a few wide outlined markings, no paving tiles, no cobblestones, no grid of lines on the ground.
- Background: a few simple houses with big windows, a big rounded bush or tree near the truck, light blue sky with a few big puffy clouds and a sun. Keep background objects large and simple, no other vehicles.
- No people, no animals, no text, no letters, no logos, no frame, no signature, no paper texture.
```

## Konventioner
- Svenska i UI och kommentarer. Ingen byggpipeline, inga dependencies.
- Tänk på multi-touch och `stopPropagation` på nya knappar.
