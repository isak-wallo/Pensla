# Figurgranskning, Pensla v107

Datum: 2026-11-19. Granskningen gjordes med ögonen på renderade ark. Inget i appen eller i `bilder.js` är ändrat.

Om rubrikerna: ingen rubrik avslöjar var någon figur gömmer sig. Rubriker märkta **(spoilerfri)** har spoilerfritt innehåll. Under rubriker märkta **(gömställen i texten)** står var figurerna sitter.

## Sammanfattning (spoilerfri)

- Jag har gått igenom **84 aktiva bilder med 252 figurer**, både stilla och vinkande, maskade som i appen.
- **Armen syns i alla 252.** Ingen figur har armen synlig under 90 % (lägst 90 %). Vinkarmen är inget problem i v107.
- **13 figurer är dåliga** (se nedan) och har var sitt nytt förslag. Alla förslag är renderade och kontrollerade: kroppen syns till 65–100 %, armen till 100 % och fötterna till högst 18 %.
- **Det vanligaste felet är att figuren svävar mitt i en framruta eller i en hytt** (7 av 13). Fötterna syns till 93–100 % ovanför instrumentbrädan, eller så går ratten rakt över ansiktet. Resten är en kompis inne i en höbal eller trädkrona (fötterna syns), en kompis som står grön mot en grön kulle, och en röd kompis mot rött (planets nos) eller med en antenn tvärs genom kroppen.
- **Ungefär 25 figurer är svaga men godtagbara.** De listas utan förslag längre ned.
- Det nya måttet **fötter synliga** fångar svävande figurer automatiskt: 17 figurer har mer än 40 % av fötterna synliga, och 7 av de 13 dåliga har mer än 90 %.

## Metod (spoilerfri)

- Nytt skript: `verktyg/figurgranskning.py`. Det använder samma ytnumrering, mask och vinkbild (armen uppe) som `vinkarm.py` (som `labelRegions`/`prepKeiws` i `app.js`). För varje aktiv bild ritar det:
  - hela bilden färdigmålad med alla figurer stilla,
  - samma bild när alla vinkar,
  - en uppförstoring per figur, stilla och vinkande, med andelen synlig kropp (`kr`), arm och fötter (`fot`).
- Mätvärdena hamnar i `matt.json`. Med `--forslag FIL.json` ritas föreslagna platser i stället för dem i `bilder.js`, och `bilder.js` ändras inte.
- Så här körs det:
  - alla aktiva bilder: `python verktyg/figurgranskning.py --par`. Arken hamnar i `granskning/figurgranskning/`, som git redan ignorerar.
  - förslagen: `python verktyg/figurgranskning.py --forslag docs/utredningar/figurgranskning_v107/forslag.json`.
- `granska_figurer.py` har hårdkodade Windows-sökvägar och går inte att köra här, därför ett eget skript. Python-Playwright hittade inte sin egen Chromium-version, så skriptet faller tillbaka på den förinstallerade (`/opt/pw-browsers`, eller `PENSLA_CHROME`).
- Bedömningen följer reglerna i CLAUDE.md:
  - Kroppen ska ligga i en bakgrundsyta, och fötterna ska vara skymda av något med mörk kontur.
  - Figuren ska inte stå framför motivet, inte vara grön på grönt eller röd på rött, och inte sitta i små fönster.
  - Därtill uppdragets krav: armen ska synas, och figuren ska inte sväva eller sitta mitt i en framruta.

Bilder i `docs/utredningar/figurgranskning_v107/` (3,1 MB totalt):
- `oversikt-1.jpg` och `oversikt-2.jpg`: alla 84 bilder färdigmålade med figurerna, i nummerordning.
- `fore-efter-NNN-namn.jpg`: ett ark per förslag, med i dag överst och förslaget under (hel bild stilla, hel bild vinkande och utsnitt per figur).
- `forslag.json`: förslagen i maskinläsbar form, i det format som `figurgranskning.py --forslag` och `vinkarm.py --ark` läser.

## Dåliga figurer med förslag (gömställen i texten)

Formatet är detsamma som i `bilder.js`. Mätvärden: i dag → förslag.

| Nr | Bild | Figur | Problem | I dag | Förslag |
|---|---|---|---|---|---|
| 34 | Stort flygplan 3 | rod | Står på tornet med antennen rakt genom kroppen, tätt intill grön | `{ x: 754, y: 150, s: 0.5 }` | `rod: { x: 1120, y: 258, s: 0.42, ytor: [[1120, 206]] }` (bakom terminalens tak; kr 91 %, fot 0 %) |
| 38 | Flygplan 3 | rod | Röd mot planets röda nos, trängs med grön och keIWs vid cockpit | `{ x: 369, y: 359, s: 0.5 }` | `rod: { x: 1040, y: 130, s: 0.4, ytor: [[1040, 80]] }` (bakom molnet till höger; kr 90 %, fot 18 %) |
| 106 | Traktor 8 | gron | Grön mot grön kulle, inget föremål framför (svävar) | `{ x: 204, y: 304, s: 0.5 }` | `gron: { x: 135, y: 278, s: 0.36, ytor: [[135, 233]] }` (bakom träden till vänster; kr 90 %, fot 0 %) |
| 111 | Ambulans 4 | keiws | Svävar mitt i framrutan, fötterna syns till 99 % | `{ x: 690, y: 450, s: 0.4 }` | `keiws: { x: 700, y: 478, s: 0.4, ytor: [[700, 428]] }` (kvar i rutan men tittar fram över instrumentbrädan; kr 96 %, fot 0 %) |
| 114 | Plogbil 2 | keiws | Svävar i framrutan (fot 100 %), blå mot blått glas, stol och ratt genom honom | `{ x: 834, y: 344, s: 0.386 }` | `keiws: { x: 400, y: 228, s: 0.4, ytor: [[400, 170]] }` (bakom sandlasset på flaket; kr 88 %, fot 0 %) |
| 115 | Plogbil 3 | keiws | Som 114 (fot 100 %) | `{ x: 561, y: 366, s: 0.386 }` | `keiws: { x: 290, y: 248, s: 0.34, ytor: [[290, 206]] }` (bakom det snöiga taket på det gula huset; kr 65 %, fot 0 %) |
| 116 | Bärgningsbil 2 | keiws | Som 114 (fot 100 %), blå i blått glas | `{ x: 276, y: 421, s: 0.42 }` | `keiws: { x: 310, y: 290, s: 0.4, ytor: [[310, 240]] }` (bakom ljusrampen på hyttaket; kr 92 %, fot 0 %) |
| 117 | Bärgningsbil 3 | keiws | Som 114 (fot 100 %) | `{ x: 1092, y: 414, s: 0.386 }` | `keiws: { x: 1000, y: 262, s: 0.4, ytor: [[1000, 212]] }` (bakom ljusrampen på hyttaket; kr 88 %, fot 0 %) |
| 118 | Traktor 11 | rod | Står inne i mittersta höbalen, framför motivet | `{ x: 269, y: 513, s: 0.455 }` | `rod: { x: 730, y: 150, s: 0.4, ytor: [[730, 100]] }` (bakom det lilla molnet; kr 83 %, fot 0 %) |
| 140 | Skördetröska 5 | keiws | Svävar i hytten (fot 93 %) med ratt och stol genom kroppen | `{ x: 476, y: 418, s: 0.42 }` | `keiws: { x: 990, y: 180, s: 0.4, ytor: [[990, 130]] }` (bakom det lilla molnet vid solen; kr 98 %, fot 1 %) |
| 143 | Skördetröska 8 | rod | Mitt i trädkronan, hela figuren syns (fot 100 %) | `{ x: 1450, y: 290, s: 0.5 }` | `rod: { x: 1450, y: 150, s: 0.4, ytor: [[1450, 100]] }` (bakom trädkronan, kroppen mot himlen; kr 82 %, fot 0 %) |
| 145 | Skördetröska 10 | keiws | Ratten går tvärs över ansiktet, fötterna syns till 48 % | `{ x: 615, y: 425, s: 0.45 }` | `keiws: { x: 1058, y: 165, s: 0.4, ytor: [[1058, 115]] }` (bakom det lilla molnet till höger; kr 100 %, fot 16 %) |
| 146 | Skördetröska 11 | keiws | Ratten går tvärs över ansiktet, fötterna syns till 38 % | `{ x: 549, y: 466, s: 0.441 }` | `keiws: { x: 540, y: 140, s: 0.4, ytor: [[540, 90]] }` (bakom molnet ovanför hytten; kr 98 %, fot 2 %) |

Om förslagen:
- I alla förslag syns armen till 100 % när figuren vinkar.
- Förslaget för 115 ger lägst andel synlig kropp (65 %). Det ligger på den nedre gränsen men ser naturligt ut: han tittar fram bakom snötaket.
- För 111 räckte det att sänka keIWs. För plogbilarna, bärgningsbilarna och skördetröskorna går det inte, eftersom ratt och stol står där fötterna skulle döljas. Därför har keIWs flyttats ut ur hytten där.

## Svaga men godtagbara figurer (gömställen i texten)

För de här ges inga förslag. Ta dem i en senare runda om du vill.

- **Står i ett litet fönster med fötterna synliga:**
  - 9 keIWs (fot 100 %)
  - 10 och 11 keIWs (s 0,274, fot 100 %)
  - 12 keIWs (fot 66 %)
  - 4 keIWs (framruta, fot 92 %, men vindrutetorkaren skymmer lite)
  - 46 keIWs (i ett runt fönster, 84 % kropp)
- **I hytten med ratt eller stol över sig, men fötterna dolda:** keIWs i 118, 119, 121, 122, 124 och 129.
- **Står ovanpå något med fötterna synliga:**
  - 128 keIWs på tanklocket (fot 54 %)
  - 134 gron på taket (fot 58 %)
  - 142 keIWs i rutan (fot 71 %)
  - 145 gron på tröskans tak (fot 83 %)
- **Färg mot nästan samma färg:**
  - 13 rod mot det röda skrovet
  - 54 rod mot den röda motorhuven
  - 64 gron ovanför den gröna tröskan
  - 118 gron mot mörkgröna träd
- **Kompisarna står tätt intill varandra:** 127 gron och rod, 133 gron och rod (gron dessutom liten, s 0,28).
- **Övrigt:**
  - 17 gron är liten (s 0,288) och står i vattnet vid fören.
  - 116 rod har bärgningskedjan över kroppen.
  - 120 keIWs och rod är små (s 0,28 och 0,288).

Övriga figurer, ungefär 214, är bra: kroppen ligger i himmel, ruta eller vägg och fötterna är skymda bakom tak, moln, buske, rotor, stege eller instrumentbräda.

## Kort sammanfattning och förslag (spoilerfri)

**Fynd:**
- 84 bilder och 252 figurer är granskade.
- Armen syns i alla vid vinkning (lägst 90 %).
- 13 figurer är dåliga, varav 7 som svävar i framruta eller hytt (fötterna synliga till 93–100 %, eller ratten över ansiktet).
- Ungefär 25 figurer är svaga men godtagbara.
- Alla 13 förslag är renderade: arm 100 %, kropp 65–100 %, fötter högst 18 %.

**Förslag till Isak:**
1. **(Rekommenderas)** För in alla 13 förslag i `bilder.js` som de står i tabellen (`forslag.json`).
2. För bara in de 8 keIWs-förslagen (111, 114–117, 140, 145, 146) nu, och ta kompisarna (34, 38, 106, 118, 143) senare.
3. Behåll keIWs i hytterna men sänk honom så att fötterna döljs bakom instrumentbrädan (som för 111). Det kräver en ny runda för plogbilarna, bärgningsbilarna och skördetröskorna, där ratten står i vägen.
4. Gör fotmåttet till en varning i granskningen: en figur vars fötter syns till mer än 50 % räknas som svävande, som KLIPPS för armen.
5. Gå också igenom de cirka 25 svaga figurerna i en egen runda.
6. Låt allt vara som det är.
