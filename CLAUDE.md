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
- Panelen har fem knappar, till höger i liggande läge (en rad nederst
  i stående): **◀** föregående bild, **▶** nästa bild (agerar direkt på
  `touchstart` med `stopPropagation`), **FÄRGLÄGG** (håll 1 s → hela
  färgbilden sveps fram från vänster och keIWs poppar upp, `fargaHela`;
  BÖRJA OM ångrar), de lite mindre **SPARA** (håll 1 s → bilden laddas
  ner som PNG 1200×900 till plattans Hämtade filer, `sparaBild`; knappen
  visar SPARAD ✓ en stund) och **BÖRJA OM** (håll 1 s → SÄKER?, håll 1 s
  igen → bilden töms; samma spärr som Kluddas RENSA). Håll-logiken
  (`startHold`/`holdEnd`) delas av de tre. Ett för kort tryck visar
  "HÅLL INNE FÖR ATT …" i 5 s, som i Kludda.
- **Bildbanken:** alla bilder står med fast löpnummer i `bilder.js`
  (`ALLA_BILDER`), men bara de vars nummer står i `AKTIVA` visas och cachas
  (ägaren vill ha runt 20 aktiva åt gången). Alla bilder, även inaktiva,
  får keIWs och testas när de läggs in, så vilken som helst kan aktiveras.
  Ägaren väljer på `galleri.html`
  (https://isak-wallo.github.io/Pensla/galleri.html, inte i `ASSETS`):
  konturer och färgbild visas bredvid varandra, kryssa i de aktiva och
  skriv en kommentar vid bilder som behöver kontrolleras; ägaren skickar
  listan (AKTIVA + KONTROLLERA + TA BORT). Bilder under TA BORT förs in i
  `BORTTAGNA` i `bilder.js`: de försvinner ur galleriet men filerna och
  numret ligger kvar i repot (numret återanvänds aldrig).
  Galleriet är ett levande dokument: allt i `ALLA_BILDER` visas, grupperat
  efter typ, så nya bilder dyker upp där av sig själva. v62: de gamla
  bilderna i `arkiv/` ligger i banken som nr 75–105 (`verktyg/arkivbild.py`
  skriver `bilder/farg/arkiv-NN-namn.svg/.jpg`). 16 av dem har bara
  konturer (`utanFarg: true`): de syns i galleriet men kan inte väljas, och
  `aktiva.py` vägrar ta med dem. Får en av dem en färgbild senare: lägg den
  som `forlagor/arkiv-NN-namn.jpg`, kör `fargbild.py` på den (troligen med
  `FARGKANTER`), byt `utanFarg` mot en `keiws`-post och behåll numret. För in den i `AKTIVA` och kör
  `python verktyg/aktiva.py`.
  Om ytor-punkten hamnar på en linje (t.ex. efter omspårning) syns inte
  keIWs: ge då flera punkter inne i rutan.
- Varje bild minns det man målat så länge appen är öppen
  (`pictureState`/`loadPicture`).
- **keIWs** (den lilla blå klossfiguren) gömmer sig i varje bild, som krypet
  i Richard Scarrys böcker. Han syns inte från början; när man målat
  `KEIWS_TRAFF` pixlar där han är poppar han upp
  med en liten studs, vinkar, blinkar och blir kvar. BÖRJA OM gömmer honom
  igen.
- **Namn:** appen hette Färga fram till v49; repot döptes om till Pensla i
  v50 (den gamla Pages-adressen /Farga/ slutade då fungera). Den lokala
  mappen heter fortfarande `Farga`. Ingen pensla.keiws.com förrän ägaren
  säger till.
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
  färgkanterna (`FARGKANTER` i `fargbild.py`, se nedan). v61: ägaren valde
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
- Hostas via GitHub Pages: `https://isak-wallo.github.io/Pensla/`.
  **Inget byggsteg** — commit + push är driftsättning.

### Arbetsflöde: bara `main`
Jobba direkt på `main` (inga sidgrenar). Commit-meddelanden på svenska.
Ägaren testar från GitHub Pages och förväntar sig att nya versioner ligger
ute.

### VIKTIGT vid uppdatering: bumpa SW-versionen
`sw.js` har `const VERSION = 'vNN'`. Höj den varje gång filer ändras och
pushas, annars fastnar plattan på gammal cache.

## Arkitektur (`app.js`)

- **Lager** i 1200×900: `lineCanvas` (konturerna, SVG:n), `colorCanvas`
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
  penseln går, och räknar träffar på keIWs. `checkTouched` poppar honom
  när `KEIWS_TRAFF` nåtts. Ritning sker en gång per frame (`requestRender`,
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
  titta fram bakom det. Hyttfönster är bra gömställen.

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
     (1200 × 900, beskärs mitt på till 4:3).
   - Glapp i konturerna gör inget (färgen tas ändå ur färgbilden).
   - Bilder där viktiga former saknar mörk kontur (Copilot-bilderna, båten)
     står i `FARGKANTER`: där läggs färgkanter (Canny i Lab, `KANT_LAG`/
     `KANT_HOG`) till de mörka linjerna, och förlagan skalas först upp till
     2400 px bred. Kräver `pip install opencv-python-headless`.
   - Glans- och skuggstreck som ändå blir kvar tas bort för hand med `BORT`
     i skriptet: `'NAMN': [(x, y), ...]` i 1200-skala; den lilla biten
     (under `BORT_MAX` px) närmast varje punkt tas bort. Skriptet säger till
     om det inte hittar någon bit vid en punkt.
3. Titta på SVG:n (t.ex. öppna den i Playwright och ta en skärmbild).
4. Lägg en post sist i `ALLA_BILDER` i `bilder.js` med nästa lediga
   löpnummer: `{ nr, namn, fil: 'NAMN', keiws: {...} }`. Numren är fasta och
   återanvänds aldrig. Lägg numret i `AKTIVA` om bilden ska synas och kör
   `python verktyg/aktiva.py` (skriver de aktiva bildernas filer i `ASSETS`
   i `sw.js` och bumpar `VERSION`).
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

## Konventioner
- Svenska i UI och kommentarer. Ingen byggpipeline, inga dependencies.
- Tänk på multi-touch och `stopPropagation` på nya knappar.
