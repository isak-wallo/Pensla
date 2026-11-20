"""Gemensamma delar för bildöversynen (bildoversyn.py) och vektorbilderna
(vektorbild.py): konturerna i bildens storlek, skelett, glapp i konturerna
och var keIWs och kompisarna hamnar.

Konturerna ritas i Chrome (Playwright) precis som i appen, och det som är
svagare än LINE_ALPHA räknas som yta (4-grannar), som labelRegions i app.js.
"""
import base64
import json
import os
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fargbild import tunna, utan_sporrar  # noqa: E402

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FARG = os.path.join(ROT, 'bilder', 'farg')
PAPER_H = 900
LINE_ALPHA = 200
K8 = np.ones((3, 3), int)

# keIWs klossar (keiws.js): stilla, blink och vinka-animationen.
_src = open(os.path.join(ROT, 'keiws.js'), encoding='utf-8').read()
STILLA = json.loads(re.search(r'stilla: (\[\[.*?\]\]),', _src).group(1))
VINKA = [b['rekt'] for b in json.loads(re.search(r'vinka: (\[\{.*\}\])\s*\n\};', _src, re.S).group(1))]
FARGER = {
    'keiws': {'bla': '#5685d7', 'ljus': '#6c99e4', 'oga': '#101628', 'mellan': '#4b75c0', 'mork': '#4065a8'},
    'gron': {'bla': '#50c499', 'ljus': '#64d2aa', 'oga': '#101628'},
    'rod': {'bla': '#d66d61', 'ljus': '#e38277', 'oga': '#101628'},
}
# Studsen när han poppar upp (app.js: upp = 1 + 2,5(p-1)^3 + 1,5(p-1)^2)
# lyfter honom som mest 0,08 × 204 enheter över sin plats.
STUDS = 17


def bilder():
    """(ALLA_BILDER, AKTIVA, BORTTAGNA) ur bilder.js (via node)."""
    import subprocess
    js = ("const t=require('fs').readFileSync(process.argv[1],'utf8');"
          "process.stdout.write(JSON.stringify(new Function(t+';return [ALLA_BILDER,AKTIVA,BORTTAGNA];')()))")
    ut = subprocess.run(['node', '-e', js, os.path.join(ROT, 'bilder.js')], capture_output=True, check=True)
    return json.loads(ut.stdout.decode('utf-8'))


class Ritare:
    """Ritar konturernas SVG i Chrome och ger alfakanalen (som lCtx i app.js)."""

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        self.b = self.pw.chromium.launch()
        self.sida = self.b.new_page()
        self.sida.set_content('<html><body></body></html>')
        return self

    def __exit__(self, *a):
        self.b.close()
        self.pw.stop()

    def alfa(self, svg_text, W, H):
        data = self.sida.evaluate("""async ([svg, W, H]) => {
            const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml' }));
            const im = new Image();
            im.src = url;
            await im.decode();
            const c = document.createElement('canvas');
            c.width = W; c.height = H;
            const ctx = c.getContext('2d');
            ctx.drawImage(im, 0, 0, W, H);
            URL.revokeObjectURL(url);
            const d = ctx.getImageData(0, 0, W, H).data;
            const a = new Uint8Array(W * H);
            for (let i = 0; i < a.length; i++) a[i] = d[i * 4 + 3];
            let s = '';
            for (let i = 0; i < a.length; i += 0x8000) s += String.fromCharCode.apply(null, a.subarray(i, i + 0x8000));
            return btoa(s);
        }""", [svg_text, W, H])
        return np.frombuffer(base64.b64decode(data), np.uint8).reshape(H, W)


def las_bild(ritare, fil, hojd=PAPER_H):
    """(alfa för konturerna, färgbilden RGB) i bildens storlek (hojd px hög)."""
    jpg = Image.open(os.path.join(FARG, fil + '.jpg')).convert('RGB')
    W = round(hojd * jpg.width / jpg.height)
    svg = open(os.path.join(FARG, fil + '.svg'), encoding='utf-8').read()
    return ritare.alfa(svg, W, hojd), np.asarray(jpg.resize((W, hojd), Image.LANCZOS))


def grannar(sk):
    return nd.convolve(sk.astype(np.uint8), K8.astype(np.uint8), mode='constant') - sk


def andpunkter(sk):
    """Fria ändar i ett skelett: grannarna (1–3 st) ligger i en enda klump
    runt pixeln (en övergång 0 -> 1 varv runt den)."""
    m = np.pad(sk.astype(np.uint8), 1)
    H, W = sk.shape
    ring = [m[0:H, 1:W + 1], m[0:H, 2:], m[1:H + 1, 2:], m[2:, 2:], m[2:, 1:W + 1], m[2:, 0:W], m[1:H + 1, 0:W], m[0:H, 0:W]]
    B = sum(r.astype(int) for r in ring)
    A = sum(((ring[i] == 0) & (ring[(i + 1) % 8] == 1)).astype(int) for i in range(8))
    return sk & (B >= 1) & (B <= 3) & (A == 1)


def skelett(linje, sporre=6):
    return utan_sporrar(tunna(linje), sporre)


def egen_gren(sk, start, steg):
    """Skelettpixlar man når från start längs skelettet inom `steg` steg."""
    H, W = sk.shape
    sett = {start}
    rand = [start]
    for _ in range(steg):
        ny = []
        for y, x in rand:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    q = (y + dy, x + dx)
                    if 0 <= q[0] < H and 0 <= q[1] < W and sk[q] and q not in sett:
                        sett.add(q)
                        ny.append(q)
        rand = ny
        if not rand:
            break
    return sett


def riktning(gren, start):
    """Enhetsvektor från grenens inre mot änden (y, x)."""
    pts = np.array(list(gren), float)
    d = np.array(start, float) - pts.mean(0)
    n = np.hypot(*d)
    return d / n if n else d


def andar(sk, kant=4, radie=20, gren=40):
    """Fria ändar i skelettet. Varje ände får typ 'glapp' (en annan linje finns
    inom `radie` px framför den: konturen har ett hål) eller 'lös' (ett streck
    som slutar fritt). Returnerar [(y, x, typ, avstånd, (ty, tx))]."""
    H, W = sk.shape
    e = andpunkter(sk)
    ys, xs = np.nonzero(e)
    ut = []
    for y, x in zip(ys, xs):
        if y < kant or x < kant or y >= H - kant or x >= W - kant:
            continue
        egen = egen_gren(sk, (y, x), gren)
        rk = riktning(egen, (y, x))
        y0, y1, x0, x1 = max(0, y - radie), min(H, y + radie + 1), max(0, x - radie), min(W, x + radie + 1)
        ty, tx = np.nonzero(sk[y0:y1, x0:x1])
        bast = None
        for yy, xx in zip(ty + y0, tx + x0):
            if (yy, xx) in egen:
                continue
            d = np.hypot(yy - y, xx - x)
            if d > radie or d < 1:
                continue
            # framåt (eller åt sidan), inte bakåt längs sitt eget streck
            if ((yy - y) * rk[0] + (xx - x) * rk[1]) / d < -0.2:
                continue
            if bast is None or d < bast[0]:
                bast = (d, (int(yy), int(xx)))
        if bast:
            ut.append((int(y), int(x), 'glapp', round(bast[0], 1), bast[1]))
        else:
            ut.append((int(y), int(x), 'lös', None, None))
    return ut


# ---------------------------------------------------------------- figurerna

def rektanglar(c, rekt, lyft=0.0):
    """Klossarna i bildkoordinater (x0, y0, x1, y1, färgnyckel), som ritaKeiws."""
    x, y, s = c['x'], c['y'] - lyft * c['s'], c['s']
    X = lambda v: round(x + (v - 80) * s)
    Y = lambda v: round(y + (v - 204) * s)
    return [(X(a), Y(b), X(cc), Y(d), f) for a, b, cc, d, f in rekt]


def figurmask(c, shape, rekt=None, lyft=0.0):
    m = np.zeros(shape, bool)
    H, W = shape
    for x0, y0, x1, y1, _ in rektanglar(c, rekt or STILLA, lyft):
        m[max(0, y0):max(0, min(H, y1)), max(0, x0):max(0, min(W, x1))] = True
    return m


def hela_figuren(c, shape):
    """Allt figuren täcker: stilla, alla vinkbilder och studsen."""
    m = figurmask(c, shape)
    for r in VINKA:
        m |= figurmask(c, shape, r)
    m |= figurmask(c, shape, STILLA, STUDS)
    return m


def utanfor(c, W, H):
    """Hur mycket av figurens ram (med vinkande arm och studs) som är utanför bilden."""
    x0 = c['x'] + (-44 - 80) * c['s']
    x1 = c['x'] + (216 - 80) * c['s']
    y0 = c['y'] + (-48 - STUDS - 204) * c['s']
    return x0 < 0 or x1 > W or y0 < 0 or c['y'] > H


def kolla_figur(c, alfa, lab):
    """Hur figuren c (x, y, s, ytor) syns i appen i dag: andel av figuren som
    döljs (av streck resp. av annan yta), om ett streck går över kroppen, om
    fötterna står på något och om den vinkande armen klipps."""
    H, W = lab.shape
    ytor = {int(lab[min(H - 1, round(py)), min(W - 1, round(px))]) for px, py in c['ytor']}
    ytor.discard(0)
    i_yta = np.isin(lab, list(ytor)) if ytor else np.zeros_like(lab, bool)
    under_fotter = np.zeros_like(i_yta)
    under_fotter[:min(H, int(c['y']) + 1)] = True
    syns = i_yta & under_fotter
    linje = alfa >= LINE_ALPHA
    fig = figurmask(c, (H, W))
    kropp = figurmask(c, (H, W), [[0, 0, 160, 160, 'bla']])
    n = max(1, fig.sum())
    dold = fig & ~syns
    res = {
        'dold': round(100 * dold.sum() / n, 1),
        'dold_streck': round(100 * (dold & linje).sum() / n, 1),
        'kropp_dold': round(100 * (kropp & ~syns).sum() / max(1, kropp.sum()), 1),
        'streck_over_kropp': bool((kropp & linje).sum() > 0.005 * max(1, kropp.sum())),
        'utanfor': utanfor(c, W, H),
    }
    arm = np.zeros((H, W), bool)
    for r in VINKA:
        arm |= figurmask(c, (H, W), r)
    arm &= ~fig
    res['arm_dold'] = round(100 * (arm & ~i_yta).sum() / max(1, arm.sum()), 1)
    # Står fötterna på något? En linje (eller en annan yta) strax under
    # fötterna, under största delen av dem. Annars svävar figuren mitt i sin yta.
    fx0, fx1 = round(c['x'] + (22 - 80) * c['s']), round(c['x'] + (138 - 80) * c['s'])
    yy = int(round(c['y']))
    band = lab[min(H - 1, yy):min(H, yy + max(4, round(14 * c['s']))), max(0, fx0):min(W, fx1)]
    if band.size:
        stod = (~np.isin(band, list(ytor))).any(0).mean()
    else:
        stod = 1.0
    res['star_pa'] = round(float(stod), 2)
    return res


def lab_farg(rgb):
    """sRGB (0–255) -> CIE Lab."""
    c = np.asarray(rgb, float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192], [0.1805, 0.0722, 0.9505]])
    xyz /= [0.9505, 1.0, 1.089]
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def hexrgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def stora_bitar(m, minst):
    """m utan sammanhängande bitar (8-grannar) mindre än `minst` px."""
    bit, n = nd.label(m, np.ones((3, 3)))
    storlek = np.bincount(bit.ravel())
    storlek[0] = 0
    return storlek[bit] >= minst
