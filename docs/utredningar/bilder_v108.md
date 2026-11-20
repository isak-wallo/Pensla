# Bilderna, Pensla v108-test: nagelfarning

Datum: 2026-11-20. Grenen `jobb/figurer-v108`. Figurerna har en egen rapport, `figurer_v108.md`.

Rubriker märkta **(spoilerfri)** säger inget om var figurerna gömmer sig. Den här rapporten handlar om linjerna, ytorna, färgbilderna och formatet, så den nämner inga gömställen.

## Sammanfattning (spoilerfri)

- Alla 84 aktiva bilder är genomgångna, både med mätning (`bildoversyn.py`, som nu också räknar ytorna) och med ögonen (färgbild och konturer bredvid varandra, och hörnen förstorade).
- **Rättat:** fyra bilder var beskurna så att fordonet klipptes av, och de visas nu i hela sitt format: Flygplan 6 (50), Stort flygplan 5 (52), Skördetröska (64) och Traktor 7 (69). Före/efter-bilder finns i `bilder_v108/`.
- **Inga fel i färgbilderna.** Det finns inga Gemini-vattenmärken i hörnen, ingen text, inga trasiga toningar eller JPEG-skräp som syns i normal storlek.
- **Linjerna** har glapp i alla bilder (2984 totalt, median 26 per bild). I webbappen syns de inte, eftersom färgen tas pixel för pixel ur färgbilden. De spelar roll först för vektorbilderna (Pensla N), där `vektorbild.py` sluter dem.
- **En bild behöver bytas:** Traktor 10 (108). Den har 282 glapp och 87 lösa streck, och däcken är spårade i småbitar. Prompten står nedan.

## Hur det gjordes (spoilerfri)

- `python verktyg/bildoversyn.py` mäter:
  - glapp och lösa streck (som förut);
  - **små ytor**: ytor under 60 px, för små att se eller måla;
  - **remsor**: ytor som ingenstans är bredare än 5 px, alltså dubbla eller fransiga konturer;
  - **linjeandel**: hur stor del av bilden som är linje, ett mått på hur tät bilden är.
- Ögonen: ett ark per åtta bilder, med färgbilden och konturerna (med glappen markerade) bredvid varandra. Dessutom förstorades alla nedre hörn för att leta efter vattenmärken.
- Beskärningen: förlagorna jämfördes med 4:3-rutan i `BESKAR_4_3` (`fargbild.py`).

## Rättat (spoilerfri)

| Nr | Bild | Problem | Åtgärd |
|---|---|---|---|
| 50 | Flygplan 6 | Beskärningen till 4:3 klippte av vingspetsen och vindstrutens stolpe | Ur `BESKAR_4_3`, nu 1350 × 900 |
| 52 | Stort flygplan 5 | Bagagevagnen till vänster klipptes mitt itu | Samma |
| 64 | Skördetröska | Skärbordets vänstra ände klipptes av | Samma |
| 69 | Traktor 7 | Vagnens bakre ände klipptes av | Samma |

- `fargbild.py` gav exakt samma SVG när den kördes om på en oförändrad förlaga (kontrollerat på flygplan6), så omspårningen ändrar inget annat än formatet.
- Figurerna flyttades 75 px åt höger (85 px i förlagan × 900/1024). I Skördetröska ändrades linjerna nära himlen lite, och därför justerades två figurer så att armen syns helt (figurgranskningen: inga varningar). I Traktor 7 syns keIWs kropp till 62 % (förut 70 %) men fötterna är nu helt dolda, och där lämnades platsen.
- Före/efter: `docs/utredningar/bilder_v108/format-*.jpg`.

## Kvar, går inte att rätta i verktygen (spoilerfri)

- **Glapp i linjerna (2984).** De syns inte på webben. De värsta (över 60) är:
  - Traktor 10 (282), Sopbil 4 (98), Kranbil 2 (95), Betongbil 4 (93), Brandbil 2 (86), Traktor 9 (84);
  - Raket och Stort flygplan 4 (78 var), Brandbil och Raket 2 (73 var), Grävare 2 (71), Buss 2 (68), Stort flygplan (66), Sopbil 3 (64), Ambulans (63).

  Glappen sitter mest i däckmönster, buskar och gräs. Att spåra om med andra inställningar ger ofta fler streck i stället. För vektorbilderna sluter `vektorbild.py` glappen.
- **Lösa streck.** Mest glans och mönster i däck, gräs och vete. Flest har:
  - Traktor 10 (87), Traktor 7 (59), Traktor 13 (48), Glassbil (41), Traktor 11 (40), Skördetröska 3 (34), Skördetröska (32), Traktor 12 (30).

  Strecken i fälten i Skördetröska 3 och 4 finns också i färgbilden, som fåror. De kan tas bort med `BORT` i `fargbild.py` om Isak tycker att de stör. Punkterna står i `granskning/oversyn/NAMN.png` (orange ringar).
- **Små ytor.** Mest i vete, gräs och däck: Skördetröska (117), Skördetröska 4 (111), Traktor 7 (106), Traktor 11 (76), Hjullastare 3 (65), Brandbil 7 och Skördetröska 3 (55 var). De stör inte målandet, eftersom penseln tar färgen pixel för pixel.
- **Remsor (dubbla eller fransiga konturer):** 110 totalt och högst 13 per bild (Skördetröska 4). Ingen bild sticker ut.
- **Bakgrund utan kontur.** Många av Geminis kullar och moln har ingen mörk kontur. På webben syns det inte. I vektorbilderna blir de egna färgytor (`fargytor` i `vektorbild.py`).

## Kräver en ny bild (spoilerfri)

**Traktor 10 (108).**
- Problem: däcken och hytten är spårade i hundratals småbitar (282 glapp, 87 lösa streck, 41 små ytor, linjeandel 10,1 %, den tätaste bilden).
- Förslag: byt mot en ny bild i GPT-stilen (CLAUDE.md), som spåras med `TECKNING`. Prompt (samma mall som bärgningsbilen; ändra bara fordonet och miljön):

```
A playful but slightly more realistic picture-book illustration for small children: a big modern red farm tractor with a cab driving along a dirt road between green fields, seen from the side at a slight three-quarter angle. Realistic proportions: a cab with big windows, a long hood with a grille, big back wheels and smaller front wheels, an exhaust pipe, but still friendly and softly rounded, not a toy. Landscape format 16:10, wider than tall, the whole tractor visible with space around it.

Style rules (important):
- Bold, clean, smooth outlines in near-black around EVERY shape, all the same thickness, in the foreground AND the background: hills, trees, fence, road, clouds, the sun and each sun ray all get the same bold outline. No thin, light or colored lines anywhere.
- Every area must be fully closed by outlines, no gaps.
- Only the outlines are black. All fill colors are lighter: tires and dark parts are medium gray, never black or dark navy.
- Mostly flat colors: each area has one main color with at most a very soft, light highlight. No strong gradients, no shading bands, no dark shadows along outlines, no shadows on the ground under the tractor.
- Tires with a few large, simple tread blocks (at most 8 visible per tire), each block a closed shape. No small lugs, no ribbed or accordion details, no panel lines, bolts or rivets.
- A bit more detail than a toy (a seat and steering wheel in the cab, side mirrors, headlights, a step), but no tiny enclosed areas. No grilles with many slots.
- The road is one plain area, no stones or gravel dots.
- Background: rolling green hills, a few big round trees, a red barn, a simple wooden fence, light blue sky with a few big puffy clouds and a sun. Keep background objects large and simple, no other vehicles.
- No people, no animals, no text, no letters, no logos, no frame, no signature, no paper texture.
```

**Om Pensla N ska ha rena vektorer av alla bilder:** Sopbil 4, Kranbil 2, Betongbil 4, Brandbil 2 och Traktor 9 har också över 80 glapp. Webben klarar sig med dem som de är, men de kan bytas mot nya bilder med samma mall (fordon och miljö som i dag). Se också avsnittet om vektorbilderna i `vektor_v108.md`.

## Tabell: alla aktiva bilder efter v108 (spoilerfri)

Glapp och lösa streck som i `bildoversyn.md`. Små ytor = under 60 px. Remsor = ytor som ingenstans är bredare än 5 px. Linje % = andel linje.

| Nr | Bild | Glapp | Lösa streck | Små ytor | Remsor | Linje % |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 4 | Sopbil snett | 46 | 19 | 2 | 0 | 8.6 |
| 6 | Flygplan | 28 | 2 | 1 | 0 | 3.6 |
| 7 | Flygplan 2 | 32 | 9 | 1 | 0 | 5.2 |
| 8 | Helikopter | 36 | 1 | 1 | 0 | 6.6 |
| 9 | Helikopter 2 | 15 | 2 | 0 | 0 | 6.1 |
| 10 | Tåg | 59 | 2 | 8 | 3 | 6.7 |
| 11 | Tåg 2 | 21 | 1 | 9 | 3 | 5.0 |
| 12 | Båt | 32 | 17 | 0 | 0 | 5.6 |
| 13 | Båt 2 | 37 | 19 | 1 | 0 | 4.8 |
| 14 | Stort flygplan | 66 | 6 | 0 | 0 | 5.4 |
| 15 | Stort flygplan 2 | 34 | 3 | 2 | 0 | 6.0 |
| 16 | Raket | 78 | 12 | 6 | 0 | 3.8 |
| 17 | Segelbåt | 23 | 18 | 2 | 1 | 4.5 |
| 18 | Segelbåt 2 | 42 | 15 | 2 | 0 | 4.8 |
| 19 | Polisbil | 29 | 11 | 0 | 0 | 7.0 |
| 20 | Polisbil 2 | 55 | 2 | 3 | 0 | 4.3 |
| 21 | Polisbil 3 | 44 | 15 | 1 | 0 | 7.7 |
| 22 | Ambulans | 63 | 1 | 0 | 0 | 4.8 |
| 23 | Ambulans 2 | 28 | 1 | 0 | 0 | 5.6 |
| 25 | Betongbil 2 | 55 | 9 | 5 | 0 | 6.0 |
| 26 | Kranbil | 31 | 4 | 1 | 0 | 6.0 |
| 27 | Kranbil 2 | 95 | 8 | 1 | 0 | 5.1 |
| 28 | Buss | 2 | 14 | 1 | 0 | 5.6 |
| 29 | Buss 2 | 68 | 3 | 4 | 0 | 5.8 |
| 30 | Brandbil | 73 | 27 | 2 | 0 | 5.3 |
| 31 | Brandbil 2 | 86 | 3 | 1 | 0 | 6.8 |
| 32 | Dumper | 20 | 3 | 1 | 0 | 6.7 |
| 33 | Dumper 2 | 39 | 4 | 0 | 0 | 5.1 |
| 34 | Stort flygplan 3 | 23 | 4 | 3 | 0 | 5.6 |
| 35 | Stort flygplan 4 | 78 | 6 | 2 | 0 | 3.6 |
| 36 | Sopbil 3 | 64 | 3 | 1 | 0 | 7.0 |
| 37 | Sopbil 4 | 98 | 3 | 2 | 0 | 5.2 |
| 38 | Flygplan 3 | 34 | 9 | 0 | 0 | 5.9 |
| 39 | Flygplan 4 | 33 | 2 | 1 | 0 | 5.1 |
| 40 | Flygplan 5 | 18 | 17 | 3 | 0 | 3.9 |
| 41 | Grävare 2 | 71 | 26 | 0 | 0 | 5.3 |
| 42 | Grävare 3 | 48 | 3 | 0 | 0 | 5.5 |
| 43 | Traktor 3 | 20 | 9 | 0 | 0 | 6.1 |
| 46 | Raket 2 | 73 | 20 | 0 | 0 | 5.6 |
| 47 | Raket 3 | 54 | 26 | 8 | 4 | 4.2 |
| 50 | Flygplan 6 | 11 | 10 | 19 | 5 | 6.0 |
| 52 | Stort flygplan 5 | 16 | 19 | 21 | 5 | 8.3 |
| 54 | Traktor 6 | 31 | 29 | 40 | 5 | 8.3 |
| 64 | Skördetröska | 27 | 32 | 117 | 6 | 8.1 |
| 69 | Traktor 7 | 25 | 59 | 106 | 4 | 8.6 |
| 106 | Traktor 8 | 17 | 5 | 3 | 0 | 9.1 |
| 107 | Traktor 9 | 84 | 9 | 13 | 3 | 8.9 |
| 108 | Traktor 10 | 282 | 87 | 41 | 1 | 10.1 |
| 109 | Betongbil 4 | 93 | 9 | 8 | 5 | 7.2 |
| 111 | Ambulans 4 | 24 | 11 | 7 | 3 | 5.9 |
| 113 | Stort flygplan 6 | 28 | 9 | 17 | 2 | 7.9 |
| 114 | Plogbil 2 | 13 | 14 | 36 | 1 | 7.8 |
| 115 | Plogbil 3 | 14 | 27 | 16 | 2 | 8.2 |
| 116 | Bärgningsbil 2 | 15 | 11 | 9 | 1 | 8.2 |
| 117 | Bärgningsbil 3 | 14 | 15 | 20 | 0 | 7.5 |
| 118 | Traktor 11 | 35 | 40 | 76 | 1 | 8.2 |
| 119 | Traktor 12 | 12 | 30 | 21 | 0 | 7.7 |
| 120 | Traktor 13 | 50 | 48 | 44 | 3 | 9.0 |
| 121 | Hjullastare | 49 | 21 | 18 | 2 | 7.3 |
| 122 | Hjullastare 2 | 12 | 25 | 33 | 5 | 8.0 |
| 123 | Hjullastare 3 | 15 | 21 | 65 | 3 | 8.5 |
| 124 | Hjullastare 4 | 16 | 20 | 37 | 2 | 7.7 |
| 125 | Brandbil 6 | 4 | 9 | 8 | 1 | 6.0 |
| 126 | Tankbil | 8 | 29 | 2 | 0 | 5.9 |
| 127 | Tankbil 2 | 12 | 20 | 8 | 0 | 7.1 |
| 128 | Tankbil 3 | 6 | 15 | 24 | 2 | 7.2 |
| 129 | Tankbil 4 | 14 | 24 | 17 | 3 | 7.2 |
| 130 | Brandbil 7 | 22 | 16 | 55 | 4 | 8.8 |
| 131 | Brandbil 8 | 17 | 15 | 28 | 4 | 8.6 |
| 132 | Glassbil | 7 | 41 | 29 | 3 | 7.2 |
| 133 | Glassbil 2 | 11 | 21 | 16 | 0 | 7.3 |
| 134 | Glassbil 3 | 23 | 19 | 20 | 3 | 7.7 |
| 135 | Glassbil 4 | 5 | 5 | 10 | 0 | 6.4 |
| 136 | Glassbil 5 | 4 | 7 | 8 | 3 | 5.9 |
| 137 | Skördetröska 2 | 6 | 4 | 7 | 0 | 5.2 |
| 138 | Skördetröska 3 | 19 | 34 | 55 | 2 | 7.1 |
| 139 | Skördetröska 4 | 31 | 20 | 111 | 13 | 7.9 |
| 140 | Skördetröska 5 | 14 | 18 | 16 | 0 | 6.3 |
| 141 | Skördetröska 6 | 7 | 10 | 15 | 0 | 5.6 |
| 142 | Skördetröska 7 | 1 | 4 | 6 | 0 | 5.2 |
| 143 | Skördetröska 8 | 1 | 4 | 7 | 0 | 5.9 |
| 144 | Skördetröska 9 | 4 | 2 | 14 | 1 | 6.2 |
| 145 | Skördetröska 10 | 22 | 9 | 16 | 0 | 6.0 |
| 146 | Skördetröska 11 | 12 | 15 | 12 | 1 | 6.3 |
