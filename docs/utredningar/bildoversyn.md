# Bildöversyn 2026-11-18: glapp i konturerna och gömda figurer

Genomgång av alla 84 aktiva bilder i `bilder.js`, gjord med
`python verktyg/bildoversyn.py` (förhandsbilder i `granskning/oversyn/`,
inte i git). Inga bilder och ingen kod i webbappen har ändrats.

## Vad som mättes

- **Glapp**: konturerna tunnas till ett skelett och varje fri ände
  undersöks. Finns en annan linje inom 20 px rakt fram är det ett glapp
  (två ytor rinner ihop). Annars räknas änden som ett **löst streck**
  (glans, skugga eller en kontur som tar slut). Ändar vid bildkanten
  räknas inte.
- **Figurerna** (keIWs, grön, röd) ritas som i appen: bara i sina ytor och
  ovanför fötterna. `dold` är hur stor del av figuren (stilla) som inte
  syns, och `kroppen` är samma sak för själva kroppen. `streck` betyder att
  en kontur går över kroppen. `armen klipps` betyder att mer än 30 % av den
  vinkande armen försvinner, och `svävar` att det inte finns något under
  fötterna.

## Huvudfynd

1. **Glapp finns i alla 84 bilder**: 2986 glapp, median 27 per bild. Bara 7
   bilder har högst 5 glapp, medan 37 har fler än 30. De värsta är
   traktor10 (282), sopbil4 (98), kranbil2 (95), betongbil4 (93),
   brandbil2 (86), traktor9 (84), raket och flygplan-stort4 (78 var),
   raket2 och brandbil (73 var). Lösa streck: 1252, median 11 per bild.
   I webbappen syns glappen inte, eftersom färgen tas pixel för pixel ur
   färgbilden. De blir däremot synliga så fort en yta ska fyllas som en
   helhet (vektorer, ifyllnad, native).
2. **Figurerna står för det mesta delvis bakom något.** 243 av 252 figurer
   döljs till mer än 2 %. Det är "tittar fram bakom"-designen, där
   fötterna alltid döljs (cirka 8 %). Det som faktiskt stör:
   - 161 figurer har kroppen dold till mer än 2 %, och 67 till mer än 10 %;
   - 188 har en kontur över kroppen;
   - 86 får den vinkande armen avklippt;
   - 52 är dolda till mer än 20 %;
   - 12 svävar och 14 sticker delvis ut utanför bilden;
   - i raket står keIWs och röd på samma plats.

   Bara 41 figurer (16 %) syns helt utan streck över sig. Bara två bilder
   (flygplan2, skordetroska8) har alla tre figurerna rena.
3. **Värst dolda**:

   | Bild | Figur | Dold |
   |---|---|---:|
   | skordetroska9 | keIWs | 49 % |
   | skordetroska6 | keIWs | 48 % |
   | traktor8 | keIWs | 42 % |
   | skordetroska3 | keIWs | 42 % |
   | tankbil2 | keIWs | 37 % |
   | traktor9 | keIWs | 36 % |
   | tankbil3 | keIWs | 35 % |
   | glassbil | keIWs | 30 % |
   | skordetroska2 | röd | 29 % |
   | helikopter2 | röd | 29 % |
   | tankbil3 | grön | 28 % |

   keIWs i hyttfönstret (framrutan med ratt och stolpar) är den vanligaste
   orsaken.

## Det som gjordes nu: sex bilder som vektorer (till Pensla N)

`python verktyg/vektorbild.py --gor NAMN` gör en bild till rena vektorer
(format 1, JSON). Resultatet läggs i
`keIWs/pensla-native/app/src/main/assets/bilder/`.

**Hur verktyget gör en bild:**

1. Konturerna läses i dubbel upplösning och tunnas till ett skelett.
2. Glapp sluts: ändar som pekar mot en linje kopplas ihop, annars förlängs
   de rakt fram upp till 40 px. Lösa streck som inte når någon linje äts
   bort till närmaste korsning, och lösa prickar under 60 px tas bort.
3. Linjerna ritas om med jämn bredd 5 och spåras med potrace.
4. Varje sluten yta blir en polygon med en färg: en platt färg (median),
   eller en linjär toning när färgbilden har en tydlig toning i ytan.
   Ytor under 60 px blir linje.
5. Gömställen för figurerna står i `GOMSTALLEN` och skrivs med `--figurer`.

**Kontrollen (`--kontroll`)** gör om bilden från JSON och kollar att:

- inga streck slutar fritt (10 px marginal mot kanten);
- inga luckor finns mellan ytorna;
- figurerna står helt fritt i alla lägen (stilla, vinka och studs), med
  2 px luft mot streck;
- figurerna ligger inom bilden och inte på varandra;
- kontrasten mot ytan bakom är minst Lab 25.

`--kandidater` föreslår fria platser med en linje under fötterna.
Kandidaterna hamnar oftast på moln och spetsar. De slutliga platserna
valdes därför för hand, på mark, tak och däck, med kandidaterna som hjälp.

| Bild | Ytor | kB | keIWs | Grön | Röd |
|---|---:|---:|---|---|---|
| sopbil-snett (4) | 140 | 118 | på flaket | trottoaren t.v. | gatan t.h. |
| flygplan-stort (14) | 71 | 73 | på flygkroppen | plattan t.v. | plattan t.h. |
| raket (16) | 53 | 63 | gräset t.v. | kullen | gräset t.h. |
| segelbat (17) | 52 | 53 | på bommen | stranden t.h. | buskarna på kullen |
| tankbil3 (128) | 168 | 154 | på tanklocket | trottoaren t.h. | gatan t.v. |
| skordetroska6 (141) | 150 | 135 | åkern t.v. | åkern t.h. | kullen t.v. |

Alla sex klarar kontrollen utan fel. Två saker bör tittas på:

- I segelbåten står röd en bit ovanför buskarna. Det finns ingen fri plats
  som är lägre där.
- Moln och träd som ligger kant i kant utan linje emellan blir en enda yta
  med en toning. Det syns i sopbilens moln och träd.

## Plan för resten

1. **Vektorisera fler i omgångar om 6–10**, de med minst glapp först (se
   tabellen). Det går fort, cirka 3–5 minuter per bild. Det som tar tid är
   att välja gömställena för hand.
2. **Bilder med fler än 60 glapp** (traktor10, sopbil4, kranbil2,
   betongbil4, brandbil2, traktor9 m.fl.): verktyget sluter glappen, men
   ytor som saknar egen kontur rinner ihop till en toning. Spåra om dem
   först med `fargbild.py` (`TECKNING`/`FARGOMRADEN`). Går det inte, byt
   ut dem mot nya bilder från Gemini.
3. **Figurerna i webbappen:** flytta de 67 figurer vars kropp är dold till
   mer än 10 % till fria platser, med `gomstallen.py` (`--kandidater`/
   `--valj`). Ta de värst dolda först (tabellen ovan) och rätta krocken i
   raket. Armen som klipps (86 st) blir bra av sig själv när figuren står
   fritt.
4. **Gemensamt format:** webben kan läsa format 1 direkt. `d` går rakt in i
   `Path2D`, ytorna fylls med `evenodd` och linjen ritas överst. Om webben
   ska gå över till vektorer kan bilderna flyttas till ett eget ställe som
   båda läser. Det är ett eget beslut, så inget i `bilder.js` har ändrats.
5. Kör `bildoversyn.py` igen efter varje omgång. Numren i tabellen nedan
   är utgångsläget.

## Tabell: alla aktiva bilder

| Nr | Bild | Glapp | Lösa streck | keIWs | Grön | Röd |
|---:|---|---:|---:|---|---|---|
| 4 | Sopbil snett | 46 | 19 | ok | 8 % dold | 20 % dold, kroppen 11 %, streck över kroppen |
| 6 | Flygplan | 28 | 2 | 8 % dold, armen klipps | 20 % dold, kroppen 9 %, streck över kroppen | 16 % dold, kroppen 8 %, streck över kroppen |
| 7 | Flygplan 2 | 32 | 9 | 10 % dold | 8 % dold | 8 % dold |
| 8 | Helikopter | 36 | 1 | 8 % dold | 8 % dold | 19 % dold, kroppen 5 %, streck över kroppen, armen klipps |
| 9 | Helikopter 2 | 15 | 2 | svävar | 8 % dold | 29 % dold, kroppen 14 %, streck över kroppen, armen klipps |
| 10 | Tåg | 59 | 2 | svävar | 11 % dold, kroppen 3 %, streck över kroppen, armen klipps | 18 % dold, kroppen 11 %, streck över kroppen |
| 11 | Tåg 2 | 21 | 1 | armen klipps, svävar | 11 % dold, kroppen 3 %, streck över kroppen | 11 % dold, kroppen 2 %, streck över kroppen |
| 12 | Båt | 32 | 17 | 5 % dold | 8 % dold | 24 % dold, kroppen 14 %, streck över kroppen |
| 13 | Båt 2 | 37 | 19 | 23 % dold, kroppen 8 %, streck över kroppen, armen klipps | 12 % dold | 16 % dold, streck över kroppen |
| 14 | Stort flygplan | 66 | 6 | 20 % dold, kroppen 10 %, streck över kroppen, armen klipps | 8 % dold, streck över kroppen | 12 % dold, kroppen 4 %, streck över kroppen |
| 15 | Stort flygplan 2 | 34 | 3 | 8 % dold, streck över kroppen | 9 % dold, streck över kroppen | 25 % dold, kroppen 18 %, streck över kroppen |
| 16 | Raket | 78 | 12 | 17 % dold, kroppen 11 %, streck över kroppen | utanför bilden, 11 % dold, kroppen 4 %, streck över kroppen | 17 % dold, kroppen 11 %, streck över kroppen (krockar: keiws+rod) |
| 17 | Segelbåt | 23 | 18 | utanför bilden, 20 % dold, kroppen 14 %, streck över kroppen | 16 % dold, kroppen 9 %, streck över kroppen, armen klipps | 14 % dold, kroppen 4 %, streck över kroppen, armen klipps |
| 18 | Segelbåt 2 | 42 | 15 | 20 % dold, kroppen 14 %, streck över kroppen | 19 % dold, kroppen 8 %, streck över kroppen, armen klipps | 10 % dold |
| 19 | Polisbil | 29 | 11 | 10 % dold, armen klipps | 10 % dold, kroppen 3 %, streck över kroppen | 7 % dold, armen klipps |
| 20 | Polisbil 2 | 55 | 2 | 16 % dold, kroppen 6 %, streck över kroppen | 9 % dold, kroppen 2 %, streck över kroppen | 13 % dold, kroppen 6 %, streck över kroppen, svävar |
| 21 | Polisbil 3 | 44 | 15 | 12 % dold, streck över kroppen | 18 % dold, kroppen 12 %, streck över kroppen | 11 % dold |
| 22 | Ambulans | 63 | 1 | 25 % dold, kroppen 16 %, streck över kroppen | 17 % dold, kroppen 11 %, streck över kroppen, armen klipps | 8 % dold |
| 23 | Ambulans 2 | 28 | 1 | 16 % dold, kroppen 6 %, streck över kroppen, armen klipps | 14 % dold, kroppen 7 %, streck över kroppen | 18 % dold, kroppen 11 %, streck över kroppen, armen klipps |
| 25 | Betongbil 2 | 55 | 9 | 15 % dold, armen klipps | 8 % dold, armen klipps | 19 % dold, kroppen 13 %, streck över kroppen, armen klipps |
| 26 | Kranbil | 31 | 4 | 13 % dold, streck över kroppen, armen klipps | 13 % dold, kroppen 7 %, streck över kroppen | 18 % dold, kroppen 10 %, streck över kroppen |
| 27 | Kranbil 2 | 95 | 8 | 21 % dold, kroppen 10 %, streck över kroppen, armen klipps | 13 % dold, kroppen 2 %, streck över kroppen, armen klipps | 9 % dold, streck över kroppen |
| 28 | Buss | 2 | 14 | 15 % dold, armen klipps | 12 % dold | 9 % dold, kroppen 3 %, streck över kroppen |
| 29 | Buss 2 | 68 | 3 | 8 % dold | utanför bilden, 19 % dold, kroppen 8 %, streck över kroppen | 12 % dold, kroppen 5 %, streck över kroppen |
| 30 | Brandbil | 73 | 27 | 9 % dold | 8 % dold, streck över kroppen | 12 % dold, streck över kroppen, armen klipps |
| 31 | Brandbil 2 | 86 | 3 | 26 % dold, kroppen 13 %, streck över kroppen, armen klipps | 8 % dold, streck över kroppen | utanför bilden, 14 % dold, kroppen 7 %, streck över kroppen |
| 32 | Dumper | 20 | 3 | 14 % dold | 15 % dold, kroppen 4 %, streck över kroppen, armen klipps | utanför bilden, 8 % dold |
| 33 | Dumper 2 | 39 | 4 | 15 % dold, armen klipps | 8 % dold, armen klipps | 14 % dold, kroppen 3 %, streck över kroppen, armen klipps |
| 34 | Stort flygplan 3 | 23 | 4 | 18 % dold, streck över kroppen, armen klipps | 9 % dold | 13 % dold, kroppen 6 %, streck över kroppen |
| 35 | Stort flygplan 4 | 78 | 6 | utanför bilden, 8 % dold | 18 % dold, kroppen 12 %, streck över kroppen | 21 % dold, kroppen 14 %, streck över kroppen |
| 36 | Sopbil 3 | 64 | 3 | 16 % dold, kroppen 4 %, streck över kroppen, armen klipps | 13 % dold | 8 % dold, armen klipps |
| 37 | Sopbil 4 | 98 | 3 | 20 % dold, kroppen 10 %, streck över kroppen, armen klipps | 8 % dold | 11 % dold, kroppen 4 %, streck över kroppen, armen klipps |
| 38 | Flygplan 3 | 34 | 9 | 12 % dold, kroppen 5 %, streck över kroppen | 8 % dold | 21 % dold, kroppen 10 %, streck över kroppen |
| 39 | Flygplan 4 | 33 | 2 | 9 % dold | 15 % dold, kroppen 10 %, streck över kroppen | 16 % dold, kroppen 9 %, streck över kroppen |
| 40 | Flygplan 5 | 18 | 17 | 11 % dold, kroppen 5 %, streck över kroppen, armen klipps | 9 % dold, streck över kroppen | 17 % dold, kroppen 11 %, streck över kroppen |
| 41 | Grävare 2 | 71 | 26 | 14 % dold, armen klipps | 19 % dold, kroppen 13 %, streck över kroppen | 8 % dold, armen klipps |
| 42 | Grävare 3 | 48 | 3 | 16 % dold, kroppen 2 %, streck över kroppen, armen klipps | 8 % dold | 14 % dold, kroppen 8 %, streck över kroppen |
| 43 | Traktor 3 | 20 | 9 | 13 % dold, streck över kroppen, armen klipps | 8 % dold | 10 % dold, streck över kroppen |
| 46 | Raket 2 | 73 | 20 | 22 % dold, kroppen 10 %, streck över kroppen, armen klipps | utanför bilden, 10 % dold, kroppen 3 %, streck över kroppen | 15 % dold, kroppen 9 %, streck över kroppen |
| 47 | Raket 3 | 54 | 26 | 19 % dold, kroppen 11 %, streck över kroppen | 12 % dold, kroppen 6 %, streck över kroppen | 23 % dold, kroppen 17 %, streck över kroppen |
| 50 | Flygplan 6 | 10 | 11 | 16 % dold, kroppen 5 %, streck över kroppen | 12 % dold, kroppen 4 %, streck över kroppen | 10 % dold, kroppen 3 %, streck över kroppen |
| 52 | Stort flygplan 5 | 17 | 19 | utanför bilden, 10 % dold, kroppen 2 %, streck över kroppen | 21 % dold, kroppen 11 %, streck över kroppen, armen klipps | 22 % dold, kroppen 14 %, streck över kroppen, armen klipps |
| 54 | Traktor 6 | 31 | 29 | 20 % dold, kroppen 14 %, streck över kroppen | utanför bilden, 8 % dold | 22 % dold, kroppen 15 %, streck över kroppen, armen klipps |
| 64 | Skördetröska | 27 | 39 | 11 % dold, kroppen 3 %, streck över kroppen | utanför bilden, 7 % dold | 11 % dold, kroppen 4 %, streck över kroppen, armen klipps |
| 69 | Traktor 7 | 27 | 52 | utanför bilden, 17 % dold, kroppen 6 %, streck över kroppen, armen klipps | 16 % dold, kroppen 9 %, streck över kroppen, armen klipps | 20 % dold, kroppen 14 %, streck över kroppen |
| 106 | Traktor 8 | 17 | 5 | 42 % dold, kroppen 38 %, streck över kroppen | 9 % dold, streck över kroppen | utanför bilden, 7 % dold |
| 107 | Traktor 9 | 84 | 9 | 36 % dold, kroppen 28 %, streck över kroppen | 21 % dold, kroppen 15 %, streck över kroppen, armen klipps | 8 % dold |
| 108 | Traktor 10 | 282 | 87 | 17 % dold, kroppen 14 %, streck över kroppen | 8 % dold | 14 % dold, kroppen 7 %, streck över kroppen |
| 109 | Betongbil 4 | 93 | 9 | 10 % dold, kroppen 2 %, streck över kroppen | 11 % dold, kroppen 3 %, streck över kroppen | 8 % dold, streck över kroppen |
| 111 | Ambulans 4 | 24 | 11 | 4 % dold, streck över kroppen, svävar | 11 % dold, kroppen 3 %, streck över kroppen | utanför bilden, 17 % dold, kroppen 10 %, streck över kroppen |
| 113 | Stort flygplan 6 | 28 | 9 | 16 % dold, kroppen 4 %, streck över kroppen, armen klipps | 8 % dold | 14 % dold, kroppen 2 %, streck över kroppen, armen klipps |
| 114 | Plogbil 2 | 13 | 14 | armen klipps, svävar | 7 % dold | 16 % dold, kroppen 9 %, streck över kroppen |
| 115 | Plogbil 3 | 14 | 27 | armen klipps, svävar | 8 % dold | 15 % dold, kroppen 8 %, streck över kroppen |
| 116 | Bärgningsbil 2 | 15 | 11 | armen klipps, svävar | 9 % dold, kroppen 3 %, streck över kroppen | 18 % dold, kroppen 6 %, streck över kroppen, armen klipps |
| 117 | Bärgningsbil 3 | 14 | 15 | armen klipps, svävar | 12 % dold, kroppen 6 %, streck över kroppen | 24 % dold, kroppen 15 %, streck över kroppen |
| 118 | Traktor 11 | 35 | 40 | 12 % dold, streck över kroppen, armen klipps | 12 % dold, kroppen 6 %, streck över kroppen | 10 % dold, armen klipps |
| 119 | Traktor 12 | 12 | 30 | 12 % dold, kroppen 3 %, streck över kroppen, armen klipps | 11 % dold, kroppen 4 %, streck över kroppen | 11 % dold, kroppen 3 %, streck över kroppen |
| 120 | Traktor 13 | 50 | 48 | 24 % dold, kroppen 12 %, streck över kroppen, armen klipps | 15 % dold, kroppen 5 %, streck över kroppen | 15 % dold, kroppen 8 %, streck över kroppen, armen klipps |
| 121 | Hjullastare | 49 | 21 | 17 % dold, kroppen 4 %, streck över kroppen, armen klipps | 8 % dold | 19 % dold, kroppen 14 %, streck över kroppen |
| 122 | Hjullastare 2 | 12 | 25 | 15 % dold, kroppen 2 %, streck över kroppen, armen klipps | 9 % dold, streck över kroppen | 23 % dold, kroppen 14 %, streck över kroppen |
| 123 | Hjullastare 3 | 15 | 21 | 21 % dold, kroppen 10 %, streck över kroppen, armen klipps | 14 % dold, kroppen 3 %, streck över kroppen | 16 % dold, kroppen 5 %, streck över kroppen |
| 124 | Hjullastare 4 | 16 | 20 | 12 % dold, streck över kroppen, armen klipps | 13 % dold, kroppen 6 %, streck över kroppen | 15 % dold, kroppen 9 %, streck över kroppen |
| 125 | Brandbil 6 | 4 | 9 | 17 % dold, kroppen 2 %, streck över kroppen | 8 % dold | 10 % dold, kroppen 4 %, streck över kroppen |
| 126 | Tankbil | 8 | 29 | 8 % dold | 10 % dold | 13 % dold, kroppen 5 %, streck över kroppen |
| 127 | Tankbil 2 | 12 | 20 | 37 % dold, kroppen 34 %, streck över kroppen | 10 % dold, streck över kroppen | 8 % dold, streck över kroppen |
| 128 | Tankbil 3 | 6 | 15 | 35 % dold, kroppen 31 %, streck över kroppen | 28 % dold, kroppen 14 %, streck över kroppen | 23 % dold, kroppen 10 %, streck över kroppen, armen klipps |
| 129 | Tankbil 4 | 14 | 24 | 24 % dold, kroppen 17 %, streck över kroppen | 24 % dold, kroppen 15 %, streck över kroppen | 20 % dold, kroppen 13 %, streck över kroppen |
| 130 | Brandbil 7 | 22 | 16 | 13 % dold, kroppen 3 %, streck över kroppen | 13 % dold, kroppen 3 %, streck över kroppen, armen klipps | 22 % dold, kroppen 13 %, streck över kroppen |
| 131 | Brandbil 8 | 17 | 15 | 18 % dold, kroppen 12 %, streck över kroppen | 9 % dold, streck över kroppen | 15 % dold, kroppen 2 %, streck över kroppen, armen klipps |
| 132 | Glassbil | 7 | 41 | 30 % dold, kroppen 26 %, streck över kroppen | 22 % dold, kroppen 13 %, streck över kroppen, armen klipps | 12 % dold, kroppen 5 %, streck över kroppen |
| 133 | Glassbil 2 | 11 | 21 | 26 % dold, kroppen 18 %, streck över kroppen, armen klipps | 17 % dold, kroppen 6 %, streck över kroppen, armen klipps | 10 % dold, kroppen 2 %, streck över kroppen |
| 134 | Glassbil 3 | 23 | 19 | 11 % dold, kroppen 2 %, streck över kroppen, armen klipps | 17 % dold, kroppen 6 %, streck över kroppen, armen klipps | 21 % dold, kroppen 14 %, streck över kroppen, armen klipps |
| 135 | Glassbil 4 | 5 | 5 | 10 % dold | 9 % dold, streck över kroppen | 13 % dold, kroppen 6 %, streck över kroppen |
| 136 | Glassbil 5 | 4 | 7 | 15 % dold, kroppen 2 %, streck över kroppen | 8 % dold, streck över kroppen | 19 % dold, kroppen 13 %, streck över kroppen |
| 137 | Skördetröska 2 | 6 | 4 | 9 % dold, armen klipps | 19 % dold, kroppen 13 %, streck över kroppen | 29 % dold, kroppen 15 %, streck över kroppen, armen klipps |
| 138 | Skördetröska 3 | 19 | 34 | 42 % dold, kroppen 37 %, streck över kroppen, armen klipps, svävar | 12 % dold, streck över kroppen | 23 % dold, kroppen 15 %, streck över kroppen |
| 139 | Skördetröska 4 | 31 | 20 | 19 % dold, kroppen 4 %, streck över kroppen, armen klipps | 18 % dold, kroppen 12 %, streck över kroppen, armen klipps | 22 % dold, kroppen 14 %, streck över kroppen, armen klipps |
| 140 | Skördetröska 5 | 14 | 18 | 25 % dold, kroppen 18 %, streck över kroppen, armen klipps | 11 % dold, kroppen 3 %, streck över kroppen | 21 % dold, kroppen 8 %, streck över kroppen, armen klipps |
| 141 | Skördetröska 6 | 7 | 10 | 48 % dold, kroppen 41 %, streck över kroppen, armen klipps | 22 % dold, kroppen 12 %, streck över kroppen | 20 % dold, kroppen 14 %, streck över kroppen, armen klipps |
| 142 | Skördetröska 7 | 1 | 4 | 2 % dold | utanför bilden, 22 % dold, kroppen 13 %, streck över kroppen, armen klipps | 12 % dold, kroppen 7 %, streck över kroppen, svävar |
| 143 | Skördetröska 8 | 1 | 4 | 8 % dold | 8 % dold | svävar |
| 144 | Skördetröska 9 | 4 | 2 | 49 % dold, kroppen 46 %, streck över kroppen, armen klipps | 21 % dold, kroppen 11 %, streck över kroppen, armen klipps | 8 % dold, streck över kroppen |
| 145 | Skördetröska 10 | 22 | 9 | 22 % dold, kroppen 22 %, streck över kroppen, armen klipps | 21 % dold, kroppen 9 %, streck över kroppen | 17 % dold, kroppen 11 %, streck över kroppen |
| 146 | Skördetröska 11 | 12 | 15 | 15 % dold, kroppen 7 %, streck över kroppen, armen klipps | 23 % dold, kroppen 12 %, streck över kroppen | 15 % dold, kroppen 7 %, streck över kroppen |
