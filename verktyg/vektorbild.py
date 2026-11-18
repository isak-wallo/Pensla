"""Vektorbilder: gör om en bild (bilder/farg/NAMN.svg + NAMN.jpg) till rena
vektorer i en kompakt JSON som både Pensla N (Android) och webben kan rita
skarpt i alla storlekar, och kontrollerar dem.

    python verktyg/vektorbild.py --gor NAMN ...         # gör NAMN.json
    python verktyg/vektorbild.py --kandidater NAMN ...  # gömställen att välja bland
    python verktyg/vektorbild.py --kontroll [NAMN ...]  # kontrollerar JSON-filerna

`--ut MAPP` byter mapp för JSON-filerna (förval: pensla-native/app/src/main/
assets/bilder bredvid repot, tills webben också använder formatet).
Förhandsbilder och kandidater hamnar i granskning/vektor/.

Formatet (NAMN.json, version 1). Alla mått i bildpixlar, bilden är `h` = 900
hög och `b` bred; banor är SVG-banor med bara M, L, C och Z (absoluta
koordinater), så webben kan ge dem direkt till Path2D och Android läser dem
med en liten tolk:

    { "format": 1, "nr": 4, "namn": "Sopbil snett", "fil": "sopbil-snett",
      "b": 1200, "h": 900,
      "ytor": [ { "d": "M.. Z", "f": "#rrggbb" },                   // platt färg
                { "d": "M.. Z", "f": ["#rrggbb", "#rrggbb"],        // eller toning
                  "g": [x0, y0, x1, y1] } ],                         // från (x0,y0) till (x1,y1)
      "linje": { "f": "#3a3a44", "d": "M.. Z" },                     // konturerna som fylld bana (evenodd)
      "figurer": { "keiws": { "x": 700, "y": 480, "s": 0.4 },        // mitt under fötterna, skala
                   "gron": {...}, "rod": {...} } }

Färgytorna fyller hela bilden utan luckor: varje yta går in till mitten av
linjerna runt den, och linjerna (jämn bredd LINJE_BREDD) ritas ovanpå.
Ytorna ritas med evenodd. Figurerna står helt fritt i en yta (inget streck
över dem, inte ens när de vinkar eller studsar) och ritas utan mask, bara
klippta under fötterna när de poppar upp.

Så görs en bild (--gor):
 1. Konturerna ritas i dubbel storlek (Chrome), små hål fylls och allt
    tunnas till ett skelett (som TECKNING i fargbild.py).
 2. Glapp sluts: en fri ände kopplas till närmaste linje framför sig (inom
    GLAPP_MAX px), annars förlängs den rakt fram (inom FORLANG_MAX px), och
    går inte det tas strecket bort (glans- och skuggstreck).
 3. Ytor mindre än YTA_MIN px blir linje. Linjerna ritas om med jämn bredd
    och spåras med potrace (mjuka kurvor).
 4. Varje yta blir en polygon (till mitten av linjerna) med en färg ur
    färgbilden: en linjär toning om ytan har en tydlig ljusskiftning, annars
    platt (medianfärgen).
 5. Figurernas platser står i GOMSTALLEN nedan (väljs med --kandidater).

Kontrollen (--kontroll) ritar JSON-filen och säger till om något av detta
inte stämmer: inga fria ändar i linjerna (alla konturer slutna), inga
omålade luckor mellan ytorna, varje figur helt fri från streck (med
FRI_MARGINAL px luft) och inne i bilden, figurerna överlappar inte varandra,
och de syns mot sin bakgrund (KONTRAST_MIN).
"""
import argparse
import json
import os
import re
import sys

import cv2
import numpy as np
import potrace
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bildanalys as ba  # noqa: E402
from fargbild import tunna, utan_sporrar, LINJEFARG  # noqa: E402

KEIWS_MAPP = os.path.dirname(ba.ROT)
UT_FORVAL = os.path.join(KEIWS_MAPP, 'pensla-native', 'app', 'src', 'main', 'assets', 'bilder')
GRANSK = os.path.join(ba.ROT, 'granskning', 'vektor')

F = 2                  # arbetsskala (1800 px hög)
LINJE_BREDD = 5.0      # linjernas bredd (px vid 900 px höjd)
HAL_MAX = 40           # hål i linjerna mindre än så (px vid 900) fylls
SPORRE = 8             # kortare sporrar tas bort (px vid 900)
GLAPP_MAX = 22         # så långt en fri ände får kopplas till en annan linje
FORLANG_MAX = 40       # så långt en fri ände får förlängas rakt fram
YTA_MIN = 60           # mindre ytor blir linje (px vid 900)
TONING_MIN = 7.0       # toning först om ytans ljushet skiljer så mycket (Lab) mellan ändarna
FORENKLA = 0.7         # polygonförenkling för ytorna (px vid 900)
FRI_MARGINAL = 2       # luft mellan figur och streck (px)
KONTRAST_MIN = 25      # Lab-avstånd mellan figurens färg och ytan bakom

# Var keIWs och kompisarna står i varje vektorbild: (x, y, s), x och y =
# mitt under fötterna. Väljs bland kandidaterna (--kandidater) och skrivs
# här för hand; en egen plats går också bra.
GOMSTALLEN = {
    'sopbil-snett': {'keiws': (628, 301, 0.5), 'gron': (90, 700, 0.35), 'rod': (1010, 860, 0.4)},
    'flygplan-stort': {'keiws': (736, 250, 0.35), 'gron': (130, 840, 0.45), 'rod': (1090, 850, 0.4)},
    'raket': {'keiws': (150, 860, 0.45), 'gron': (862, 583, 0.3), 'rod': (1110, 860, 0.45)},
    'segelbat': {'keiws': (720, 500, 0.3), 'gron': (1100, 458, 0.3), 'rod': (968, 366, 0.3)},
    'tankbil3': {'keiws': (598, 322, 0.35), 'gron': (1246, 553, 0.3), 'rod': (150, 870, 0.4)},
    'skordetroska6': {'keiws': (64, 814, 0.5), 'gron': (1400, 850, 0.45), 'rod': (76, 445, 0.3)},
}


# ------------------------------------------------------------------ banor

def tal(v):
    s = '%.1f' % v
    return s[:-2] if s.endswith('.0') else s


def polygonbana(konturer):
    """[(N,2) punkter] -> 'M x y L x y ... Z' per kontur."""
    d = []
    for k in konturer:
        if len(k) < 3:
            continue
        d.append('M' + tal(k[0][0]) + ' ' + tal(k[0][1]))
        d.append('L' + ' '.join(tal(x) + ' ' + tal(y) for x, y in k[1:]))
        d.append('Z')
    return ''.join(d)


def potracebana(m, skala):
    d = []
    p = lambda q: tal(q.x * skala) + ' ' + tal(q.y * skala)
    for kurva in potrace.Bitmap(~m).trace(turdsize=2, alphamax=1.0, opticurve=True, opttolerance=0.3):
        d.append('M' + p(kurva.start_point))
        for s in kurva.segments:
            if s.is_corner:
                d.append('L' + p(s.c) + 'L' + p(s.end_point))
            else:
                d.append('C' + p(s.c1) + ' ' + p(s.c2) + ' ' + p(s.end_point))
        d.append('Z')
    return ''.join(d)


def las_bana(d, steg=8):
    """SVG-bana (M, L, C, Z, absoluta) -> lista av polygoner (N,2)."""
    ut, akt = [], []
    tok = re.findall(r'[MLCZ]|-?\d+(?:\.\d+)?', d)
    i, kmd, pos = 0, None, (0.0, 0.0)
    while i < len(tok):
        t = tok[i]
        if t in 'MLCZ':
            kmd = t
            i += 1
            if t == 'Z':
                if akt:
                    ut.append(np.array(akt))
                akt = []
            continue
        if kmd == 'M':
            if akt:
                ut.append(np.array(akt))
            pos = (float(tok[i]), float(tok[i + 1]))
            akt = [pos]
            i += 2
            kmd = 'L'
        elif kmd == 'L':
            pos = (float(tok[i]), float(tok[i + 1]))
            akt.append(pos)
            i += 2
        elif kmd == 'C':
            c1 = (float(tok[i]), float(tok[i + 1]))
            c2 = (float(tok[i + 2]), float(tok[i + 3]))
            e = (float(tok[i + 4]), float(tok[i + 5]))
            for k in range(1, steg + 1):
                t_ = k / steg
                a = (1 - t_) ** 3
                b = 3 * (1 - t_) ** 2 * t_
                c = 3 * (1 - t_) * t_ ** 2
                dd = t_ ** 3
                akt.append((a * pos[0] + b * c1[0] + c * c2[0] + dd * e[0],
                            a * pos[1] + b * c1[1] + c * c2[1] + dd * e[1]))
            pos = e
            i += 6
        else:
            i += 1
    if akt:
        ut.append(np.array(akt))
    return ut


def fyll_bana(d, shape, skala=1.0):
    """Ritar banan (evenodd) som en mask i storleken shape (skala = px per bildpixel)."""
    m = np.zeros(shape, np.uint8)
    polys = [np.round(p * skala * 16).astype(np.int32) for p in las_bana(d) if len(p) >= 3]
    # evenodd: varje delbana XOR:as in
    for p in polys:
        t = np.zeros(shape, np.uint8)
        cv2.fillPoly(t, [p], 1, lineType=cv2.LINE_8, shift=4)
        m ^= t
    return m.astype(bool)


# ------------------------------------------------------------------ linjerna

def skiva(r):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def gren_bakat(sk, start, maxlangd):
    """Följer skelettet från en fri ände tills en korsning. Returnerar
    (pixlar utan korsningen, nådde korsning)."""
    H, W = sk.shape
    vag = [start]
    sett = {start}
    y, x = start
    for _ in range(maxlangd):
        nb = [(y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
              if (dy or dx) and 0 <= y + dy < H and 0 <= x + dx < W and sk[y + dy, x + dx]
              and (y + dy, x + dx) not in sett]
        if len(nb) != 1:
            return vag, len(nb) > 1
        # korsning: grannen har fler än två grannar
        y, x = nb[0]
        n = sum(sk[yy, xx] for yy in range(max(0, y - 1), min(H, y + 2)) for xx in range(max(0, x - 1), min(W, x + 2))) - 1
        if n >= 3:
            return vag, True
        vag.append((y, x))
        sett.add((y, x))
    return vag, False


def beskar_andar(sk, starter):
    """Äter bort de fria ändarna i `starter` (och bara de) tills de når en korsning."""
    H, W = sk.shape
    sk = sk.copy()
    aktiva = set(starter)
    for _ in range(6000):
        ny = set()
        for y, x in aktiva:
            if not sk[y, x]:
                continue
            y0, y1, x0, x1 = max(0, y - 1), min(H, y + 2), max(0, x - 1), min(W, x + 2)
            del_ = sk[y0:y1, x0:x1]
            if del_.sum() - 1 > 3:
                continue
            if not _ar_ande(sk, y, x):
                continue
            sk[y, x] = False
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    if sk[yy, xx] and _ar_ande(sk, yy, xx):
                        ny.add((yy, xx))
        if not ny:
            break
        aktiva = ny
    return sk


def _ar_ande(sk, y, x):
    H, W = sk.shape
    ring = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    v = [bool(0 <= y + dy < H and 0 <= x + dx < W and sk[y + dy, x + dx]) for dy, dx in ring]
    B = sum(v)
    A = sum((not v[i]) and v[(i + 1) % 8] for i in range(8))
    return 1 <= B <= 3 and A == 1


def stang_glapp(sk, logg):
    """Kopplar ihop eller tar bort fria ändar tills inga finns kvar."""
    H, W = sk.shape
    for varv in range(8):
        andar = ba.andar(sk, kant=4 * F, radie=GLAPP_MAX * F, gren=30 * F)
        if not andar:
            return sk
        u8 = sk.astype(np.uint8)
        kopplade = forlangda = borttagna = 0
        bort = []
        for y, x, typ, _, mal in andar:
            if not u8[y, x]:
                continue
            if typ == 'glapp':
                cv2.line(u8, (x, y), (mal[1], mal[0]), 1, 1, cv2.LINE_8)
                kopplade += 1
                continue
            # förläng rakt fram tills den möter en linje eller bildkanten
            egen = ba.egen_gren(sk, (y, x), 12 * F)
            rk = ba.riktning(egen, (y, x))
            traff = None
            for k in range(2, FORLANG_MAX * F):
                yy, xx = int(round(y + rk[0] * k)), int(round(x + rk[1] * k))
                if not (0 <= yy < H and 0 <= xx < W):
                    traff = (min(H - 1, max(0, yy)), min(W - 1, max(0, xx)))
                    break
                if u8[yy, xx] and (yy, xx) not in egen:
                    traff = (yy, xx)
                    break
            if traff:
                cv2.line(u8, (x, y), (traff[1], traff[0]), 1, 1, cv2.LINE_8)
                forlangda += 1
            else:
                bort.append((y, x))
                borttagna += 1
        if bort:
            # Streck som slutar fritt tas bort: ändarna äts upp pixel för
            # pixel tills de når en korsning (eller bildkanten).
            u8 = beskar_andar(u8.astype(bool), bort).astype(np.uint8)
        sk = utan_sporrar(tunna(u8.astype(bool)), SPORRE * F)
        logg.append('varv %d: %d glapp kopplade, %d förlängda, %d streck borttagna' % (varv + 1, kopplade, forlangda, borttagna))
    return sk


def linjeskelett(alfa2, logg):
    linje = alfa2 >= 128
    # små hål i linjerna fylls (annars blir de små öglor i skelettet)
    lab, n = nd.label(~linje)
    storlek = np.bincount(lab.ravel())
    hal = (storlek < HAL_MAX * F * F)
    hal[0] = False
    linje |= hal[lab]
    sk = utan_sporrar(tunna(linje), SPORRE * F)
    sk = stang_glapp(sk, logg)
    sk = ba.stora_bitar(sk, 30 * F)
    # för små ytor blir linje, och sedan sluts det som ev. öppnats igen
    for _ in range(3):
        lab, n = nd.label(~sk)
        storlek = np.bincount(lab.ravel())
        liten = storlek < YTA_MIN * F * F
        liten[0] = False
        if not liten[1:].any():
            break
        logg.append('%d små ytor blir linje' % liten[1:].sum())
        sk = utan_sporrar(tunna(sk | liten[lab]), SPORRE * F)
        sk = stang_glapp(sk, logg)
    return sk


# ------------------------------------------------------------------ ytorna

def yta_farg(rgb, lab_bild, m, inre, ox, oy):
    """Färg för ytan m: platt hex eller (två hex, [x0,y0,x1,y1]) som toning."""
    ys, xs = np.nonzero(inre if inre.sum() > 30 else m)
    px = rgb[ys, xs].astype(float)
    L = lab_bild[ys, xs, 0]
    xs, ys = xs + ox, ys + oy
    if len(px) < 200:
        return '#%02x%02x%02x' % tuple(np.median(px, 0).astype(int))
    A = np.stack([np.ones_like(xs, float), xs, ys], 1)
    koef, *_ = np.linalg.lstsq(A, L, rcond=None)
    g = koef[1:]
    if np.hypot(*g) < 1e-6:
        return '#%02x%02x%02x' % tuple(np.median(px, 0).astype(int))
    rk = g / np.hypot(*g)
    t = xs * rk[0] + ys * rk[1]
    t0, t1 = np.percentile(t, 3), np.percentile(t, 97)
    if t1 - t0 < 4:
        return '#%02x%02x%02x' % tuple(np.median(px, 0).astype(int))
    tt = (t - t0) / (t1 - t0)
    B = np.stack([np.ones_like(tt), tt], 1)
    c, *_ = np.linalg.lstsq(B, px, rcond=None)
    c0, c1 = np.clip(c[0], 0, 255), np.clip(c[0] + c[1], 0, 255)
    if np.linalg.norm(ba.lab_farg(c0) - ba.lab_farg(c1)) < TONING_MIN:
        return '#%02x%02x%02x' % tuple(np.median(px, 0).astype(int))
    mx, my = xs.mean(), ys.mean()
    tm = mx * rk[0] + my * rk[1]
    p0 = (mx + rk[0] * (t0 - tm), my + rk[1] * (t0 - tm))
    p1 = (mx + rk[0] * (t1 - tm), my + rk[1] * (t1 - tm))
    hx = lambda c_: '#%02x%02x%02x' % tuple(np.round(c_).astype(int))
    return [hx(c0), hx(c1)], [round(v / F, 1) for v in (p0[0], p0[1], p1[0], p1[1])]


def ytor(sk, rgb2):
    """Färgytorna: en polygon per yta, in till mitten av linjerna."""
    lab, n = nd.label(~sk)
    lab_bild = ba.lab_farg(rgb2)
    tjock = cv2.dilate(sk.astype(np.uint8), skiva(int(LINJE_BREDD * F / 2) + 2)).astype(bool)
    objs = nd.find_objects(lab)
    ut = []
    for i, sl in enumerate(objs, 1):
        if sl is None:
            continue
        y0, y1 = max(0, sl[0].start - 2), min(lab.shape[0], sl[0].stop + 2)
        x0, x1 = max(0, sl[1].start - 2), min(lab.shape[1], sl[1].stop + 2)
        m = lab[y0:y1, x0:x1] == i
        # in till mitten av linjen: växer över skelettet
        stor = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8))
        konturer, _ = cv2.findContours(stor, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        polys = []
        for k in konturer:
            k = cv2.approxPolyDP(k, FORENKLA * F, True)[:, 0, :].astype(float)
            if len(k) < 3:
                continue
            polys.append((k + [x0, y0]) / F)
        if not polys:
            continue
        inre = m & ~tjock[y0:y1, x0:x1]
        farg = yta_farg(rgb2[y0:y1, x0:x1], lab_bild[y0:y1, x0:x1], m, inre, x0, y0)
        post = {'d': polygonbana(polys)}
        if isinstance(farg, str):
            post['f'] = farg
        else:
            post['f'], post['g'] = farg
        ut.append((m.sum(), post))
    ut.sort(key=lambda t: -t[0])
    return [p for _, p in ut]


# ------------------------------------------------------------------ rendering (förhandsbild/kontroll)

def rita(data, skala=1.0, med_linje=True, med_figurer=True):
    W, H = round(data['b'] * skala), round(data['h'] * skala)
    im = np.full((H, W, 3), 255, float)
    yy, xx = np.mgrid[0:H, 0:W]
    tackt = np.zeros((H, W), bool)
    for y in data['ytor']:
        m = fyll_bana(y['d'], (H, W), skala)
        tackt |= m
        if isinstance(y['f'], str):
            im[m] = ba.hexrgb(y['f'])
        else:
            x0, y0, x1, y1 = [v * skala for v in y['g']]
            dx, dy = x1 - x0, y1 - y0
            t = (((xx[m] + 0.5 - x0) * dx + (yy[m] + 0.5 - y0) * dy) / max(1e-6, dx * dx + dy * dy)).clip(0, 1)
            c0, c1 = np.array(ba.hexrgb(y['f'][0]), float), np.array(ba.hexrgb(y['f'][1]), float)
            im[m] = c0 + (c1 - c0) * t[:, None]
    if med_figurer:
        for namn, c in data.get('figurer', {}).items():
            for x0, y0, x1, y1, f in ba.rektanglar({'x': c['x'] * skala, 'y': c['y'] * skala, 's': c['s'] * skala}, ba.STILLA):
                im[max(0, y0):y1, max(0, x0):x1] = ba.hexrgb(ba.FARGER[namn].get(f, ba.FARGER[namn]['bla']))
    linje = fyll_bana(data['linje']['d'], (H, W), skala)
    if med_linje:
        im[linje] = ba.hexrgb(data['linje']['f'])
    return im.astype(np.uint8), linje, tackt


# ------------------------------------------------------------------ figurerna

def ram(c):
    """Rektanglarna figuren täcker (alla lägen) i bildkoordinater."""
    rekt = []
    for r in [ba.STILLA] + ba.VINKA:
        rekt += [(x0, y0, x1, y1) for x0, y0, x1, y1, _ in ba.rektanglar(c, r)]
    rekt += [(x0, y0, x1, y1) for x0, y0, x1, y1, _ in ba.rektanglar(c, ba.STILLA, ba.STUDS)]
    return rekt


def kolla_figurer(data, linje, skala=1.0):
    """Fel och varningar för figurerna i data (linje = linjemask i skala)."""
    fel, varn = [], []
    H, W = linje.shape
    blockerat = cv2.dilate(linje.astype(np.uint8), skiva(max(1, round(FRI_MARGINAL * skala)))).astype(bool)
    rgb, _, _ = rita(data, skala, med_linje=False, med_figurer=False)
    masker = {}
    for namn, c in data.get('figurer', {}).items():
        cc = {'x': c['x'] * skala, 'y': c['y'] * skala, 's': c['s'] * skala}
        m = np.zeros((H, W), bool)
        ute = False
        for x0, y0, x1, y1 in ram(cc):
            if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
                ute = True
            m[max(0, y0):max(0, min(H, y1)), max(0, x0):max(0, min(W, x1))] = True
        if ute:
            fel.append('%s: delvis utanför bilden' % namn)
        n = (m & blockerat).sum()
        if n:
            fel.append('%s: %d px på eller intill ett streck' % (namn, n))
        masker[namn] = m
        kropp = ba.figurmask(cc, (H, W), [[0, 0, 160, 160, 'bla']])
        omkring = cv2.dilate(kropp.astype(np.uint8), skiva(max(2, round(8 * skala)))).astype(bool) & ~kropp & ~linje
        if omkring.any():
            bak = ba.lab_farg(rgb[omkring].mean(0))
            k = np.linalg.norm(bak - ba.lab_farg(ba.hexrgb(ba.FARGER[namn]['bla'])))
            if k < KONTRAST_MIN:
                varn.append('%s: syns dåligt mot bakgrunden (Lab %.0f)' % (namn, k))
    namn_ = list(masker)
    for i in range(len(namn_)):
        for j in range(i + 1, len(namn_)):
            # bara stilla-lägena får inte överlappa (vinkningen sker sällan samtidigt)
            a = ba.figurmask(skalad(data['figurer'][namn_[i]], skala), (H, W))
            b = ba.figurmask(skalad(data['figurer'][namn_[j]], skala), (H, W))
            if (a & b).any():
                fel.append('%s och %s överlappar' % (namn_[i], namn_[j]))
    return fel, varn


def skalad(c, skala):
    return {'x': c['x'] * skala, 'y': c['y'] * skala, 's': c['s'] * skala}


def kandidater(data, antal=20):
    """Platser där en figur står helt fritt och på något (en linje under fötterna)."""
    rgb, linje, _ = rita(data, 1.0, med_linje=True, med_figurer=False)
    H, W = linje.shape
    blockerat = cv2.dilate(linje.astype(np.uint8), skiva(FRI_MARGINAL + 1)).astype(np.int32)
    ii = np.pad(blockerat, ((1, 0), (1, 0))).cumsum(0).cumsum(1)

    def summa(x0, y0, x1, y1):
        if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
            return 1
        return ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]
    hitta = []
    for s in (0.3, 0.35, 0.4, 0.45, 0.5):
        steg = 6
        fh = max(4, round(10 * s))
        for y in range(40, H - 2, steg // 2):
            for x in range(40, W - 40, steg):
                c = {'x': x, 'y': y, 's': s}
                if any(summa(*r) for r in ram(c)):
                    continue
                # något under fötterna: en linje strax under hela fotbredden
                fx0, fx1 = round(x + (22 - 80) * s), round(x + (138 - 80) * s)
                under = linje[y + 1:min(H, y + 1 + fh), fx0:fx1].any(0)
                if under.mean() < 0.85:
                    continue
                kropp = rgb[round(y - 204 * s):round(y - 44 * s), round(x - 80 * s):round(x + 80 * s)].reshape(-1, 3).mean(0)
                kontrast = {k: float(np.linalg.norm(ba.lab_farg(kropp) - ba.lab_farg(ba.hexrgb(v['bla'])))) for k, v in ba.FARGER.items()}
                hitta.append((s, x, y, kontrast))
    # största skalan först, spridda
    valda = []
    for s, x, y, k in sorted(hitta, key=lambda h: (-h[0], h[2])):
        if any(abs(x - v['x']) < 90 and abs(y - v['y']) < 90 for v in valda):
            continue
        valda.append({'x': x, 'y': y, 's': s, 'kontrast': {kk: round(vv) for kk, vv in k.items()}})
        if len(valda) >= antal:
            break
    return valda, rgb


# ------------------------------------------------------------------ huvudprogram

def gor(fil, ut, bild):
    logg = []
    with ba.Ritare() as r:
        alfa2, rgb2 = ba.las_bild(r, fil, ba.PAPER_H * F)
    sk = linjeskelett(alfa2, logg)
    tjock = cv2.dilate(sk.astype(np.uint8), skiva(round(LINJE_BREDD * F / 2)))
    data = {
        'format': 1, 'nr': bild['nr'], 'namn': bild['namn'], 'fil': fil,
        'b': rgb2.shape[1] // F, 'h': ba.PAPER_H,
        'ytor': ytor(sk, rgb2),
        'linje': {'f': LINJEFARG, 'd': potracebana(tjock.astype(bool), 1 / F)},
        'figurer': {k: {'x': v[0], 'y': v[1], 's': v[2]} for k, v in GOMSTALLEN.get(fil, {}).items()},
    }
    os.makedirs(ut, exist_ok=True)
    p = os.path.join(ut, fil + '.json')
    json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(fil, '\n  ' + '\n  '.join(logg), '\n  %d ytor, %d kB' % (len(data['ytor']), os.path.getsize(p) // 1024))
    return data


def satt_figurer(fil, ut):
    p = os.path.join(ut, fil + '.json')
    data = json.load(open(p, encoding='utf-8'))
    data['figurer'] = {k: {'x': v[0], 'y': v[1], 's': v[2]} for k, v in GOMSTALLEN.get(fil, {}).items()}
    json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return data


def kontroll(data):
    """Returnerar (fel, varningar)."""
    fel, varn = [], []
    im, linje, tackt = rita(data, F, med_figurer=False)
    H, W = linje.shape
    # 1. alla konturer slutna: skelettet av linjerna har inga fria ändar
    sk = utan_sporrar(tunna(linje), 3 * F)
    sk = ba.stora_bitar(sk, 20 * F)
    e = ba.andpunkter(sk)
    e[:10 * F] = e[-10 * F:] = False
    e[:, :10 * F] = e[:, -10 * F:] = False
    ys, xs = np.nonzero(e)
    if len(ys):
        fel.append('%d fria ändar i linjerna, t.ex. vid %s' % (len(ys), ', '.join('(%d, %d)' % (x // F, y // F) for y, x in list(zip(ys, xs))[:5])))
    # 2. inga luckor: allt utanför linjerna täcks av en färgyta
    lucka = ~tackt & ~linje
    lucka = nd.binary_opening(lucka, np.ones((2, 2)))
    if lucka.sum():
        fel.append('%d px utan färg mellan ytorna' % lucka.sum())
    # 3. figurerna
    f2, v2 = kolla_figurer(data, linje, F)
    fel += f2
    varn += v2
    if not data.get('figurer'):
        varn.append('inga figurer')
    return fel, varn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gor', action='store_true')
    ap.add_argument('--figurer', action='store_true', help='skriv bara om figurerna från GOMSTALLEN')
    ap.add_argument('--kandidater', action='store_true')
    ap.add_argument('--kontroll', action='store_true')
    ap.add_argument('--ut', default=UT_FORVAL)
    ap.add_argument('namn', nargs='*')
    a = ap.parse_args()
    os.makedirs(GRANSK, exist_ok=True)
    alla = {b['fil']: b for b in ba.bilder()[0]}
    namn = a.namn or sorted(f[:-5] for f in os.listdir(a.ut) if f.endswith('.json'))
    fel_totalt = 0
    for fil in namn:
        if a.gor:
            data = gor(fil, a.ut, alla[fil])
        elif a.figurer:
            data = satt_figurer(fil, a.ut)
        else:
            data = json.load(open(os.path.join(a.ut, fil + '.json'), encoding='utf-8'))
        if a.kandidater:
            k, rgb = kandidater(data)
            im = Image.fromarray((rgb * 0.75 + 255 * 0.25).astype(np.uint8))
            d = ImageDraw.Draw(im)
            font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 22)
            for i, c in enumerate(k, 1):
                for x0, y0, x1, y1, f in ba.rektanglar(c, ba.STILLA):
                    d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=ba.FARGER['keiws'].get(f, '#5685d7'))
                tx, ty = round(c['x'] + 90 * c['s']), round(c['y'] - 230 * c['s'])
                d.rectangle([tx - 2, ty, tx + 14 * len(str(i)) + 3, ty + 26], fill='white', outline='black')
                d.text((tx, ty - 1), str(i), fill='black', font=font)
            im.save(os.path.join(GRANSK, 'kand-' + fil + '.png'))
            json.dump(k, open(os.path.join(GRANSK, 'kand-' + fil + '.json'), 'w'), indent=0)
            print(fil, len(k), 'kandidater:', ' '.join('%d=(%d,%d,%s)' % (i, c['x'], c['y'], c['s']) for i, c in enumerate(k, 1)))
            continue
        im, _, _ = rita(data, 1.0)
        Image.fromarray(im).save(os.path.join(GRANSK, fil + '.png'))
        if a.kontroll or a.gor or a.figurer:
            fel, varn = kontroll(data)
            fel_totalt += len(fel)
            print(fil, 'OK' if not fel else 'FEL', *(['\n  FEL: ' + f for f in fel] + ['\n  obs: ' + v for v in varn]))
    if fel_totalt:
        sys.exit(1)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
