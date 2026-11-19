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
      "beskar": [x0, x1],                                            // bara om färgbilden beskurits (BESKAR)
      "figurer": { "keiws": { "x": 700, "y": 480, "s": 0.4,          // mitt under fötterna, skala
                              "klipp": "M.. Z" },                    // ytan han syns i
                   "gron": {...}, "rod": {...} } }

Färgytorna fyller hela bilden utan luckor: varje yta går in till mitten av
linjerna runt den, och linjerna (jämn bredd LINJE_BREDD) ritas ovanpå.
Ytorna ritas med evenodd, i tur och ordning (större först).

Figurerna maskas som på webben: `klipp` är ytan mellan de mörka linjerna där
kroppen står (himlen, rutan, väggen), och figuren ritas bara där, under
linjerna. Det som står framför (tak, träd, busken) skymmer då fötterna och
han tittar fram bakom det.

Så görs en bild (--gor):
 1. Konturerna ritas i dubbel storlek (Chrome), små hål fylls och allt
    tunnas till ett skelett (som TECKNING i fargbild.py).
 2. Glapp sluts: en fri ände kopplas till närmaste linje framför sig (inom
    GLAPP_MAX px), annars förlängs den rakt fram (inom FORLANG_MAX px), och
    går inte det tas strecket bort (glans- och skuggstreck).
 3. Ytor mindre än YTA_MIN px blir linje. Linjerna ritas om med jämn bredd
    och spåras med potrace (mjuka kurvor).
 4. Färgytorna delas efter färgbilden, inte bara efter linjerna (fargytor):
    färgbilden jämnas ut (bilateralt), kvantiseras till KVANT färger och
    delas i fragment, och grannfragment slås ihop så länge kanten mellan dem
    är svag (KANT_MAX, en mjuk toning i stället för en färgkant) och färgerna
    inte skiljer för mycket (SLA_IHOP_MAX). Himmel/kulle, gräs/väg och
    vatten/land blir då egna ytor fast de saknar mörk kontur, och vågor,
    glans och vägstreck blir kvar som egna små ytor (minst FARGYTA_MIN px).
    Pixlarna under de mörka linjerna får färg från ytan bredvid.
 5. Varje yta blir en polygon med en färg ur färgbilden: en linjär toning
    om ytan har en tydlig ljusskiftning inom samma kulör (TONING_KULOR),
    annars platt (medianfärgen).
 6. Figurernas platser står i GOMSTALLEN nedan (väljs med --kandidater),
    och var och en får sin klippbana.

Kontrollen (--kontroll) ritar JSON-filen och säger till om något av detta
inte stämmer: inga fria ändar i linjerna (alla konturer slutna), inga
omålade luckor mellan ytorna, trohet mot originalfärgbilden (ΔE i Lab,
utanför linjerna: medel högst DE_MEDEL_MAX, högst DE_STOR_ANDEL av pixlarna
med ΔE över DE_STOR, och ingen yta över DE_YTA_MIN px med medel över
DE_YTA_MAX), varje figur har en klippbana där kroppen syns (KROPP_SYNS),
inne i bilden, figurerna överlappar inte varandra, och de syns mot sin
bakgrund (KONTRAST_MIN). Fel gör att skriptet slutar med kod 1.
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

def _keiws_mapp():
    """Mappen med Pensla och pensla-native (även när verktyget körs från en git worktree)."""
    import subprocess
    try:
        gemensam = subprocess.run(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'], cwd=ba.ROT,
                                  capture_output=True, text=True, check=True).stdout.strip()
        return os.path.dirname(os.path.dirname(os.path.abspath(gemensam)))
    except Exception:
        return os.path.dirname(ba.ROT)


KEIWS_MAPP = _keiws_mapp()
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
KROPP_SYNS = 0.6       # så stor del av kroppen ska synas i klippbanan
FOTTER_SYNS = 0.5      # syns mer av fötterna står han inte bakom något (varning)

# Färgytorna (fargytor)
KVANT = 32             # antal färger i kvantiseringen
KANT_MAX = 7.0         # starkare kant (ΔE över ~6 px) än så delar ytor
SLA_IHOP_MAX = 28.0    # medelfärgerna får skilja högst så mycket (Lab) för att slås ihop
FARGYTA_MIN = 24       # mindre färgytor slås ihop med sin närmaste granne (px vid 900)
TONING_KULOR = 25      # toning bara om kulören (hue, grader) skiljer mindre än så

# Trohet mot originalet (--kontroll)
DE_MEDEL_MAX = 4.0     # medel-ΔE utanför linjerna
DE_STOR = 15.0         # en pixel med större ΔE räknas som fel färg
DE_STOR_ANDEL = 0.03   # högst så stor andel pixlar med fel färg
DE_YTA_MIN = 400       # ytor större än så (px vid 900) kontrolleras var för sig
DE_YTA_MAX = 10.0      # högsta medel-ΔE i en sådan yta

# Var keIWs och kompisarna står i varje vektorbild: (x, y, s), x och y =
# mitt under fötterna. Väljs bland kandidaterna (--kandidater) och skrivs
# här för hand; en egen plats går också bra.
GOMSTALLEN = {
    # v4 (2026-11-19): kroppen ska skymmas en bit av det den står bakom
    # (ca 65–80 % synligt, matt_figurer.py), annars ser den ut att sitta
    # ovanpå eller sväva, och den vinkande armen ska synas (inga små fönster).
    'sopbil-snett': {'keiws': (760, 530, 0.33), 'gron': (97, 314, 0.3), 'rod': (780, 385, 0.3)},
    'flygplan-stort': {'keiws': (452, 170, 0.33), 'gron': (225, 432, 0.28), 'rod': (544, 287, 0.3)},
    'raket': {'keiws': (110, 509, 0.4), 'gron': (385, 347, 0.3), 'rod': (1130, 557, 0.3)},
    'segelbat': {'keiws': (865, 391, 0.3), 'gron': (860, 588, 0.3), 'rod': (300, 404, 0.3)},
    'tankbil3': {'keiws': (598, 356, 0.35), 'gron': (1080, 262, 0.28), 'rod': (1300, 198, 0.3)},
    'skordetroska6': {'keiws': (700, 170, 0.33), 'gron': (1115, 267, 0.3), 'rod': (70, 358, 0.3)},
}

# Bilder vars format avviker mycket från plattans rityta (ca 1,38:1) beskärs
# till 4:3 här: (x0, x1) i färgbildens pixlar vid 900 px höjd. Appen passar
# in bilden utan beskärning, så en 16:9-bild får annars breda tomma kanter
# upptill och nedtill.
BESKAR = {
    'skordetroska6': (200, 1400),   # 1612 x 900 (16:9) -> 1200 x 900
}


def las_bild(r, fil, hojd):
    """Som ba.las_bild, beskuren enligt BESKAR."""
    alfa, rgb = ba.las_bild(r, fil, hojd)
    if fil in BESKAR:
        x0, x1 = (round(v * hojd / ba.PAPER_H) for v in BESKAR[fil])
        alfa, rgb = np.ascontiguousarray(alfa[:, x0:x1]), np.ascontiguousarray(rgb[:, x0:x1])
    return alfa, rgb


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
    l0, l1 = ba.lab_farg(c0), ba.lab_farg(c1)
    if np.linalg.norm(l0 - l1) < TONING_MIN:
        return '#%02x%02x%02x' % tuple(np.median(px, 0).astype(int))
    # bara inom samma kulör: hue-skillnaden liten (eller någon ände nästan grå)
    k0, k1 = np.hypot(l0[1], l0[2]), np.hypot(l1[1], l1[2])
    dh = abs((np.degrees(np.arctan2(l0[2], l0[1]) - np.arctan2(l1[2], l1[1])) + 180) % 360 - 180)
    if min(k0, k1) > 10 and dh > TONING_KULOR:
        return '#%02x%02x%02x' % tuple(np.median(px, 0).astype(int))
    mx, my = xs.mean(), ys.mean()
    tm = mx * rk[0] + my * rk[1]
    p0 = (mx + rk[0] * (t0 - tm), my + rk[1] * (t0 - tm))
    p1 = (mx + rk[0] * (t1 - tm), my + rk[1] * (t1 - tm))
    hx = lambda c_: '#%02x%02x%02x' % tuple(np.round(c_).astype(int))
    return [hx(c0), hx(c1)], [round(v / F, 1) for v in (p0[0], p0[1], p1[0], p1[1])]


def _sla_ihop(frag, n, styrka, labb, kant_max, farg_max, min_area):
    """Slår ihop grannfragment (en RAG): svagaste kanten först, så länge
    kanten är svagare än kant_max och medelfärgerna skiljer mindre än
    farg_max. Sedan slås fragment mindre än min_area ihop med den granne som
    kanten är svagast mot. Returnerar en tabell fragment -> ytnummer (1..)."""
    import heapq
    area = np.bincount(frag.ravel(), minlength=n + 1).astype(float)
    summa = np.stack([np.bincount(frag.ravel(), labb[..., k].ravel(), minlength=n + 1) for k in range(3)], 1)
    # grannpar (4-grannar) och kantstyrkan mellan dem
    pa, pb, pw = [], [], []
    for a, b, wa, wb in ((frag[:, :-1], frag[:, 1:], styrka[:, :-1], styrka[:, 1:]),
                         (frag[:-1, :], frag[1:, :], styrka[:-1, :], styrka[1:, :])):
        m = (a != b) & (a > 0) & (b > 0)
        pa.append(np.minimum(a[m], b[m]))
        pb.append(np.maximum(a[m], b[m]))
        pw.append(np.maximum(wa[m], wb[m]))
    pa, pb, pw = np.concatenate(pa), np.concatenate(pb), np.concatenate(pw)
    nyckel = pa.astype(np.int64) * (n + 1) + pb
    u, inv = np.unique(nyckel, return_inverse=True)
    ws = np.bincount(inv, pw)
    wc = np.bincount(inv).astype(float)
    nb = [dict() for _ in range(n + 1)]
    for k, s, c in zip(u.tolist(), ws.tolist(), wc.tolist()):
        a, b = k // (n + 1), k % (n + 1)
        par = [s, c]
        nb[a][b] = par
        nb[b][a] = par
    foralder = np.arange(n + 1)
    levande = np.ones(n + 1, bool)

    def medel(a):
        return summa[a] / max(area[a], 1)

    def sla(a, b):
        """b in i a."""
        for c, (s, cc) in nb[b].items():
            if c == a:
                continue
            if c in nb[a]:
                nb[a][c][0] += s
                nb[a][c][1] += cc
            else:
                nb[a][c] = [s, cc]
                nb[c][a] = nb[a][c]
            nb[c].pop(b, None)
        nb[a].pop(b, None)
        nb[b] = {}
        levande[b] = False
        foralder[b] = a
        area[a] += area[b]
        summa[a] += summa[b]

    hog = [(s / c, a, b) for a in range(1, n + 1) for b, (s, c) in nb[a].items() if a < b]
    heapq.heapify(hog)
    while hog:
        w, a, b = heapq.heappop(hog)
        if w > kant_max:
            break
        if not (levande[a] and levande[b]) or b not in nb[a]:
            continue
        s, c = nb[a][b]
        if abs(s / c - w) > 1e-9:
            continue
        if np.linalg.norm(medel(a) - medel(b)) > farg_max and min(area[a], area[b]) >= min_area:
            continue
        if area[b] > area[a]:
            a, b = b, a
        sla(a, b)
        for c2, (s2, cc2) in nb[a].items():
            heapq.heappush(hog, (s2 / cc2, min(a, c2), max(a, c2)))
    # små fragment: in i den granne som kanten är svagast mot
    for _ in range(6):
        sma = [a for a in range(1, n + 1) if levande[a] and area[a] < min_area and nb[a]]
        if not sma:
            break
        for a in sorted(sma, key=lambda a: area[a]):
            if not levande[a] or area[a] >= min_area or not nb[a]:
                continue
            b = min(nb[a], key=lambda c: nb[a][c][0] / nb[a][c][1])
            sla(b, a)
    rot = foralder.copy()
    for _ in range(64):
        ny_ = rot[rot]
        if (ny_ == rot).all():
            break
        rot = ny_
    nummer = np.zeros(n + 1, np.int32)
    rotter = np.unique(rot[1:])
    nummer[rotter] = np.arange(1, len(rotter) + 1)
    return nummer[rot]


def fargytor(sk, rgb2, alfa2, logg):
    """Delar bilden i färgytor: linjeytorna (mellan skelettets linjer) delas
    vidare där färgbilden har en tydlig färgkant. Returnerar (ytnummer per
    pixel, 0 = skelettet; pixlar vars färg gissas från grannytan; linjeytorna)."""
    H, W = sk.shape
    linjeyta, n_l = nd.label(~sk)
    tjock = cv2.dilate(sk.astype(np.uint8), skiva(round(LINJE_BREDD * F / 2) + 1)).astype(bool)
    nara = cv2.dilate(sk.astype(np.uint8), skiva(round(LINJE_BREDD * F) + 2)).astype(bool)
    okand = tjock | ((alfa2 >= 128) & nara) | sk
    jamn = cv2.bilateralFilter(rgb2, 9, 25, 5)
    labb = ba.lab_farg(jamn).astype(np.float32)
    # kantstyrka: Lab-skillnad över ~6 px (Sobel på lätt utsmetad bild)
    sm = cv2.GaussianBlur(labb, (0, 0), 1.2)
    styrka = np.zeros((H, W), np.float32)
    for k in range(3):
        gx = cv2.Sobel(sm[..., k], cv2.CV_32F, 1, 0, ksize=3) / 8
        gy = cv2.Sobel(sm[..., k], cv2.CV_32F, 0, 1, ksize=3) / 8
        styrka += gx * gx + gy * gy
    styrka = np.sqrt(styrka) * 6
    del sm
    # kvantisering (k-means på ett urval, sedan närmaste centrum för alla)
    kand = np.nonzero(~okand.ravel())[0]
    rng = np.random.default_rng(1)
    urval = np.ascontiguousarray(labb.reshape(-1, 3)[rng.choice(kand, min(len(kand), 150000), replace=False)])
    _, _, centra = cv2.kmeans(urval, KVANT, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.2),
                              3, cv2.KMEANS_PP_CENTERS)
    q = np.zeros(H * W, np.int32)
    platt = labb.reshape(-1, 3)
    for i in range(0, H * W, 1 << 18):
        d = ((platt[i:i + (1 << 18), None, :] - centra[None]) ** 2).sum(-1)
        q[i:i + (1 << 18)] = d.argmin(1)
    q = q.reshape(H, W)
    # fragment: sammanhängande pixlar med samma kvantiserade färg (utanför linjerna)
    frag = np.zeros((H, W), np.int32)
    n = 0
    for c in range(KVANT):
        l_, k_ = nd.label((q == c) & ~okand)
        m = l_ > 0
        frag[m] = l_[m] + n
        n += k_
    del q
    logg.append('%d fragment' % n)
    nummer = _sla_ihop(frag, n, styrka, labb, KANT_MAX, SLA_IHOP_MAX, FARGYTA_MIN * F * F)
    yta = nummer[frag]
    yta[frag == 0] = 0
    del frag
    # En färgyta ligger alltid i en linjeyta: delas den av en linje blir delarna egna ytor.
    nyckel = yta.astype(np.int64) * (n_l + 1) + linjeyta
    nyckel[yta == 0] = 0
    _, inv = np.unique(nyckel, return_inverse=True)
    yta = inv.reshape(H, W).astype(np.int32)  # nyckel 0 (minst) blir 0
    # gissade pixlar (under och intill linjerna): närmaste färgyta i samma linjeyta
    for _ in range(4 * round(LINJE_BREDD * F) + 8):
        tom = (yta == 0) & ~sk
        if not tom.any():
            break
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            gr = np.roll(yta, (dy, dx), (0, 1))
            grl = np.roll(linjeyta, (dy, dx), (0, 1))
            m = tom & (gr > 0) & (grl == linjeyta)
            yta[m] = gr[m]
            tom &= ~m
    # linjeytor som bara består av gissade pixlar blir egna ytor
    tom = (yta == 0) & ~sk
    if tom.any():
        l_, _ = nd.label(tom)
        yta[tom] = l_[tom] + yta.max()
    # varje yta en sammanhängande bit
    ut = np.zeros((H, W), np.int32)
    n_ut = 0
    for i, sl in enumerate(nd.find_objects(yta), 1):
        if sl is None:
            continue
        l_, k_ = nd.label(yta[sl] == i)
        m = l_ > 0
        del_ = ut[sl]
        del_[m] = l_[m] + n_ut
        n_ut += k_
    logg.append('%d färgytor (%d linjeytor)' % (n_ut, n_l))
    return ut, okand, linjeyta


def ytor(yta, rgb2, okand):
    """Färgytorna: en polygon per yta (lite större, så att de täcker
    skelettet och varandra), största först."""
    lab_bild = ba.lab_farg(rgb2)
    ut = []
    for i, sl in enumerate(nd.find_objects(yta), 1):
        if sl is None:
            continue
        y0, y1 = max(0, sl[0].start - 3), min(yta.shape[0], sl[0].stop + 3)
        x0, x1 = max(0, sl[1].start - 3), min(yta.shape[1], sl[1].stop + 3)
        m = yta[y0:y1, x0:x1] == i
        stor = cv2.dilate(m.astype(np.uint8), skiva(2))
        konturer, _ = cv2.findContours(stor, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        polys = []
        for k in konturer:
            k = cv2.approxPolyDP(k, FORENKLA * F, True)[:, 0, :].astype(float)
            if len(k) < 3:
                continue
            polys.append((k + [x0, y0]) / F)
        if not polys:
            continue
        inre = m & ~okand[y0:y1, x0:x1]
        farg = yta_farg(rgb2[y0:y1, x0:x1], lab_bild[y0:y1, x0:x1], m, inre, x0, y0)
        post = {'d': polygonbana(polys)}
        if isinstance(farg, str):
            post['f'] = farg
        else:
            post['f'], post['g'] = farg
        ut.append((m.sum(), post))
    ut.sort(key=lambda t: -t[0])
    return [p for _, p in ut]


def klippbana(linjeyta, c, punkter=None):
    """Banan för linjeytan där figuren c står (vid kroppens mitt, eller vid
    punkterna), så att figuren bara syns där (som ytmasken på webben)."""
    H, W = linjeyta.shape
    punkter = punkter or [(c['x'], c['y'] - 124 * c['s'])]
    m = np.zeros((H, W), bool)
    for px, py in punkter:
        x, y = int(round(px * F)), int(round(py * F))
        for r in range(0, 12):
            del_ = linjeyta[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1]
            v = del_[del_ > 0]
            if len(v):
                m |= linjeyta == np.bincount(v).argmax()
                break
    if not m.any():
        return None
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = max(0, ys.min() - 3), min(H, ys.max() + 4), max(0, xs.min() - 3), min(W, xs.max() + 4)
    stor = cv2.dilate(m[y0:y1, x0:x1].astype(np.uint8), skiva(1))
    konturer, _ = cv2.findContours(stor, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polys = [(cv2.approxPolyDP(k, FORENKLA * F, True)[:, 0, :].astype(float) + [x0, y0]) / F for k in konturer]
    return polygonbana([p for p in polys if len(p) >= 3])


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
            klipp = fyll_bana(c['klipp'], (H, W), skala) if c.get('klipp') else np.ones((H, W), bool)
            for x0, y0, x1, y1, f in ba.rektanglar({'x': c['x'] * skala, 'y': c['y'] * skala, 's': c['s'] * skala}, ba.STILLA):
                y0, x0 = max(0, y0), max(0, x0)
                del_ = im[y0:y1, x0:x1]
                del_[klipp[y0:y1, x0:x1]] = ba.hexrgb(ba.FARGER[namn].get(f, ba.FARGER[namn]['bla']))
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
    """Fel och varningar för figurerna i data (linje = linjemask i skala).
    Figurerna ritas bara i sin klippbana (som på webben)."""
    fel, varn = [], []
    H, W = linje.shape
    rgb, _, _ = rita(data, skala, med_linje=False, med_figurer=False)
    for namn, c in data.get('figurer', {}).items():
        cc = skalad(c, skala)
        if any(x0 < 0 or y0 < 0 or x1 > W or y1 > H for x0, y0, x1, y1 in ram(cc)):
            fel.append('%s: delvis utanför bilden' % namn)
        if not c.get('klipp'):
            fel.append('%s: saknar klippbana' % namn)
            continue
        klipp = fyll_bana(c['klipp'], (H, W), skala) & ~linje
        kropp = ba.figurmask(cc, (H, W), [[0, 0, 160, 160, 'bla']])
        fotter = ba.figurmask(cc, (H, W), [[0, 168, 160, 204, 'bla']])
        syns = (kropp & klipp).sum() / max(1, kropp.sum())
        if syns < KROPP_SYNS:
            fel.append('%s: bara %d %% av kroppen syns' % (namn, 100 * syns))
        fs = (fotter & klipp).sum() / max(1, fotter.sum())
        if fs > FOTTER_SYNS:
            varn.append('%s: fötterna syns (%d %%), står inte bakom något' % (namn, 100 * fs))
        bak = kropp & ~klipp & ~linje
        omkring = cv2.dilate(kropp.astype(np.uint8), skiva(max(2, round(8 * skala)))).astype(bool) & ~kropp & klipp
        if omkring.any():
            k = np.linalg.norm(ba.lab_farg(rgb[omkring].mean(0)) - ba.lab_farg(ba.hexrgb(ba.FARGER[namn]['bla'])))
            if k < KONTRAST_MIN:
                varn.append('%s: syns dåligt mot bakgrunden (Lab %.0f)' % (namn, k))
        del bak
    namn_ = list(data.get('figurer', {}))
    for i in range(len(namn_)):
        for j in range(i + 1, len(namn_)):
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

def figurer(data):
    """Figurerna ur GOMSTALLEN med klippbanor (linjeytan där kroppen står)."""
    linje = fyll_bana(data['linje']['d'], (data['h'] * F, data['b'] * F), F)
    linjeyta, _ = nd.label(~linje)
    ut = {}
    for k, v in GOMSTALLEN.get(data['fil'], {}).items():
        c = {'x': v[0], 'y': v[1], 's': v[2]}
        klipp = klippbana(linjeyta, c, v[3] if len(v) > 3 else None)
        if klipp:
            c['klipp'] = klipp
        ut[k] = c
    return ut


def gor(fil, ut, bild):
    logg = []
    with ba.Ritare() as r:
        alfa2, rgb2 = las_bild(r, fil, ba.PAPER_H * F)
    sk = linjeskelett(alfa2, logg)
    tjock = cv2.dilate(sk.astype(np.uint8), skiva(round(LINJE_BREDD * F / 2)))
    yta, okand, _ = fargytor(sk, rgb2, alfa2, logg)
    data = {
        'format': 1, 'nr': bild['nr'], 'namn': bild['namn'], 'fil': fil,
        'b': rgb2.shape[1] // F, 'h': ba.PAPER_H,
        'ytor': ytor(yta, rgb2, okand),
        'linje': {'f': LINJEFARG, 'd': potracebana(tjock.astype(bool), 1 / F)},
    }
    if fil in BESKAR:
        data['beskar'] = list(BESKAR[fil])   # (x0, x1) i färgbilden, för granskningen
    del yta, okand, alfa2, rgb2
    data['figurer'] = figurer(data)
    os.makedirs(ut, exist_ok=True)
    p = os.path.join(ut, fil + '.json')
    json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(fil, '\n  ' + '\n  '.join(logg), '\n  %d ytor, %d kB' % (len(data['ytor']), os.path.getsize(p) // 1024))
    return data


def satt_figurer(fil, ut):
    p = os.path.join(ut, fil + '.json')
    data = json.load(open(p, encoding='utf-8'))
    data['figurer'] = figurer(data)
    json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return data


def original(fil, b):
    """Originalfärgbilden (b × 900) och dess konturer (alfa) i Chrome."""
    with ba.Ritare() as r:
        alfa, rgb = las_bild(r, fil, ba.PAPER_H)
    return rgb, alfa


def ytindex(data, shape):
    """Vilken yta som syns i varje pixel (ritordning: sista vinner), -1 = ingen."""
    idx = np.full(shape, -1, np.int32)
    for i, y in enumerate(data['ytor']):
        idx[fyll_bana(y['d'], shape)] = i
    return idx


def trohet(data, org=None):
    """Jämför färgytorna med originalfärgbilden, utanför linjerna (både
    vektorbildens och originalets). Returnerar ett mått-dict."""
    if org is None:
        org = original(data['fil'], data['b'])
    rgb_org, alfa = org
    im, linje, _ = rita(data, 1.0, med_linje=False, med_figurer=False)
    H, W = linje.shape
    bort = cv2.dilate((linje | (alfa >= 64)).astype(np.uint8), skiva(2)).astype(bool)
    de = np.linalg.norm(ba.lab_farg(im.astype(float)) - ba.lab_farg(rgb_org.astype(float)), axis=-1)
    m = ~bort
    idx = ytindex(data, (H, W))
    ytfel = []
    for i in np.unique(idx[m]):
        if i < 0:
            continue
        # ytans yttersta pixelrad är kantutjämning mot grannen, räknas inte här
        # (tunna ytor som konturer i färg fångas av totalmåtten i stället)
        mi = m & nd.binary_erosion(idx == i, np.ones((3, 3)))
        n = mi.sum()
        if n >= DE_YTA_MIN:
            v = float(de[mi].mean())
            if v > DE_YTA_MAX:
                ys, xs = np.nonzero(mi)
                ytfel.append((v, int(i), int(n), int(xs.mean()), int(ys.mean())))
    ytfel.sort(reverse=True)
    return {'medel': float(de[m].mean()), 'stor': float((de[m] > DE_STOR).mean()),
            'p95': float(np.percentile(de[m], 95)), 'ytfel': ytfel, 'de': de, 'm': m}


def kontroll(data, org=None):
    """Returnerar (fel, varningar, trohetsmått)."""
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
    # 3. trohet mot originalet
    tr = trohet(data, org)
    if tr['medel'] > DE_MEDEL_MAX:
        fel.append('medel-ΔE %.1f mot originalet (högst %.1f)' % (tr['medel'], DE_MEDEL_MAX))
    if tr['stor'] > DE_STOR_ANDEL:
        fel.append('%.1f %% av pixlarna har ΔE över %d (högst %.0f %%)' % (100 * tr['stor'], DE_STOR, 100 * DE_STOR_ANDEL))
    for v, i, n, x, y in tr['ytfel'][:6]:
        fel.append('yta %d (%d px kring %d, %d): medel-ΔE %.1f' % (i, n, x, y, v))
    if len(tr['ytfel']) > 6:
        fel.append('... och %d ytor till med för stor ΔE' % (len(tr['ytfel']) - 6))
    # 4. figurerna
    f2, v2 = kolla_figurer(data, linje, F)
    fel += f2
    varn += v2
    if not data.get('figurer'):
        varn.append('inga figurer')
    return fel, varn, tr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gor', action='store_true')
    ap.add_argument('--figurer', action='store_true', help='skriv bara om figurerna från GOMSTALLEN')
    ap.add_argument('--kandidater', action='store_true')
    ap.add_argument('--kontroll', action='store_true')
    ap.add_argument('--dekarta', action='store_true', help='spara ΔE-karta i granskning/vektor/de-NAMN.png')
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
            fel, varn, tr = kontroll(data)
            fel_totalt += len(fel)
            print(fil, 'OK' if not fel else 'FEL', '(medel-ΔE %.1f, %.1f %% över %d, 95 %%: %.1f)' % (
                tr['medel'], 100 * tr['stor'], DE_STOR, tr['p95']),
                *(['\n  FEL: ' + f for f in fel] + ['\n  obs: ' + v for v in varn]), flush=True)
            if a.dekarta:
                de = np.clip(tr['de'] / 30, 0, 1)
                bild = (np.stack([de, 1 - de, np.zeros_like(de)], -1) * 255 * tr['m'][..., None]).astype(np.uint8)
                Image.fromarray(bild).save(os.path.join(GRANSK, 'de-' + fil + '.png'))
    if fel_totalt:
        sys.exit(1)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
