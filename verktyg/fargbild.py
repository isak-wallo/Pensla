"""Gör om en färgbild (tecknad bild med mörka konturer, t.ex. från Gemini)
till en bild i Pensla: konturerna som vektorer och färgbilden som penseln
trollar fram.

Användning:  python verktyg/fargbild.py forlagor/traktor.jpg [fler ...]

Skriver för varje förlaga (namnet = filnamnet utan ändelse):
  bilder/farg/NAMN.svg  konturerna (900 px höga, mörkgrå linjer, en SVG-bana)
  bilder/farg/NAMN.jpg  färgbilden i samma storlek
Konturerna är de pixlar som är tydligt mörkare än sin omgivning (även de
ljusare linjerna runt moln och sol), så skuggor och glans inne i ytorna
inte blir linjer, och som är det mörkaste i sin närhet, så skuggor som
ligger an mot en linje inte gör den tjock. Bilden blir 900 px hög och
behåller sitt format (t.ex. 16:10 -> 1440x900); nästan 4:3 (Geminis
2400x1792) och bilderna i BESKAR_4_3 beskärs mitt på till 4:3 = 1200x900.
Kräver Pillow, numpy, scipy, potrace och OpenCV
(pip install potracer opencv-python-headless).
"""
import os, sys, heapq
import numpy as np, potrace
from PIL import Image
from scipy import ndimage as nd
import cv2

UT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bilder', 'farg')
MORKARE = 18        # så mycket mörkare än omgivningen (0–255) en linjepixel är
OMGIVNING = 21      # omgivningen = det ljusaste inom så här många px
NARA = 13           # linjen ska vara det mörkaste inom så här många px ...
DJUP_ANDEL = 0.5    # ... (högst så här stor del av sin mörkhet ljusare), så
                    # att skuggor intill en linje inte gör den tjock och svart
MIN_BIT = 200       # lösa linjebitar mindre än så (px i förlagan) tas bort
LINJEFARG = '#3a3a44'
# Små linjebitar som är glans eller skugga i färgbilden och inte ska bli
# konturer: punkter (x, y i bilden, 900 px hög) per bild. Den lilla bit (under
# BORT_MAX px i förlagan) som ligger närmast punkten tas bort.
BORT_MAX = 4000
# Bilder där konturerna också tas från färgkanterna (Canny i Lab-färg), för
# former som saknar mörk kontur. Förlagan skalas först upp till 1800 px
# höjd så att linjerna blir lika tjocka som i Gemini-bilderna. (Copilot-
# bilderna låg här t.o.m. v69, se FARGOMRADEN.)
# Värdet = minsta bitstorlek (px i den uppskalade förlagan), i stället för MIN_BIT.
FARGKANTER = {
    'bat': 600,  # skrovets underkant mot vattnet har ingen mörk kontur
    'traktor8': 600, 'traktor9': 600, 'traktor10': 600,  # Gemini/ChatGPT-test 2026-10-21
    'betongbil4': 600, 'betongbil5': 600, 'ambulans4': 600, 'ambulans5': 600,  # mellanstil 2026-10-21
}
KANT_LAG, KANT_HOG = 20, 50   # Canny-trösklarna
# Copilot-bilderna (nr 48–74) spåras sedan v70 med färgområden i stället
# (`omradeslinjer`): mörka linjer med hysteres (frön mörkare än MORK_HOG
# växer in i det som är mörkare än MORK_LAG, så linjerna blir hela i
# stället för hackiga) plus gränserna mellan färgområden. Områdena tas
# fram genom mean shift + k-means och slås sedan ihop med grannar vars
# färg skiljer mindre än OMRADE_SKILLNAD (Lab), så att skuggningar inte
# blir linjer men ränder, kors, moln och sol blir det.
FARGOMRADEN = {
    'gravare5', 'traktor5', 'flygplan6', 'sopbil5', 'flygplan-stort5', 'kranbil3', 'traktor6',
    'betongbil3', 'brandbil3', 'ambulans3', 'polisbil4', 'brandbil4', 'raddningsbat', 'sopbil6',
    'helikopter3', 'dumper3', 'skordetroska', 'dumper4', 'plogbil', 'bargningsbil', 'postbil',
    'traktor7', 'lastfartyg', 'sopbil7', 'buss3', 'brandbil5', 'polisbil5',
}
MORK_HOG, MORK_LAG = 40, 14
OMRADE_SKILLNAD = 22   # färgskillnad (Lab) som håller isär två områden
OMRADE_MIN = 150       # mindre områden (px vid 900 px höjd) går alltid ihop med närmaste granne
# TECKNING (v71, `teckning`) är nästa steg för Copilot-bilderna: linjer är
# det som är mörkare än båda sidor (dalar, så att kanten på en röd yta inte
# blir en linje), färgområdena räknas på en bild där linjerna målats bort
# (så att gränserna hamnar mitt i linjerna), och allt tunnas till ett
# skelett som ritas om med jämn bredd (LINJE_BREDD px vid 1800 px höjd).
TECKNING = set(FARGOMRADEN)   # alla Copilot-bilder sedan v73
DAL_HOG, DAL_LAG = 30, 12
LINJE_BREDD = 7
BRED_DAL, BRED_MORK = 16, 90
LINJE_MIN = 800          # mindre mörka bitar är skuggfläckar (px vid 1800 px höjd)
TECKNING_SKILLNAD = 28
HAL_MAX = 400  # mindre hål i linjerna fylls innan de tunnas (px vid 1800 px höjd)
SPORRE = 30   # kortare grenar som slutar fritt tas bort (px vid 1800 px höjd)
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
    'flygplan-stort3': [(1020, 556), (1023, 555), (89, 703)],
    'flygplan-stort4': [(1077, 150), (1033, 171), (973, 390), (281, 380), (1064, 386), (1028, 425), (311, 424), (318, 501), (358, 532), (423, 544), (490, 552), (706, 583), (764, 593), (816, 602), (887, 619), (94, 751)],
    'flygplan4': [(228, 465)],
    'gravare4': [(355, 299), (434, 311), (520, 347), (758, 395), (454, 421), (1120, 407), (767, 473), (757, 523), (493, 586), (507, 597), (723, 615), (1016, 628), (528, 631), (726, 656), (533, 676), (942, 698), (511, 716)],
    'traktor3': [(559, 163)],
    'raket2': [(693, 116), (513, 452), (488, 480), (827, 534), (838, 575)],
    'raket3': [(659, 170)],
}


# Bilder i 3:2 som spårades innan andra format än 4:3 tilläts (v69). De
# beskärs som förut, så att keIWs-måtten i bilder.js stämmer.
BESKAR_4_3 = {
    'ambulans3', 'bargningsbil', 'betongbil3', 'brandbil3', 'brandbil4',
    'brandbil5', 'buss3', 'dumper3', 'dumper4', 'flygplan-stort5',
    'flygplan6', 'gravare4', 'gravare5', 'helikopter3', 'kranbil3',
    'lastfartyg', 'plogbil', 'polisbil4', 'polisbil5', 'postbil',
    'raddningsbat', 'skordetroska', 'sopbil5', 'sopbil6', 'sopbil7',
    'traktor5', 'traktor6', 'traktor7',
}
HOJD = 900


def till_format(im, namn):
    w, h = im.size
    if namn in BESKAR_4_3 or 1.30 <= w / h <= 1.37:
        return till_4_3(im)
    return im


def storlek(im):
    """Bildens storlek i appen: 900 px hög, bredden efter formatet."""
    return round(HOJD * im.width / im.height), HOJD


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
    k = m.shape[0] / HOJD
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


def omraden(im, skillnad=OMRADE_SKILLNAD):
    """Gränserna mellan färgområdena i im (som är 900 px hög)."""
    a = np.asarray(im)
    lab = cv2.cvtColor(cv2.pyrMeanShiftFiltering(a, 10, 16, maxLevel=1), cv2.COLOR_RGB2LAB).astype(np.float32)
    lab[..., 0] *= 100 / 255
    lab[..., 1:] -= 128
    krit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    cv2.setRNGSeed(1)
    _, q, _ = cv2.kmeans(lab.reshape(-1, 3), 32, None, krit, 1, cv2.KMEANS_PP_CENTERS)
    q = q.reshape(a.shape[:2])
    # Sammanhängande bitar av varje färg är startområdena
    bit = np.zeros(q.shape, np.int32)
    n = 0
    for k in range(32):
        b, m = nd.label(q == k)
        bit[b > 0] = b[b > 0] + n
        n += m
    n += 1
    antal = np.bincount(bit.ravel(), minlength=n).astype(float)
    medel = list(np.stack([np.bincount(bit.ravel(), lab[..., i].ravel(), minlength=n)
                           for i in range(3)], 1) / np.maximum(antal, 1)[:, None])
    antal = list(antal)
    pa = np.concatenate([bit[:, 1:].ravel(), bit[1:, :].ravel()])
    pb = np.concatenate([bit[:, :-1].ravel(), bit[:-1, :].ravel()])
    olika = pa != pb
    par = np.unique(np.stack([np.minimum(pa[olika], pb[olika]), np.maximum(pa[olika], pb[olika])], 1), axis=0)
    grannar = [set() for _ in range(n)]
    for x, y in par:
        grannar[x].add(y)
        grannar[y].add(x)
    # Slå ihop de mest lika grannarna först, med uppdaterat medelvärde
    far = list(range(n))
    avst = lambda x, y: float(np.linalg.norm(medel[x] - medel[y]))
    ko = [(avst(x, y), int(x), int(y)) for x, y in par]
    heapq.heapify(ko)
    while ko:
        d0, x, y = heapq.heappop(ko)
        if far[x] != x or far[y] != y or y not in grannar[x]:
            continue
        d = avst(x, y)
        if d > d0 + 1e-6:
            heapq.heappush(ko, (d, x, y))
            continue
        if d >= skillnad and min(antal[x], antal[y]) >= OMRADE_MIN:
            continue
        if antal[x] < antal[y]:
            x, y = y, x
        medel[x] = (medel[x] * antal[x] + medel[y] * antal[y]) / (antal[x] + antal[y])
        antal[x] += antal[y]
        far[y] = x
        for z in grannar[y]:
            if z != x:
                grannar[z].discard(y)
                grannar[z].add(x)
                grannar[x].add(z)
                heapq.heappush(ko, (avst(x, z), min(x, z), max(x, z)))
        grannar[x].discard(y)
        grannar[y] = set()
    def rot(x):
        while far[x] != x:
            x = far[x]
        return x
    R = np.array([rot(x) for x in range(n)])[bit]
    kant = np.zeros(R.shape, bool)
    kant[:, 1:] |= R[:, 1:] != R[:, :-1]
    kant[1:, :] |= R[1:, :] != R[:-1, :]
    return kant


def omradeslinjer(im):
    """Mörka linjer (hysteres) plus gränser mellan färgområden, för
    FARGOMRADEN-bilderna. im är 1800 px hög."""
    L = nd.median_filter(np.asarray(im, dtype=float) @ [0.299, 0.587, 0.114], 5)
    morkare = nd.grey_closing(L, size=(OMGIVNING, OMGIVNING)) - L
    fron = nd.binary_opening(morkare > MORK_HOG, np.ones((3, 3)))
    mork = nd.binary_propagation(fron, mask=morkare > MORK_LAG)
    liten = im.resize((round(HOJD * im.width / im.height), HOJD), Image.LANCZOS)
    kant = np.asarray(Image.fromarray(omraden(liten)).resize(im.size, Image.NEAREST))
    # Gränserna intill en mörk linje behövs inte, de gör den bara tjock.
    kant = nd.binary_dilation(kant, np.ones((5, 5))) & ~nd.binary_dilation(mork, np.ones((11, 11)))
    bit, n = nd.label(kant)
    storlek = np.bincount(bit.ravel())
    storlek[0] = 0
    kant = storlek[bit] >= 600
    bit, n = nd.label(mork | kant)
    storlek = np.bincount(bit.ravel())
    storlek[0] = 0
    return storlek[bit] >= 800


def dalar(L, radier=(4, 7, 11, 16)):
    """Hur mycket mörkare varje pixel är än båda sidor, i den riktning
    och på det avstånd där skillnaden är störst. De bredaste (BRED_DAL)
    räknas bara där det är riktigt mörkt (L < BRED_MORK), så att tjocka
    fönsterramar blir en linje men inte röda kors och ränder."""
    bast = np.zeros_like(L)
    for r in radier:
        if r >= BRED_DAL:
            bred = np.zeros_like(L)
            for dx, dy in ((r, 0), (0, r), (r, r), (r, -r)):
                a = nd.shift(L, (dy, dx), order=0, mode='nearest')
                b = nd.shift(L, (-dy, -dx), order=0, mode='nearest')
                bred = np.maximum(bred, np.minimum(a, b) - L)
            bast = np.maximum(bast, np.where(L < BRED_MORK, bred, 0))
            continue
        for dx, dy in ((r, 0), (0, r), (r, r), (r, -r)):
            a = nd.shift(L, (dy, dx), order=0, mode='nearest')
            b = nd.shift(L, (-dy, -dx), order=0, mode='nearest')
            bast = np.maximum(bast, np.minimum(a, b) - L)
    return bast


def tunna(m):
    """Skelettet av m (Zhang-Suen), en pixel brett."""
    m = np.pad(m.astype(np.uint8), 1)
    grannar = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))
    andrat = True
    while andrat:
        andrat = False
        for steg in (0, 1):
            P = [np.roll(np.roll(m, -dy, 0), -dx, 1) for dy, dx in grannar]
            B = sum(P)
            A = sum((P[i] == 0) & (P[(i + 1) % 8] == 1) for i in range(8))
            if steg == 0:
                c = (P[0] * P[2] * P[4] == 0) & (P[2] * P[4] * P[6] == 0)
            else:
                c = (P[0] * P[2] * P[6] == 0) & (P[0] * P[4] * P[6] == 0)
            d = (m == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if d.any():
                m[d] = 0
                andrat = True
    return m[1:-1, 1:-1].astype(bool)


def utan_sporrar(sk, langd):
    """Tar bort korta grenar (sporrar) som sticker ut från en korsning i
    skelettet sk och slutar fritt."""
    k = np.ones((3, 3))
    grannar = nd.convolve(sk.astype(int), k, mode='constant') - sk
    korsning = nd.binary_dilation(sk & (grannar >= 3), k) & sk
    del_ = sk & ~korsning
    bit, n = nd.label(del_, k)
    if not n:
        return sk
    langder = np.bincount(bit.ravel(), minlength=n + 1)
    fri = np.zeros(n + 1, bool)
    fri[np.unique(bit[del_ & (grannar == 1)])] = True
    vid = np.zeros(n + 1, bool)
    vid[np.unique(bit[nd.binary_dilation(korsning, k) & del_])] = True
    bort = fri & vid & (langder < langd)
    bort[0] = False
    return sk & ~bort[bit]


def stora_bitar(m, minst):
    bit, n = nd.label(m, np.ones((3, 3)))
    storlek = np.bincount(bit.ravel())
    storlek[0] = 0
    return storlek[bit] >= minst


def teckning(im):
    """Linjeteckning med jämn linjebredd, för TECKNING-bilderna. im är
    1800 px hög."""
    L = nd.median_filter(np.asarray(im, dtype=float) @ [0.299, 0.587, 0.114], 3)
    d = dalar(L)
    fron = nd.binary_opening(d > DAL_HOG, np.ones((3, 3)))
    linje = stora_bitar(nd.binary_propagation(fron, mask=d > DAL_LAG), LINJE_MIN)
    ren = cv2.inpaint(np.asarray(im), nd.binary_dilation(linje, np.ones((5, 5))).astype(np.uint8),
                      5, cv2.INPAINT_TELEA)
    liten = cv2.resize(ren, (round(HOJD * im.width / im.height), HOJD), interpolation=cv2.INTER_AREA)
    kant = cv2.resize(omraden(liten, TECKNING_SKILLNAD).astype(np.uint8), im.size, interpolation=cv2.INTER_NEAREST) > 0
    alla = linje | nd.binary_dilation(kant, np.ones((3, 3)))
    alla = nd.binary_closing(alla, np.ones((5, 5)))
    # Små hål (mellan två linjer som nästan rör vid varandra) fylls, annars
    # blir skelettet en stege av små öglor.
    hal, n = nd.label(~alla)
    storlek = np.bincount(hal.ravel())
    storlek[0] = 0
    alla |= (storlek[hal] < HAL_MAX) & (hal > 0)
    skelett = tunna(alla)
    skelett = stora_bitar(utan_sporrar(utan_sporrar(skelett, SPORRE), SPORRE), 40)
    rund = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (LINJE_BREDD, LINJE_BREDD))
    tjock = cv2.dilate(skelett.astype(np.uint8), rund).astype(float)
    return nd.gaussian_filter(tjock, 1.5) > 0.45


def fargkanter(im, min_bit):
    """Mörka linjer (utan skuggspärren) plus färgkanter, för FARGKANTER-bilder."""
    L = nd.median_filter(np.asarray(im, dtype=float) @ [0.299, 0.587, 0.114], 5)
    mork = nd.binary_opening(nd.grey_closing(L, size=(OMGIVNING, OMGIVNING)) - L > MORKARE, np.ones((3, 3)))
    lab = cv2.cvtColor(cv2.bilateralFilter(np.asarray(im), 9, 40, 9), cv2.COLOR_RGB2LAB)
    kant = np.zeros(mork.shape, bool)
    for c in range(3):
        kant |= cv2.Canny(lab[:, :, c], KANT_LAG, KANT_HOG, L2gradient=True) > 0
    # Kanterna på var sida om en mörk linje behövs inte, de gör den bara tjock.
    kant = nd.binary_dilation(kant, np.ones((5, 5))) & ~nd.binary_dilation(mork, np.ones((9, 9)))
    bit, n = nd.label(mork | kant)
    storlek = np.bincount(bit.ravel())
    storlek[0] = 0
    return storlek[bit] >= min_bit


def svg(m):
    k = HOJD / m.shape[0]
    b = round(m.shape[1] * k)
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
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{b}" height="{HOJD}" viewBox="0 0 {b} {HOJD}">'
            f'<path fill="{LINJEFARG}" fill-rule="evenodd" d="{"".join(d)}"/></svg>')


def main():
    os.makedirs(UT, exist_ok=True)
    for fil in sys.argv[1:]:
        namn = os.path.splitext(os.path.basename(fil))[0]
        im = till_format(Image.open(fil).convert('RGB'), namn)
        if namn in TECKNING:
            stor = im.resize((round(1800 * im.width / im.height), 1800), Image.LANCZOS)
            m = ta_bort(teckning(stor), BORT.get(namn, []))
        elif namn in FARGOMRADEN:
            stor = im.resize((round(1800 * im.width / im.height), 1800), Image.LANCZOS)
            m = ta_bort(omradeslinjer(stor), BORT.get(namn, []))
        elif namn in FARGKANTER:
            stor = im.resize((round(1800 * im.width / im.height), 1800), Image.LANCZOS) if im.height < 1800 else im
            m = ta_bort(fargkanter(stor, FARGKANTER[namn]), BORT.get(namn, []))
        else:
            m = ta_bort(linjer(im), BORT.get(namn, []))
        open(os.path.join(UT, namn + '.svg'), 'w').write(svg(m))
        im.resize(storlek(im), Image.LANCZOS).save(os.path.join(UT, namn + '.jpg'), quality=88)
        print(namn, im.size, '->', os.path.join(UT, namn) + '.svg/.jpg')


if __name__ == '__main__':
    main()
