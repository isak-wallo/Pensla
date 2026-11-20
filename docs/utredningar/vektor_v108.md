# Vektorbilderna till Pensla N, v108

Datum: 2026-11-20. Grenen `jobb/figurer-v108`.

Rubriker märkta **(spoilerfri)** säger inget om var figurerna gömmer sig. Tabellen längst ned ger bara mått, inga platser.

## Sammanfattning (spoilerfri)

- **Alla 84 aktiva bilder** finns nu som vektor-JSON (format 1) i `native/bilder/NAMN.json`. Kopiera dem till `pensla-native/app/src/main/assets/bilder/`.
- **`--kontroll` godkänner alla 84:** inga fria ändar, inga luckor och alla figurer godkända.
  - Medel-ΔE mot färgbilden är i snitt 1,85 (median 1,7, högst 3,9).
  - Sex bilder ligger över 3: Skördetröska 3,9, Traktor 7 3,5, Flygplan 6 3,4, Traktor 6 3,3, Sopbil 3 3,2 och Traktor 8 3,1.
- **Figurerna står på webbens platser** (bilder.js, med granskningen i v108). De är justerade så att kroppen syns till 65–80 % i 250 av 252 fall (övriga 86 och 89 %) och armen till minst 90 %.
- **Storlek:** 16,7 MB totalt för 84 filer. Snittet är 198 kB per bild, den minsta är 89 kB och den största 745 kB (Skördetröska, där vetet ger många små ytor).
  - Appen läser en bild åt gången, så 2 GB minne räcker gott.
  - Om APK:n ska hållas liten är vetebilderna och traktorerna med gräs de tyngsta. Se tabellen.

## Grenen jobb/vektor3 (spoilerfri)

- `jobb/vektor3` slogs ihop in i den här grenen utan konflikter. Den lade bara till filer: `vektorbild.py`, `matt_figurer.py`, `bildanalys.py`, `bildoversyn.py` och `bildoversyn.md`.
- Ändringar efter sammanslagningen:
  - **Chromium och typsnitt:** `bildanalys.py`/`vektorbild.py` hittar Chromium och ett typsnitt på Linux.
  - **Var filerna hamnar:** förvald mapp är `native/bilder` i repot (förut `pensla-native` bredvid repot).
  - **Figurerna:** utan en post i `GOMSTALLEN` tas webbens platser ur bilder.js, flyttade efter `BESKAR`. Varje figur (också de i `GOMSTALLEN`) går genom `justera`:
    - den flyttas upp eller ner högst 40 px och åt sidan högst en femtedel av kroppen, och krymps högst 20 %;
    - det fortsätter tills den ligger inne i bilden, armen syns till 90 % och kroppen till 65–80 %, med så liten ändring som möjligt;
    - först prövas webbens yta. Räcker den inte (linjerna i vektorbilden kan dela en yta annorlunda) prövas ytan vid kroppens mitt.
  - **Kontrollen:**
    - Armen ska synas till minst 90 % (`ARM_MIN`), annars är det ett fel.
    - En kropp som syns mer än 85 % ger en varning.
    - Fria ändar: en sporre kortare än två linjebredder, eller en ände inne i en fylld klump (en prick på en antenn, en liten mörk yta som blivit linje), räknas inte. Sådana kan varken öppna eller stänga en yta.
  - **Glipor:** smala glipor i den tjocka linjen (hål under `YTA_MIN`) fylls innan linjen spåras.
  - **`BILDINST`:** egna inställningar per bild:
    - Dumper: toning över mer kulör, för hyttens skugga;
    - Skördetröska: 48 färger och 4 % tillåtna felpixlar, för vetet;
    - Traktor 6 och 7: en liten yta får ha ΔE upp till 15, där ett litet träd och ett hjulnav blir en del av den större ytan.
  - **`matt_figurer.py`:** läser figurerna ur JSON-filerna och mäter alla.

## Så görs de om (spoilerfri)

```
python verktyg/vektorbild.py --gor NAMN ...       # gör JSON (0,5–2 min per bild)
python verktyg/vektorbild.py --figurer NAMN ...   # bara figurerna (efter ändringar i bilder.js)
python verktyg/vektorbild.py --kontroll           # alla i native/bilder
python verktyg/matt_figurer.py                    # kropp, fötter och arm per figur
```

Förhandsbilder hamnar i `granskning/vektor/` (inte i git).

## Att titta på (spoilerfri)

- Platserna är valda av ett skript utifrån webbens gömställen och har bara granskats översiktligt med ögonen, i småbilder av alla 84. Titta gärna på dem i plattan.
- Där en figur bytt yta i vektorbilden kan den stå något annorlunda än på webben. Det gäller bland annat en figur i Ambulans 2.
- Traktor 10 blir ren som vektor, trots att webbens konturer har 282 glapp. I `bilder_v108.md` står ändå en prompt för en ny bild.

## Tabell (spoilerfri)

Kropp % = hur stor del av kroppen som syns för keIWs, grön och röd (i den ordningen). Arm min = den lägsta andelen synlig arm vid vinkning i bilden.

| Nr | Fil | Ytor | kB | Medel-ΔE | ΔE > 15 | Kropp % (keiws/gron/rod) | Arm min |
|---:|---|---:|---:|---:|---:|---|---:|
| 4 | sopbil-snett | 575 | 196 | 1.4 | 0.1 % | 79/73/80 | 100 % |
| 6 | flygplan | 187 | 92 | 1.3 | 0.0 % | 79/75/78 | 100 % |
| 7 | flygplan2 | 192 | 90 | 1.3 | 0.2 % | 80/78/79 | 100 % |
| 8 | helikopter | 240 | 106 | 1.2 | 0.0 % | 80/79/80 | 94 % |
| 9 | helikopter2 | 303 | 131 | 1.3 | 0.2 % | 78/79/77 | 95 % |
| 10 | tag | 458 | 189 | 2.5 | 0.6 % | 77/78/80 | 99 % |
| 11 | tag2 | 446 | 168 | 1.9 | 0.1 % | 80/78/71 | 92 % |
| 12 | bat | 215 | 110 | 2.0 | 0.1 % | 80/80/78 | 100 % |
| 13 | bat2 | 296 | 126 | 1.7 | 0.1 % | 72/79/73 | 95 % |
| 14 | flygplan-stort | 257 | 109 | 2.6 | 0.4 % | 71/77/67 | 100 % |
| 15 | flygplan-stort2 | 278 | 125 | 1.3 | 0.0 % | 79/79/76 | 91 % |
| 16 | raket | 204 | 106 | 2.2 | 0.2 % | 77/69/76 | 100 % |
| 17 | segelbat | 234 | 103 | 1.7 | 0.2 % | 66/75/76 | 100 % |
| 18 | segelbat2 | 178 | 93 | 1.8 | 0.0 % | 73/80/77 | 91 % |
| 19 | polisbil | 253 | 128 | 1.6 | 0.2 % | 78/79/78 | 95 % |
| 20 | polisbil2 | 211 | 116 | 1.8 | 0.2 % | 80/80/77 | 93 % |
| 21 | polisbil3 | 267 | 132 | 2.5 | 2.3 % | 79/79/80 | 97 % |
| 22 | ambulans | 174 | 107 | 2.7 | 2.9 % | 80/76/80 | 97 % |
| 23 | ambulans2 | 228 | 112 | 1.2 | 0.2 % | 78/80/65 | 94 % |
| 25 | betongbil2 | 310 | 144 | 1.6 | 0.4 % | 78/79/68 | 95 % |
| 26 | kranbil | 373 | 158 | 1.2 | 0.2 % | 78/79/78 | 96 % |
| 27 | kranbil2 | 363 | 176 | 1.5 | 0.3 % | 72/79/80 | 92 % |
| 28 | buss | 283 | 137 | 1.5 | 0.2 % | 78/80/89 | 95 % |
| 29 | buss2 | 287 | 135 | 1.8 | 0.1 % | 80/80/78 | 92 % |
| 30 | brandbil | 352 | 149 | 2.8 | 2.1 % | 78/78/78 | 97 % |
| 31 | brandbil2 | 422 | 182 | 1.6 | 0.3 % | 72/79/80 | 91 % |
| 32 | dumper | 246 | 127 | 2.3 | 0.2 % | 80/78/80 | 96 % |
| 33 | dumper2 | 237 | 130 | 1.8 | 0.4 % | 80/78/79 | 100 % |
| 34 | flygplan-stort3 | 332 | 131 | 1.4 | 0.1 % | 79/78/80 | 93 % |
| 35 | flygplan-stort4 | 424 | 128 | 1.7 | 0.8 % | 79/79/66 | 100 % |
| 36 | sopbil3 | 338 | 158 | 3.2 | 1.4 % | 80/79/79 | 97 % |
| 37 | sopbil4 | 357 | 165 | 2.0 | 0.2 % | 80/80/77 | 92 % |
| 38 | flygplan3 | 324 | 127 | 1.4 | 0.1 % | 80/78/79 | 100 % |
| 39 | flygplan4 | 189 | 95 | 2.2 | 0.3 % | 80/80/80 | 100 % |
| 40 | flygplan5 | 162 | 97 | 2.0 | 0.1 % | 80/79/79 | 99 % |
| 41 | gravare2 | 335 | 154 | 2.1 | 0.9 % | 79/80/80 | 100 % |
| 42 | gravare3 | 238 | 138 | 2.2 | 0.2 % | 80/78/79 | 100 % |
| 43 | traktor3 | 243 | 117 | 2.9 | 0.1 % | 78/79/80 | 94 % |
| 46 | raket2 | 283 | 119 | 1.7 | 0.1 % | 77/80/74 | 95 % |
| 47 | raket3 | 214 | 102 | 1.1 | 0.1 % | 65/79/78 | 100 % |
| 50 | flygplan6 | 746 | 266 | 3.4 | 1.1 % | 80/79/80 | 100 % |
| 52 | flygplan-stort5 | 736 | 267 | 2.5 | 0.6 % | 80/79/79 | 96 % |
| 54 | traktor6 | 1228 | 366 | 3.3 | 1.8 % | 79/80/70 | 92 % |
| 64 | skordetroska | 2964 | 746 | 3.9 | 3.5 % | 78/80/80 | 100 % |
| 69 | traktor7 | 1248 | 415 | 3.5 | 1.9 % | 67/78/79 | 93 % |
| 106 | traktor8 | 301 | 164 | 3.1 | 0.7 % | 73/78/79 | 96 % |
| 107 | traktor9 | 490 | 217 | 1.4 | 0.1 % | 80/65/78 | 94 % |
| 108 | traktor10 | 798 | 296 | 2.3 | 0.9 % | 65/80/80 | 91 % |
| 109 | betongbil4 | 586 | 203 | 1.6 | 0.3 % | 80/78/78 | 100 % |
| 111 | ambulans4 | 287 | 142 | 2.9 | 1.9 % | 78/78/86 | 100 % |
| 113 | flygplan-stort6 | 550 | 227 | 1.4 | 0.4 % | 78/79/78 | 91 % |
| 114 | plogbil2 | 589 | 271 | 1.8 | 0.6 % | 79/80/80 | 100 % |
| 115 | plogbil3 | 619 | 281 | 2.0 | 0.7 % | 66/78/80 | 98 % |
| 116 | bargningsbil2 | 566 | 253 | 1.6 | 0.5 % | 80/80/79 | 100 % |
| 117 | bargningsbil3 | 653 | 258 | 1.9 | 0.6 % | 80/80/79 | 100 % |
| 118 | traktor11 | 753 | 329 | 2.2 | 1.1 % | 78/79/78 | 100 % |
| 119 | traktor12 | 573 | 284 | 1.4 | 0.3 % | 79/79/78 | 95 % |
| 120 | traktor13 | 867 | 360 | 2.6 | 0.7 % | 65/80/80 | 91 % |
| 121 | hjullastare | 940 | 325 | 1.1 | 0.7 % | 79/80/79 | 100 % |
| 122 | hjullastare2 | 847 | 287 | 1.9 | 0.6 % | 80/79/78 | 94 % |
| 123 | hjullastare3 | 882 | 314 | 2.0 | 0.8 % | 70/78/79 | 90 % |
| 124 | hjullastare4 | 932 | 333 | 2.2 | 0.8 % | 80/80/79 | 95 % |
| 125 | brandbil6 | 447 | 184 | 0.9 | 0.4 % | 79/80/79 | 94 % |
| 126 | tankbil | 450 | 169 | 0.8 | 0.2 % | 79/80/79 | 94 % |
| 127 | tankbil2 | 542 | 242 | 1.6 | 0.3 % | 78/77/79 | 100 % |
| 128 | tankbil3 | 479 | 223 | 1.4 | 0.3 % | 77/68/80 | 96 % |
| 129 | tankbil4 | 393 | 204 | 1.8 | 0.3 % | 65/80/79 | 90 % |
| 130 | brandbil7 | 566 | 257 | 1.8 | 0.6 % | 79/78/80 | 99 % |
| 131 | brandbil8 | 669 | 265 | 1.7 | 0.4 % | 65/79/80 | 97 % |
| 132 | glassbil | 619 | 254 | 1.7 | 0.4 % | 73/80/79 | 100 % |
| 133 | glassbil2 | 549 | 238 | 1.9 | 0.4 % | 70/80/79 | 91 % |
| 134 | glassbil3 | 543 | 235 | 1.7 | 0.4 % | 80/80/79 | 98 % |
| 135 | glassbil4 | 414 | 157 | 0.8 | 0.1 % | 78/79/78 | 100 % |
| 136 | glassbil5 | 379 | 149 | 0.8 | 0.2 % | 79/78/80 | 100 % |
| 137 | skordetroska2 | 356 | 179 | 1.1 | 0.6 % | 79/78/77 | 92 % |
| 138 | skordetroska3 | 554 | 250 | 1.6 | 0.5 % | 78/80/79 | 100 % |
| 139 | skordetroska4 | 698 | 277 | 2.1 | 0.6 % | 77/72/80 | 95 % |
| 140 | skordetroska5 | 782 | 280 | 2.0 | 0.4 % | 79/79/79 | 94 % |
| 141 | skordetroska6 | 494 | 187 | 1.1 | 0.3 % | 68/71/78 | 100 % |
| 142 | skordetroska7 | 503 | 209 | 1.0 | 0.5 % | 79/77/79 | 97 % |
| 143 | skordetroska8 | 461 | 202 | 1.3 | 0.2 % | 80/79/80 | 97 % |
| 144 | skordetroska9 | 575 | 240 | 1.1 | 0.7 % | 80/79/80 | 96 % |
| 145 | skordetroska10 | 509 | 221 | 1.5 | 0.3 % | 79/80/80 | 95 % |
| 146 | skordetroska11 | 526 | 230 | 1.7 | 0.4 % | 78/79/67 | 100 % |
