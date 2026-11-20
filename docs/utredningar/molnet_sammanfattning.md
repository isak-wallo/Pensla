# Arbetet i molnet: Pensla

Datum: 2026-11-20. Grenen `jobb/sammanfattning` utgår från `origin/main` (1d7554a).

## Kort sammanfattning (spoilerfri)

- **Allt är ihopslaget i main.** Båda Pensla-jobben i molnet, `jobb/speltest-figurer` (v107) och `jobb/figurer-v108` (v108), finns där. Main står på v109-test. Där tog ägaren också bort Traktor 10 ur appen, så det finns nu 83 aktiva bilder.
- **v107** granskade alla figurer, både stilla och vinkande. Armen syns i alla, men 13 figurer var dåliga.
- **v108:**
  - flyttade 27 figurer, och efter det svävar bara en figur (förut 16);
  - gjorde fotmåttet till en varning i granskningen;
  - gick igenom alla aktiva bilder (linjer, ytor, färger och format) och rättade formatet på fyra;
  - gjorde vektor-JSON till Pensla N av alla aktiva bilder, och alla klarade kontrollen.
- **Inget är halvfärdigt i koden.** Det som återstår är beslut och granskning med ögonen. Listan finns nedan.

## Jobben och grenarna (spoilerfri)

| Jobb | Gren | Status | I main? |
|---|---|---|---|
| Figurgranskning v107 (och vinkarmen före den) | `jobb/speltest-figurer` (spets aa18d92) | Klart | Ja |
| Figurer, bildgenomgång och vektorbilder v108 | `jobb/figurer-v108` (spets 1d21247) | Klart | Ja |
| Traktor 10 borttagen, v109-test | direkt i main (1d7554a) | Klart | Ja |

**v107 (`jobb/speltest-figurer`):**
- `cc64ede`: vinkarmen syns (104 figurer i 66 bilder fick mindre s eller ny plats) och verktyget `verktyg/vinkarm.py`.
- `aa18d92`: figurgranskningen av alla 252 figurer, med `verktyg/figurgranskning.py` och rapporten `docs/utredningar/figurgranskning_v107.md`.
  - Resultat: 13 dåliga figurer, var och en med ett förslag (`forslag.json`), och ungefär 25 svaga.
- Förslagen fördes in i v108.
- Grenen innehåller inget speltest utöver granskningen, och alltså inget som är halvfärdigt.

**v108 (`jobb/figurer-v108`):**
- **Figurerna:** de 13 förslagen och 14 nya förbättringar är införda. Svävande figurer (fötterna syns till mer än 50 %) gick från 16 till 1, och figurer där armen syns till minst 99 % från 139 till 157. Rapport: `figurer_v108.md`.
- **Verktygen:**
  - fotmåttet är en varning (SVÄVAR) i `figurgranskning.py` och `vinkarm.py`;
  - skripten går nu också på Linux;
  - `aktiva.py` klarar versioner med ändelse, som v108-test.
- **Genomgången av bilderna:**
  - Alla aktiva bilder är mätta (glapp, lösa streck, små ytor, remsor och linjeandel) och granskade med ögonen.
  - Fyra Copilot-bilder visas nu i hela sitt format (50, 52, 64 och 69), eftersom beskärningen klippte av fordonet.
  - Inga fel hittades i färgbilderna.
  - Rapport: `bilder_v108.md`.
- **Vektorbilderna:**
  - `jobb/vektor3` slogs ihop utan konflikter.
  - Alla aktiva bilder finns som JSON i `native/bilder/` och klarar `--kontroll`. Medel-ΔE är i snitt 1,85.
  - Storleken är 16,7 MB för 84 bilder, innan Traktor 10 togs bort.
  - Rapport: `vektor_v108.md`.

## Idéer, förslag och fynd som inte är byggda

Varje punkt gäller spelet **Pensla**. Storleken är uppskattad (liten, mellan, stor).

**Figurerna som lämnades (gömställen i texten)**

| Punkt | Motivering | Storlek | Rekommendation |
|---|---|---|---|
| Nr 4 keIWs svävar i framrutan (fot 92 %) | Den enda SVÄVAR som är kvar. Sänks han hamnar torkarbladet över kroppen, och platsen ovanför hytten är för nära gron | liten | ta in (välj en plats för hand, t.ex. bakom soptunnorna eller med mindre s) |
| 10 och 11 keIWs i lokets små fönster | Fötterna är dolda nu, men fönstren är fortfarande små. Platserna ute fick en kullinje över ansiktet | liten | kanske |
| 46 keIWs i det runda fönstret | Platserna ute hamnade framför fenorna | liten | kanske |
| 118, 119 och 129 keIWs med ratten över sig | Fötterna är redan dolda, och att sänka dem ändrade inget synligt | liten | nej |
| 127 och 133: gron står tätt intill rod | Förslagen bakom moln hamnade inne i molnet | liten | kanske |
| 13 rod mot det röda skrovet, 54 rod mot den röda motorhuven, 64 gron mot den gröna tröskan | Ingen bättre plats hittades med verktygen | mellan | kanske (för hand i galleriet) |
| 120 keIWs är liten bakom ladan (kropp 64 %) | Ingen bättre plats hittades | liten | kanske |
| 69 keIWs: kroppen syns till 62 % efter formatbytet (förut 70 %) | Fötterna är nu helt dolda | liten | nej |

**Bilderna**

| Punkt | Motivering | Storlek | Rekommendation |
|---|---|---|---|
| Ny bild i stället för 108 Traktor 10 | Ägaren har redan tagit bort den ur appen (v109-test). Prompten för en ny traktor i GPT-stilen står i `bilder_v108.md` och nedan | mellan | kanske (bara om en traktor till behövs) |
| Glappen i linjerna (2984 totalt, median 26 per bild) | Syns inte på webben, eftersom färgen tas pixel för pixel. Vektorbilderna sluter dem själva | stor | nej för webben |
| Fler än 80 glapp: Sopbil 4, Kranbil 2, Betongbil 4, Brandbil 2 och Traktor 9 | Kan bytas mot nya bilder med samma mall om vektorbilderna ser hackiga ut | stor | kanske |
| Lösa streck (mest glans och mönster i däck, gräs och vete; flest i Traktor 7, 13 och 11, Glassbil och Skördetröska 3) | Kan tas bort med `BORT` i `fargbild.py`. Strecken i fälten i Skördetröska 3 och 4 är fåror som också finns i färgbilden | mellan | kanske, bara där Isak tycker att de stör |
| Små ytor (vete, gräs, däck) | Stör inte målandet | – | nej |

**Vektorbilderna (Pensla N)**

| Punkt | Motivering | Storlek | Rekommendation |
|---|---|---|---|
| Lösare gränser i `BILDINST` för fyra bilder | Dumper: toning över mer kulör. Skördetröska: 48 färger och 4 % tillåtna felpixlar (förut 3 %). Traktor 6 och 7: en liten yta får ha ΔE 15 (förut 10). Det syns bara som ett litet träd, ett hjulnav eller en strimma i vetet med fel färg | liten | ta in som det är, och titta på de fyra i plattan |
| Ändrad regel för fria ändar i `--kontroll` | Sporrar kortare än två linjebredder, och ändar inne i en fylld klump (en prick på en antenn), räknas inte längre. De kan varken öppna eller stänga en yta, men regeln är lösare än förut | liten | ta in |
| Figurerna i vektorbilderna | Platserna är valda av skriptet `justera` utifrån webbens platser och bara granskade i småbilder. Där vektorlinjerna delar en yta annorlunda har figuren bytt yta, t.ex. en figur i Ambulans 2 | mellan | ta in, men titta på varje bild i plattan |
| Storleken: 16,7 MB JSON, högst 745 kB (Skördetröska) | Appen läser en bild åt gången, så 2 GB räcker. Vetebilderna och traktorerna med gräs är tyngst | liten | nej (inget behövs nu) |
| `native/bilder/` till pensla-native | Filerna ligger i Pensla-repot och ska kopieras till `pensla-native/app/src/main/assets/bilder/` hos keIWs | liten | ta in |

**Prompten för en ny traktor** (GPT-stilen, spåras med `TECKNING`):

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

## Öppna frågor till Isak (spoilerfri)

1. **Den sista svävande figuren:** ska den få en plats vald för hand, eller får den vara kvar?
2. **Figurerna i små fönster** (två tåg och en raket): räcker det att fötterna nu är dolda, eller ska de flyttas ut även om platserna där är sämre?
3. **Ny traktor:** ska det göras en ny bild med prompten ovan i stället för Traktor 10, eller räcker de andra traktorerna?
4. **Vektorbilderna:** ska de lösare gränserna (fyra bilder) och den nya regeln för fria ändar godtas? Vill du titta på alla vektorbilder i plattan innan de kopieras in i pensla-native?
5. **Bilder med många glapp:** ska de fem bytas mot nya, ifall de ser hackiga ut som vektorer?
6. **Lösa streck:** ska de tas bort med `BORT` i någon bild, och i så fall vilka?
7. **Släppet:** v109-test ligger på testsidan när den publiceras. Ska den släppas skarpt ("släpp"), och ska en ny APK byggas?
