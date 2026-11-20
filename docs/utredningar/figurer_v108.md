# Figurerna, Pensla v108-test

Datum: 2026-11-20. Grenen `jobb/figurer-v108`. Det här bygger på `figurgranskning_v107.md`.

Om rubrikerna: rubriker märkta **(spoilerfri)** säger inget om var figurerna gömmer sig. Under rubriker märkta **(gömställen i texten)** står var figurerna sitter.

## Sammanfattning (spoilerfri)

- **27 figurer i 24 bilder har flyttats.** 13 av dem är förslagen från v107, och 14 kommer från en ny runda bland de svaga figurerna.
- **Svävande figurer:** före ändringarna hade 16 figurer mer än hälften av fötterna synliga. Efter ändringarna är det 1.
- **Armen:** antalet figurer där armen syns till minst 99 % gick från 139 till 157 av 252. Ingen figur har armen under 90 %, varken före eller efter.
- **Inget blev sämre.** Alla aktiva bilder granskades om efter ändringarna. De 225 figurer som inte flyttats har exakt samma mått som förut. Av de flyttade har ingen fått sämre arm. Fyra har fått något mer synliga fötter, men högst 18 %.
- **Fotmåttet är nu en varning** (SVÄVAR, när mer än 50 % av fötterna syns) i `figurgranskning.py` och `vinkarm.py`.
- `sw.js` har nu `VERSION = 'v108-test'`. `ASSETS` är oförändrad, eftersom `AKTIVA` inte har ändrats (kontrollerat med `aktiva.py`).

## Ändringar i verktygen (spoilerfri)

- **`vinkarm.py`:**
  - `matt()` mäter nu också fötterna (`fot`, det vill säga stilla-klossarna under kroppen).
  - Utskriften visar `fot` och varnar `SVÄVAR` när fötterna syns till mer än `FOT_MAX` (0,5).
  - Före/efter-arken visar fotmåttet.
  - `chromium()` ligger här och delas av skripten. Den tar Playwrights egen Chromium, och annars `PENSLA_CHROME` eller den som finns i `/opt/pw-browsers`.
- **`figurgranskning.py`:**
  - Varningarna KLIPPS och SVÄVAR står i rött i arket och i utskriften, och under `varning` i `matt.json`.
  - Sist skrivs en lista över alla varningar.
- **`gomstallen.py`:**
  - Går nu att köra på Linux: Chromium hittas med `chromium()`, och DejaVu används när Segoe UI saknas.
  - Kräver scipy.
- **`aktiva.py`:** behåller en ändelse i versionen (v108-test → v109-test). Förut klarade den bara `vNNN`.
- **`granska_figurer.py`:** inte ändrad. Den har hårdkodade Windows-sökvägar och mäter hela figuren, inte fötterna, så den gick inte att prova här.
- **`CLAUDE.md`:** har ett nytt stycke om fotmåttet och granskningen, och raden om `aktiva.py` beskriver ändelsen.

## Arbetssätt (spoilerfri)

1. `gomstallen.py --kandidater` togs fram för de svaga bilderna, och armen, kroppen och fötterna mättes för varje kandidat.
2. För figurer som står i en ruta söktes en plats i samma yta, nära den gamla, där fötterna döljs (av fönsterkanten, instrumentbrädan eller taket) och armen syns helt.
3. Varje förslag ritades som ett före/efter-ark (`vinkarm.py --ark`) och granskades med ögonen.
4. Bara förslag som blev tydligt bättre fördes in. Tre förslag som såg bra ut i siffrorna ströks efter granskningen med ögonen, eftersom figuren hamnade inne i ett moln i stället för bakom det.

Före/efter-ark finns i `docs/utredningar/figurer_v108/`, ett per ändrad bild (25 ark, 1,9 MB). Varje ark visar ett utsnitt före och efter, stilla och vinkande, och hela bilden efter.

## Flyttade figurer (gömställen i texten)

Mått: kr = synlig kropp, arm = synlig arm vid vinkning, fot = synliga fötter. Formatet är x, y, s.

**Från v107-förslagen (13):**

| Nr | Figur | Före | Efter | Var |
|---|---|---|---|---|
| 34 | rod | 754,150,0.5 kr 94 arm 100 fot 0 | 1120,258,0.42 kr 91 arm 100 fot 0 | bakom terminalens tak |
| 38 | rod | 369,359,0.5 kr 90 arm 100 fot 1 | 1040,130,0.4 kr 90 arm 100 fot 18 | bakom molnet till höger |
| 106 | gron | 204,304,0.5 kr 99 arm 100 fot 8 | 135,278,0.36 kr 90 arm 100 fot 0 | bakom träden |
| 111 | keiws | 690,450,0.4 kr 99 arm 100 fot 99 | 700,478,0.4 kr 96 arm 100 fot 0 | över instrumentbrädan |
| 114 | keiws | 834,344,0.386 kr 100 arm 90 fot 100 | 400,228,0.4 kr 88 arm 100 fot 0 | bakom lasset |
| 115 | keiws | 561,366,0.386 kr 100 arm 90 fot 100 | 290,248,0.34 kr 65 arm 100 fot 0 | bakom husets tak |
| 116 | keiws | 276,421,0.42 kr 100 arm 91 fot 100 | 310,290,0.4 kr 92 arm 100 fot 0 | bakom ljusrampen |
| 117 | keiws | 1092,414,0.386 kr 100 arm 91 fot 100 | 1000,262,0.4 kr 88 arm 100 fot 0 | bakom ljusrampen |
| 118 | rod | 269,513,0.455 kr 97 arm 91 fot 0 | 730,150,0.4 kr 83 arm 100 fot 0 | bakom det lilla molnet |
| 140 | keiws | 476,418,0.42 kr 84 arm 93 fot 93 | 990,180,0.4 kr 98 arm 100 fot 1 | bakom molnet |
| 143 | rod | 1450,290,0.5 kr 100 arm 100 fot 100 | 1450,150,0.4 kr 82 arm 100 fot 0 | bakom trädkronan |
| 145 | keiws | 615,425,0.45 kr 79 arm 91 fot 48 | 1058,165,0.4 kr 100 arm 100 fot 16 | bakom molnet |
| 146 | keiws | 549,466,0.441 kr 91 arm 91 fot 38 | 540,140,0.4 kr 98 arm 100 fot 2 | bakom molnet |

**Från de svaga figurerna (14):**

| Nr | Figur | Före | Efter | Var |
|---|---|---|---|---|
| 9 | keiws | 705,468,0.361 kr 100 arm 91 fot 100 | 706,546,0.345 kr 100 arm 100 fot 0 | kvar i fönstret, tittar fram över kanten bredvid stolen |
| 10 | keiws | 519,504,0.274 kr 100 arm 93 fot 100 | 514,522,0.287 kr 100 arm 100 fot 0 | kvar i lokets fönster, tittar fram över kanten |
| 11 | keiws | 709,499,0.274 kr 100 arm 90 fot 100 | 704,514,0.287 kr 98 arm 100 fot 0 | kvar i lokets fönster, tittar fram över kanten |
| 12 | keiws | 728,488,0.248 kr 100 arm 91 fot 66 | 520,314,0.34 kr 94 arm 100 fot 1 | bakom skorstenen, mot himlen (förut i ett litet fönster) |
| 17 | gron | 382,547,0.288 kr 80 arm 92 fot 0 | 545,535,0.5 kr 100 arm 100 fot 9 | bakom relingen, mot seglet (förut liten, i vattnet) |
| 116 | rod | 918,381,0.405 kr 85 arm 90 fot 0 | 864,260,0.5 kr 91 arm 100 fot 10 | bakom kranbommen, mot himlen (förut med kedjan över sig) |
| 120 | rod | 516,269,0.288 kr 85 arm 90 fot 0 | 699,238,0.5 kr 95 arm 100 fot 9 | bakom kullen, mot himlen (förut liten) |
| 121 | keiws | 712,406,0.4 kr 85 arm 93 fot 31 | 716,415,0.36 kr 88 arm 100 fot 0 | över armen och lyktan |
| 122 | keiws | 596,421,0.41 kr 88 arm 90 fot 6 | 600,424,0.369 kr 88 arm 99 fot 0 | över motorhuven, utan ratten över sig |
| 124 | keiws | 751,402,0.455 kr 98 arm 92 fot 32 | 746,414,0.45 kr 90 arm 100 fot 0 | lite lägre, fötterna bakom instrumentbrädan |
| 128 | keiws | 588,335,0.3 kr 100 arm 100 fot 54 | 601,338,0.31 kr 100 arm 100 fot 0 | bakom tanklocket (förut stod han på det) |
| 134 | gron | 875,272,0.3 kr 100 arm 100 fot 58 | 873,278,0.29 kr 100 arm 100 fot 0 | bakom taket (förut stod hen på det) |
| 142 | keiws | 670,440,0.45 kr 100 arm 99 fot 71 | 662,452,0.445 kr 100 arm 100 fot 0 | lite lägre i rutan, fötterna bakom kanten |
| 145 | gron | 875,206,0.3 kr 100 arm 100 fot 83 | 876,218,0.31 kr 99 arm 100 fot 0 | bakom tröskans tak (förut stod hen på det) |

I bilder.js har kommentarerna för 12, 114–117, 128, 140, 145 och 146 bytts ut, så att de stämmer med de nya platserna.

## Lämnade som de är (gömställen i texten)

- **4 keiws (fot 92 %, den enda SVÄVAR som är kvar).** I framrutan går torkarna diagonalt över rutan. När han sänks går torkaren tvärs över kroppen. Platsen ovanför hyttaket blir för nära gron. Andra platser ute är framför soptunnorna eller på vägen. Behöver en hand vald plats eller en ny bild.
- **10 och 11 keiws:** fötterna är nu dolda, men lokets fönster är fortfarande litet (s 0,287). Platserna ute (bakom vagnstaken) gav en kullinje tvärs över ansiktet.
- **46 keiws (runt fönster, kr 83 %, arm 91 %):** platserna ute hamnade framför raketens fenor. Att flytta honom inom fönstret ändrade för lite.
- **118, 119 och 129 keiws (i hytten med ratten över sig):** fötterna är redan dolda. De sänkta platserna såg likadana ut, med ratten kvar över kroppen.
- **118 gron, 127 gron och 133 gron:** förslagen bakom moln såg bra ut i siffrorna, men figuren hamnade inne i molnet. De ströks. 127 och 133 gron står alltså fortfarande nära rod.
- **13 rod (röd mot det röda skrovet):** gomstallen.py hittade ingen kandidat med armen synlig.
- **54 rod (röd mot den röda motorhuven):** den enda bra platsen ute är ovanför hyttaket, men där står redan keiws och gron på rad.
- **64 gron (ovanför den gröna tröskan):** alternativet i hytten blev grönt mot den gröna karmen och var inte bättre.
- **120 keiws (s 0,28 bakom ladan, kr 64 %):** fick ingen bättre plats. Rod i samma bild är däremot flyttad.

## Kontroll efter ändringarna (spoilerfri)

- `python verktyg/figurgranskning.py --par` kördes på alla 84 aktiva bilder och 252 figurer. Den gav en enda varning (nr 4 keiws SVÄVAR).
- **Före → efter:**
  - SVÄVAR (fot > 50 %): 16 → 1
  - fot > 40 %: 17 → 1
  - arm < 90 %: 0 → 0
  - arm ≥ 99 %: 139 → 157
- Inga andra tester finns i `verktyg/`. Dessutom kontrollerades syntaxen i `bilder.js` och `sw.js` med node, och `aktiva.py` gav samma `ASSETS`.

## Senare i samma version (gömställen i texten)

När Flygplan 6, Stort flygplan 5, Skördetröska och Traktor 7 fick hela sitt format (se `bilder_v108.md`) flyttades alla deras figurer 75 px åt höger. I Skördetröska hade linjerna mot himlen ändrats lite, och därför flyttades två figurer:

- keiws flyttades till 1000,223,0.47 (arm 36 → 100 %);
- rod flyttades till 374,227,0.4 (arm 89 → 100 %).

I Traktor 7 syns keiws kropp nu till 62 % (förut 70 %), men fötterna syns inte längre (förut 20 %). Platsen lämnades som den är.
