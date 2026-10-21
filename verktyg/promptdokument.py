# Skriver promptar/copilot-bilder.docx: alla bildpromptar i ett dokument att ge
# till en bildgenerator (t.ex. Copilot). Lägg till nya bilder i BILDER.
# Kör: python verktyg/promptdokument.py (kräver python-docx).
from docx import Document
from docx.shared import Pt, Cm
import os
UT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'promptar') + os.sep

STIL = [
    "Bold, clean, smooth outlines in near-black around EVERY shape, all about the same thickness. Every area must be fully closed by outlines, no gaps.",
    "Only the outlines are black. All fill colors are lighter: {mork} are medium gray, never black.",
    "A soft, rounded 3D toy look: gentle light gradients and soft highlights give the shapes volume, but colors stay light, never cross an outline, and there are no dark shadows or dark bands along the outlines.",
]
SIST = "No people, no animals, no text, no letters, no logos, no frame, no signature, no paper texture."
FORMAT = "Landscape format 4:3, wider than tall, the whole {sak} visible with space around it."

# (rubrik, filnamn, motiv, sak, mörka delar, detaljrad, extra rader, bakgrund)
BILDER = [
    ("Traktor", "traktor", "a cute chubby red tractor with a cab, big back wheels and small front wheels, on a winding dirt road through green fields, seen from the side at a slight three-quarter angle.",
     "tractor", "tires and dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (cab windows, exhaust pipe, lights, steps) but no tiny enclosed areas; tire treads are few and large.", [],
     "rolling green hills, a few round trees, a small red barn, light blue sky with a few clouds and a sun."),
    ("Grävmaskin", "gravare", "a cute chunky yellow excavator with a cab, a bent arm and a bucket digging into a sand pile, on a construction site, seen from the side at a slight three-quarter angle.",
     "excavator", "tracks and dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (cab window, lights, track wheels) but no tiny enclosed areas; the tracks have only a few large wheels and no small tread pattern.", [],
     "a simple construction site with a sand pile, a few traffic cones and soft hills, light blue sky with a few clouds and a sun."),
    ("Litet flygplan", "flygplan", "a cute small propeller airplane with a big cockpit window, round side windows and chubby wheels, standing on a grass airfield, seen from the side at a slight three-quarter angle.",
     "airplane", "tires, propeller and dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (windows, propeller, tail) but no tiny enclosed areas.", [],
     "a grass airfield with a windsock, a small control tower and soft hills, light blue sky with a few clouds and a sun."),
    ("Sopbil", "sopbil", "a cute chunky green garbage truck with a rounded container body and a lifting arm at the back, next to a few colorful wheelie bins on a small town street, seen from the side at a slight three-quarter angle.",
     "truck", "tires and dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (cab windows, lights, mirrors, bins) but no tiny enclosed areas.", [],
     "a few colorful houses, round trees, a sidewalk, light blue sky with a few clouds and a sun."),
    ("Stort flygplan (lite mer verkligt)", "flygplan-stort3", "a big passenger jet airplane standing at an airport gate, seen from the side at a slight three-quarter angle. Realistic proportions: a long body, swept-back wings, two big engines under the wings, a tall tail fin and normal landing gear, but still friendly and softly rounded, not a toy.",
     "airplane", "tires and dark parts", "A bit more detail than a toy (cockpit windows, a row of passenger windows, a door, a colored stripe along the body, a colored tail), but no tiny enclosed areas: the passenger windows are round and not too small, and there are not too many of them.", [],
     "a simple airport with a terminal building with big windows, a control tower, a jet bridge connected to the airplane door, a runway and soft hills, light blue sky with a few clouds and a sun."),
    ("Kranbil", "kranbil", "a chunky mobile crane truck with a short folded crane arm and a hook, on a construction site, seen from the side at a slight three-quarter angle.",
     "truck", "tires and dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (cab windows, lights, steps) but no tiny enclosed areas; the crane arm is solid, not a lattice.", [],
     "a simple construction site with a few stacked blocks, traffic cones and soft hills, light blue sky with a few clouds and a sun."),
    ("Betongbil", "betongbil", "a cute cement mixer truck with a big round striped drum, on a construction site, seen from the side at a slight three-quarter angle.",
     "truck", "tires and dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (cab windows, lights, chute) but no tiny enclosed areas; the drum has only a few wide stripes.", [],
     "a simple construction site with a half-built wall, a sand pile and soft hills, light blue sky with a few clouds and a sun."),
    ("Ambulans", "ambulans", "a cute rounded ambulance, white with soft yellow and green panels, a simple red cross symbol and blue lights on the roof, parked in front of a small friendly hospital, seen from the side at a slight three-quarter angle.",
     "ambulance", "tires and dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (windows, doors, lights) but no tiny enclosed areas.", [],
     "a small friendly hospital building, a tree or two, light blue sky with a few clouds and a sun."),
    ("Polisbil", "polisbil", "a cute rounded police car, white and blue with a simple star on the door and blue lights on the roof, on a small town street, seen from the side at a slight three-quarter angle.",
     "car", "tires and dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (windows, door handles, lights) but no tiny enclosed areas.", [],
     "a few colorful houses, a small police station, a tree, light blue sky with a few clouds and a sun."),
    ("Segelbåt", "segelbat", "a cute little sailboat with a big rounded white sail, a small striped flag and a round window in the hull, on a calm lake, seen from the side at a slight three-quarter angle.",
     "boat", "dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail but no tiny enclosed areas; no thin ropes.",
     ["Water: calm, with a few simple outlined wave lines, no reflections and no sparkles."],
     "a small island with a red cottage and round trees, soft hills, light blue sky with a few clouds and a sun."),
    ("Raket", "raket", "a cute chubby rocket with round windows and three fins, standing on a simple launch pad, seen at a slight three-quarter angle.",
     "rocket", "dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (windows, fins, a few rivets drawn as dots) but no tiny enclosed areas; small soft clouds of smoke at the base, no flames.", [],
     "a grassy field with a small control building and soft hills, light blue sky with a few clouds, a sun and a pale moon."),
    ("Dumper", "dumper", "a big chunky dump truck with a raised-edge dump body full of rocks and sand, on a construction site, seen from the side at a slight three-quarter angle.",
     "truck", "big tires and dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (cab windows, lights, steps) but no tiny enclosed areas; rocks in the load are few and large.", [],
     "a simple construction site with a sand pile, a few traffic cones and soft hills, light blue sky with a few clouds and a sun."),
    ("Brandbil", "brandbil", "a cute red fire truck with a ladder on top, parked in front of a small fire station, seen from the side at a slight three-quarter angle.",
     "truck", "tires and dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (cab windows, hose reel, lights) but no tiny enclosed areas; the ladder has only a few wide rungs.", [],
     "a small friendly fire station, a tree or two, light blue sky with a few clouds and a sun."),
    ("Buss", "buss", "a cute round city bus with big windows, at a bus stop on a small town street, seen from the side at a slight three-quarter angle.",
     "bus", "tires and dark parts", "Cute rounded shapes, cartoon proportions, a bit of detail (doors, lights, mirrors) but no tiny enclosed areas.", [],
     "a few colorful houses, a bus stop shelter, a tree, light blue sky with a few clouds and a sun."),
]


def prompt(motiv, sak, mork, detalj, extra, bakgrund, verklig):
    start = ("A playful but slightly more realistic picture-book illustration for small children: " if verklig
             else "A playful cartoon picture-book illustration for small children: ")
    rader = [start + motiv + " " + FORMAT.format(sak=sak), "", "Style rules (important):"]
    stil = [s.format(mork=mork) for s in STIL]
    if verklig:
        stil[2] = stil[2].replace("A soft, rounded 3D toy look", "A soft 3D look")
    rader += ["- " + s for s in stil + [detalj] + extra + ["Background: " + bakgrund, SIST]]
    return "\n".join(rader)


doc = Document()
st = doc.styles['Normal']
st.font.name = 'Calibri'
st.font.size = Pt(11)
doc.add_heading('Bilder till målarboken Pensla', 0)
doc.add_paragraph(
    "Hej Copilot! Jag gör en målarboksapp för små barn. Skapa en bild för varje prompt "
    "i det här dokumentet. Följ varje prompt exakt, den är skriven på engelska med flit.")
doc.add_heading('Så här vill jag ha det', 1)
for t in [
    "En bild per prompt, i den ordning de står. Om du bara kan göra en bild åt gången: gör bild 1 och vänta tills jag skriver \"nästa\".",
    "Liggande format 4:3 (bredare än hög), till exempel 1600 × 1200 pixlar.",
    "Alla bilder ska ha samma stil: tecknad bilderbok, tjocka nästan svarta konturer runt varje form, ljusa mjuka färger med en mjuk 3D-känsla, inga mörka skuggor längs konturerna.",
    "Konturerna är viktigast: varje yta ska vara helt omsluten av en kontur, utan glapp. Bilden görs sedan om till en målarbok där barnet målar fram färgerna.",
    "Ingen text, inga bokstäver, inga loggor, ingen ram, ingen signatur, inga människor och inga djur i bilderna.",
    "Ge varje bild filnamnet som står vid rubriken, till exempel traktor.jpg.",
]:
    doc.add_paragraph(t, style='List Bullet')
for i, (rubrik, fil, motiv, sak, mork, detalj, extra, bakgrund) in enumerate(BILDER, 1):
    doc.add_heading(f'Bild {i}: {rubrik}  ({fil}.jpg)', 1)
    r = doc.add_paragraph().add_run(prompt(motiv, sak, mork, detalj, extra, bakgrund, fil == 'flygplan-stort3'))
    r.font.name = 'Consolas'
    r.font.size = Pt(9.5)
for s in doc.sections:
    s.left_margin = s.right_margin = Cm(2)
doc.save(UT + 'copilot-bilder.docx')
print(len(BILDER), 'bilder')
