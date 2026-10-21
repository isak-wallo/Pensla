"""Gör om en färgbild (tecknad bild med mörka konturer, t.ex. från Gemini)
till en bild i Pensla: konturerna som vektorer och färgbilden som penseln
trollar fram.

Användning:  python verktyg/fargbild.py forlagor/traktor.jpg [fler ...]

Skriver för varje förlaga (namnet = filnamnet utan ändelse):
  bilder/farg/NAMN.svg  konturerna (1200x900, mörkgrå linjer, en SVG-bana)
  bilder/farg/NAMN.jpg  färgbilden i 1200x900
Konturerna är de pixlar som är tydligt mörkare än sin omgivning (även de
ljusare linjerna runt moln och sol), så skuggor och glans inne i ytorna
inte blir linjer, och som är det mörkaste i sin närhet, så skuggor som
ligger an mot en linje inte gör den tjock. Förlagan beskärs mitt på till 4:3.
Kräver Pillow, numpy, scipy och potrace (pip install potracer).
"""
import os, sys
import numpy as np, potrace
from PIL import Image
from scipy import ndimage as nd

UT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bilder', 'farg')
MORKARE = 18        # så mycket mörkare än omgivningen (0–255) en linjepixel är
OMGIVNING = 21      # omgivningen = det ljusaste inom så här många px
NARA = 13           # linjen ska vara det mörkaste inom så här många px ...
DJUP_ANDEL = 0.5    # ... (högst så här stor del av sin mörkhet ljusare), så
                    # att skuggor intill en linje inte gör den tjock och svart
MIN_BIT = 200       # lösa linjebitar mindre än så (px i förlagan) tas bort
LINJEFARG = '#3a3a44'
# Små linjebitar som är glans eller skugga i färgbilden och inte ska bli
# konturer: punkter (x, y i 1200x900) per bild. Den lilla bit (under
# BORT_MAX px i förlagan) som ligger närmast punkten tas bort.
BORT_MAX = 4000
BORT = {
    'traktor': [(740, 320), (190, 395), (315, 530), (825, 600), (710, 715)],
    'traktor2': [(630, 495)],
    'sopbil': [(420, 430), (270, 400), (770, 270), (1160, 320)],
    'sopbil-snett': [(255, 365), (615, 720)],
    'flygplan2': [(280, 533), (1072, 300)],
    'helikopter': [(455, 335), (400, 395), (480, 325), (1070, 455)],
    'helikopter2': [(520, 585), (118, 735), (1088, 735), (862, 740)],
    'tag': [(863, 391), (898, 392), (147, 411), (187, 412), (138, 425), (54, 425)],
    'tag2': [(126, 456), (189, 460)],
    'bat': [(888, 496), (825, 527)],
    'flygplan-stort': [(163, 323), (921, 365)],
    'flygplan-stort2': [(822, 531)],
    'raket': [(649, 134), (672, 162), (388, 706), (776, 706)],
    'segelbat': [(518, 635), (522, 630)],
    'polisbil': [(418, 688), (732, 689)],
    'polisbil2': [(1118, 297), (400, 392), (637, 423), (962, 660)],
    'ambulans': [(158, 618), (442, 647)],
    'betongbil': [(735, 195), (863, 199), (947, 354), (409, 364), (485, 368), (386, 438), (1090, 497), (1114, 511), (456, 532), (1082, 553), (1129, 703), (1044, 708), (31, 725), (137, 739), (261, 826), (337, 839), (1170, 840), (1147, 853), (776, 860)],
    'kranbil': [(426, 279), (718, 605), (142, 663), (86, 676), (171, 701), (268, 727), (1054, 720), (586, 751), (379, 833), (695, 849), (995, 861), (622, 866)],
    'kranbil2': [(955, 403), (805, 675), (522, 859)],
    'buss': [(479, 368), (89, 529), (380, 560), (94, 630)],
    'buss2': [(790, 541), (420, 621), (709, 636), (440, 717), (882, 719)],
    'brandbil2': [(265, 363), (380, 371)],
    'dumper2': [(747, 246), (642, 325), (374, 727), (800, 736), (290, 738), (1070, 831), (1163, 835), (1136, 852), (965, 867), (1009, 871)],
}


def till_4_3(im):
    w, h = im.size
    if w * 3 > h * 4:
        b = round(h * 4 / 3)
        return im.crop(((w - b) // 2, 0, (w - b) // 2 + b, h))
    hh = round(w * 3 / 4)
    return im.crop((0, (h - hh) // 2, w, (h - hh) // 2 + hh))


def ta_bort(m, punkter):
    bit, n = nd.label(m)
    storlek = np.bincount(bit.ravel())
    k = m.shape[1] / 1200
    for x, y in punkter:
        x, y, r = round(x * k), round(y * k), round(15 * k)
        ruta = bit[max(y - r, 0):y + r, max(x - r, 0):x + r]
        yy, xx = np.nonzero((ruta > 0) & (storlek[ruta] < BORT_MAX))
        if not len(yy):
            print('  ingen liten bit vid', (x, y))
            continue
        nara = np.argmin((yy - r) ** 2 + (xx - r) ** 2)
        m[bit == ruta[yy[nara], xx[nara]]] = False
    return m


def linjer(im):
    L = np.asarray(im, dtype=float) @ [0.299, 0.587, 0.114]
    L = nd.median_filter(L, 5)
    morkare = nd.grey_closing(L, size=(OMGIVNING, OMGIVNING)) - L
    djup = L - nd.grey_erosion(L, size=(NARA, NARA))
    m = nd.binary_opening((morkare > MORKARE) & (djup < morkare * DJUP_ANDEL), np.ones((3, 3)))
    bit, n = nd.label(m)
    storlek = np.bincount(bit.ravel())
    storlek[0] = 0
    return storlek[bit] >= MIN_BIT


def svg(m):
    k = 1200 / m.shape[1]
    p = lambda q: f"{q.x * k:.1f} {q.y * k:.1f}"
    d = []
    for kurva in potrace.Bitmap(~m).trace(turdsize=4, alphamax=1.0, opticurve=True, opttolerance=0.4):
        d.append(f"M{p(kurva.start_point)}")
        for s in kurva.segments:
            if s.is_corner:
                d.append(f"L{p(s.c)}L{p(s.end_point)}")
            else:
                d.append(f"C{p(s.c1)} {p(s.c2)} {p(s.end_point)}")
        d.append("Z")
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900">'
            f'<path fill="{LINJEFARG}" fill-rule="evenodd" d="{"".join(d)}"/></svg>')


def main():
    os.makedirs(UT, exist_ok=True)
    for fil in sys.argv[1:]:
        namn = os.path.splitext(os.path.basename(fil))[0]
        im = till_4_3(Image.open(fil).convert('RGB'))
        m = ta_bort(linjer(im), BORT.get(namn, []))
        open(os.path.join(UT, namn + '.svg'), 'w').write(svg(m))
        im.resize((1200, 900), Image.LANCZOS).save(os.path.join(UT, namn + '.jpg'), quality=88)
        print(namn, im.size, '->', os.path.join(UT, namn) + '.svg/.jpg')


if __name__ == '__main__':
    main()
