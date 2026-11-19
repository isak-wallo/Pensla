# Granskning av bilder och figurer (native och webb)

Datum: 2026-11-18. Granskare: Claude (subagent, ögongranskning, inte `vektorbild.py --kontroll`).
Ark: `C:\Dropbox\Isak\Program\AI\Claude\keIWs\Pensla\granskning\granskare\` (git-ignorerat).

## Sammanfattning

**Native (6 bilder, 18 figurer): 0 Bra, 3 OK, 15 Dåligt.**
De enda som är OK är keIWs på flygplanets tak, på sopbilens flak och på tankbilens lock. Alla andra figurer svävar i himlen, står fritt på mark eller väg, eller står framför huvudmotivet (keIWs framför seglet). Grön står dessutom på grönt vid häcken i tankbil3.

**Webb (84 aktiva bilder, 252 figurer): 143 Bra, 84 OK, 25 Dåligt.**
Webben fungerar i stort. De dåliga figurerna är av tre slag:
1. keIWs sitter i hytten bakom ratten och stolen, så att 35–49 % döljs (traktorer, tankbilar och skördetröskor: 106, 107, 108, 127, 128, 138, 141, 144).
2. Grön står på grönt i en trädkrona eller på en kulle (6, 113, 120, 127, 128, 141, 142, 144, 145, 146).
3. Figuren står framför motivet: grön i glasstruten (132–134), röd mitt på seglet (18). Dessutom står keIWs och röd på exakt samma plats i 16, och i 10 och 137 drar kullinjen eller röret tvärs över röd.

**Vanligaste felen**
- Native: figuren ritas ovanpå allt utan ytmask, så fötterna syns alltid och figuren skymmer det som ligger framför den (se nedan). Placeringarna verkar valda för en maskad ritning, men native maskar inte.
- Native: färgerna stämmer inte, eftersom angränsande ytor utan egen mörk kontur slås ihop till en polygon med toning mellan två olika färger.
- Webb: hytt-placeringar, grönt på grönt och placeringar framför huvudmotivet.

**Det här behöver vektoriseringen ändra**
1. Dela ytor efter färg och inte bara efter de mörka linjerna. Himmel/kulle, himmel/träd, gräs/väg och vatten/land saknar ofta egen kontur och blir i dag en yta med toning mellan helt olika färger (himlen tonar till grönt, marken blir vatten). Det behövs färgkanter som extra gränser, eller en uppdelning av ytan per färgkluster, före spårningen.
2. Tillåt toning bara när kulören är ungefär densamma (ljus till mörk i samma ton). Annars ska ytan delas upp eller få en platt färg.
3. Små detaljer försvinner: vågor, glans, solens ansikte, antenner och landningsbanans streck. Antingen sänks minsta ytstorlek, eller så behöver linjelagret behålla de detaljerna.
4. Kontrollen ska jämföra färgen mot originalet per pixel (t.ex. medel-ΔE per yta) och flagga ytor där det blir stora fel. I dag godkänns alla sex trots tydliga fel.

**Skillnaden mellan native och webben i hur figurerna ritas**
- Webben (`app.js`): `labelRegions` delar bilden i ytor utifrån SVG-linjerna, och `prepKeiws` och `ritaKeiwsMaskad` klipper figuren till sina ytor (`c.ytor`, destination-in). Linjelagret ritas ovanpå. Figuren syns därför bara i sin bakgrundsyta, och förgrunden (träd, tak, buskar) skymmer fötterna så att den ser ut att titta fram bakom något.
- Native (`PenslaVy.ritaKompisar`): figuren ritas ovanpå färgytorna med bara `clipRect(x−200s, y−400s, x+250s, y)`, alltså utan ytmask. Fötterna (y−36s..y) syns alltid, och figuren täcker allt bakom sig. Bara linjerna ritas över den. Den kan därför aldrig titta fram bakom något, och placeringar som är bra på webben blir svävande i native.
- Rekommendation: maska figuren i native till sin bakgrundsyta, t.ex. genom att spara ett ytindex per figur i JSON (ytan vid kroppens mitt, x, y−124s) och klippa med den ytans `Path`. Ett minimum är att klippa vid y−40s så att fötterna döljs, men då kan kroppen fortfarande hamna framför förgrunden.

## De värsta fallen

1. Native segelbåt: keIWs står på bommen mitt framför seglet. Grön och röd svävar fritt över vattnet och i himlen. Vågorna saknas och en del av marken har blivit vatten eller himmel.
2. Native flygplan-stort: landningsbanan och gräset är borta, och himlen, kullarna och marken har blivit en enda toning från turkos till grått.
3. Native raket och skordetroska6: himlen tonar till grönt. Alla figurer står fritt eller svävar.
4. Webb 16: keIWs och röd står på samma plats (997,531), så keIWs syns inte alls.
5. Webb 132–134: grön sitter i glasstruten på skylten.
6. Webb 138, 141, 144: keIWs bakom ratten och stolen, upp till 49 % dold.

---

## Native, per bild

Ark: `granskare\native-NAMN.png` (svartvitt | färglagd + figurer som native | original) och `granskare\forslag-native-NAMN.png` (förslag som native ritar i dag | förslag med ytmask som webben | original). Zoomvyer finns i `granskare\rutnat\zoom-NAMN.png`. Förslagen finns också i `granskare\forslag_native.json`.

Obs: förslagen förutsätter ytmask i native. Utan mask kommer fötterna fortfarande att synas ovanpå föremålet.

### segelbat
**Trohet: Dåligt.** Vågorna är borta. Remsan mellan horisonten och kullarna till höger har blivit himmel eller vatten (det Isak såg som mark som blivit vatten). Öns träd och gräs har blivit olivgula toningar, horisontlinjen går tvärs genom ön och glansen saknas.

| Figur | I dag | Betyg | Problem | Förslag (x, y, s) |
|---|---|---|---|---|
| keiws | 720, 500, 0.3 | Dåligt | står på bommen mitt framför seglet | 880, 382, 0.3 (bakom den gröna busken på kullen) |
| gron | 1100, 458, 0.3 | Dåligt | svävar över vatten och kulle | 860, 578, 0.3 (tittar fram bakom fören) |
| rod | 968, 366, 0.3 | Dåligt | svävar i himlen | 300, 392, 0.3 (bakom öns högra träd) |

### flygplan-stort
**Trohet: Dåligt.** Landningsbanan (grå med vita streck) och gräsremsan är borta. Himlen, kullarna och marken har blivit en toning från turkos till grått, så himlen ser grönaktig ut. Solens ansikte, tornets antenner, fönsterglansen och skuggan under planet saknas.

| Figur | I dag | Betyg | Problem | Förslag |
|---|---|---|---|---|
| keiws | 736, 250, 0.35 | OK | står på taket med en liten glipa | 118, 212, 0.33 (i tornfönstret) |
| gron | 130, 840 | Dåligt | står fritt på plattan | 230, 424, 0.35 (bakom stabilisatorn) |
| rod | 1090, 850 | Dåligt | står fritt på plattan | 950, 268, 0.28 (bakom kullen till höger) |

### raket
**Trohet: Dåligt/OK.** Himlen tonar till grönt (himmel och gräs har blivit en yta). Det vänstra rökmolnet har smält ihop med plattan till en mörkgrå yta.

| Figur | I dag | Betyg | Problem | Förslag |
|---|---|---|---|---|
| keiws | 150, 860 | Dåligt | står fritt i gräset | 110, 491, 0.4 (bakom vänstra trädet) |
| gron | 862, 583 | Dåligt | svävar ovanför busken mot ljus himmel | 870, 598, 0.3 (bakom den blå kullen) |
| rod | 1110, 860 | Dåligt | står fritt i gräset | 1130, 545, 0.3 (bakom högra trädet) |

### skordetroska6
**Trohet: Dåligt.** Himlen tonar från vitt till mörkgrönt (himmel och träd i en yta). De vänstra kullarna är gulolivfärgade i stället för gröna. Fältets orange stubb och ljusa väg har blivit en beige-persika toning.

| Figur | I dag | Betyg | Problem | Förslag |
|---|---|---|---|---|
| keiws | 64, 814 | Dåligt | står fritt i hörnet | 150, 318, 0.35 (bakom vänstra kullbusken) |
| gron | 1400, 850 | Dåligt | står fritt på fältet | 1300, 258, 0.3 (bakom ladans nock mot molnet) |
| rod | 76, 445, 0.3 | Dåligt | svävar på den gula kullen | 265, 345, 0.3 (bakom busken) |

### sopbil-snett
**Trohet: Dåligt.** De högra träden har fått himlens färg och det rosa huset är grått. Gräsremsan och buskens grönska nere till vänster har blivit grå, och himlen tonar till gråblått.

| Figur | I dag | Betyg | Problem | Förslag |
|---|---|---|---|---|
| keiws | 628, 301, 0.5 | OK | står på flakets tak | 760, 512, 0.33 (i vindrutan) |
| gron | 90, 700 | Dåligt | står fritt på vägen | 97, 306, 0.3 (bakom vänstra trädkronan mot himlen) |
| rod | 1010, 860 | Dåligt | står fritt på vägen | 780, 385, 0.3 (bakom hyttaket) |

### tankbil3
**Trohet: OK** (bäst av de sex). Det vänstra husets vägg är grön i stället för gul, och det högra blå huset är också grönt. Gräsremsan är grå och skuggan saknas.

| Figur | I dag | Betyg | Problem | Förslag |
|---|---|---|---|---|
| keiws | 598, 322, 0.35 | OK | står på tanklocket framför trädet | 598, 342, 0.35 (fötterna bakom locket) |
| gron | 1246, 553, 0.3 | Dåligt | grön på grönt vid häcken | 725, 292, 0.28 (i himlen bakom busken mellan träd och hus) |
| rod | 150, 870 | Dåligt | står fritt på gatan | 255, 440, 0.3 (bakom busken vid husväggen) |

---

## Webb (bilder.js AKTIVA, ritat maskat som webben)

Ark: `granskare\webb\NNN-fil.png` (svartvitt | färglagd maskad | original). Kontaktark finns i `granskare\webb\kontakt\k00–k13.png` och rutnät för de dåliga i `granskare\rutnat\wNNN.png`. Förslag: `granskare\webb\forslag-NNN-fil.png`, med zoomark över alla förslag i `granskare\webb\forslag-zoom.png`. bilder.js är inte ändrad.

### Betyg per bild (keIWs, grön, röd; B = Bra, O = OK, D = Dåligt)

4 B,B,O · 6 B,D,O · 7 B,O,O · 8 B,B,B · 9 O,B,O · 10 O,B,D · 11 O,B,B · 12 O,B,O · 13 B,B,O · 14 B,B,B · 15 B,B,B · 16 D,B,O · 17 O,O,O · 18 O,O,D · 19 B,B,B · 20 B,B,B · 21 B,O,B · 22 O,B,B · 23 B,B,O · 25 B,B,B · 26 B,B,B · 27 O,B,O · 28 B,B,B · 29 B,O,O · 30 B,B,B · 31 B,B,B · 32 B,B,B · 33 B,B,B · 34 O,O,B · 35 B,B,O · 36 B,B,B · 37 O,B,O · 38 B,B,O · 39 B,B,B · 40 B,B,B · 41 B,B,B · 42 B,B,B · 43 B,B,O · 46 O,B,O · 47 O,B,B · 50 B,B,B · 52 B,O,O · 54 O,B,O · 64 B,B,B · 69 O,B,B · 106 D,B,B · 107 D,O,B · 108 D,B,B · 109 B,B,O · 111 O,B,O · 113 B,D,O · 114 O,B,O · 115 O,B,B · 116 O,B,O · 117 O,B,O · 118 O,O,O · 119 B,B,B · 120 O,D,O · 121 B,B,B · 122 B,B,B · 123 O,B,O · 124 B,B,B · 125 B,B,B · 126 B,B,O · 127 D,D,B · 128 D,D,O · 129 O,O,O · 130 O,B,O · 131 O,B,O · 132 B,D,B · 133 B,D,B · 134 B,D,O · 135 B,O,O · 136 B,B,B · 137 B,O,D · 138 D,B,O · 139 O,B,O · 140 O,B,O · 141 D,D,O · 142 B,D,O · 143 B,B,O · 144 D,D,O · 145 O,D,O · 146 O,D,O

### De 25 dåliga, med förslag (ritade och kontrollerade i zoom)

| Nr | Fil | Figur | Problem | Förslag (x, y, s) |
|---|---|---|---|---|
| 6 | flygplan | gron | grön på gröna kullar, propellern går över | 1080, 300, 0.4 (bakom högra trädkronan) |
| 10 | tag | rod | på åkern, kullinjen går över kroppen | 865, 290, 0.3 (bakom det lilla trädet) |
| 16 | raket | keiws | samma plats som röd, syns inte | 140, 514, 0.42 (bakom vänstra trädet) |
| 18 | segelbat2 | rod | mitt på seglet | 260, 372, 0.4 (bakom öns träd) |
| 106 | traktor8 | keiws | bakom ratt och stol, ~40 % dold | 1025, 278, 0.35 (bakom ladans tak) |
| 107 | traktor9 | keiws | bakom ratt och stol | 1038, 288, 0.3 (bakom ladans tak) |
| 108 | traktor10 | keiws | bakom ratt och stol | 1025, 300, 0.35 (bakom ladans tak) |
| 113 | flygplan-stort6 | gron | grön på grön kulle | 1225, 240, 0.3 (bakom terminaltaket) |
| 120 | traktor13 | gron | grön på grön kulle | 862, 180, 0.3 (bakom molnet) |
| 127 | tankbil2 | keiws | bakom ratten, 35 % dold | 850, 322, 0.3 (bakom tanklocket, mot trädet) |
| 127 | tankbil2 | gron | i trädkronan, grönt på grönt | 1044, 250, 0.28 (bakom det lilla molnet) |
| 128 | tankbil3 | keiws | bakom ratten, 37 % dold | 588, 335, 0.3 (bakom tanklocket, mot trädet) |
| 128 | tankbil3 | gron | i trädkronan | 1050, 256, 0.3 (bakom husets tak) |
| 132 | glassbil | gron | i glasstruten, framför motivet | 875, 256, 0.3 (bakom bilens tak) |
| 133 | glassbil2 | gron | i glasstruten | 725, 262, 0.28 (bakom bilens tak) |
| 134 | glassbil3 | gron | i glasstruten | 875, 272, 0.3 (bakom bilens tak) |
| 137 | skordetroska2 | rod | vid röda ladan, röret och trädet över | 600, 206, 0.3 (bakom tröskans tak) |
| 138 | skordetroska3 | keiws | bakom ratt och stol | 1412, 335, 0.3 (bakom ladans tak) |
| 141 | skordetroska6 | keiws | bakom ratt och stol | 950, 150, 0.3 (bakom tröskans tak) |
| 141 | skordetroska6 | gron | i trädkronan | 1325, 256, 0.3 (bakom ladans tak) |
| 142 | skordetroska7 | gron | i trädkronan | 1388, 285, 0.3 (bakom ladans tak) |
| 144 | skordetroska9 | keiws | bakom ratt och stol, 49 % dold | 412, 288, 0.3 (bakom trädet) |
| 144 | skordetroska9 | gron | i trädkronan | 1000, 200, 0.3 (bakom tröskans tak) |
| 145 | skordetroska10 | gron | i trädkronan | 875, 206, 0.3 (bakom tröskans tak) |
| 146 | skordetroska11 | gron | i trädkronan | 750, 222, 0.3 (bakom tröskans tak) |

Alla förslag finns i `granskare\forslag_webb.json` (format `{"webb": {"NR": {figur: {x, y, s}}}}`). Kvarstående småsaker i zoom: i 6, 16, 18 och 120 skymtar fötterna svagt genom busken eller molnet, eftersom ytgränsen där är mjuk. De kan sänkas ett par pixlar till om det stör. I 113 hamnar grön liten i glipan mellan torn och terminal (OK).

### Vanliga OK-anmärkningar
- Blått på blått i hyttfönster (114–117, 123): keIWs syns, men kontrasten är låg.
- Små fönster med s 0,25–0,28 (10, 11, 12): figuren blir liten.
- Figurer vid bildkanten (29, 69, 109, 111, 130, 138, 145, 146): de skärs delvis av kanten.
- Streck över kroppen vid kullinjer (flera bilder): kullinjen går genom figuren men den känns ändå igen.
