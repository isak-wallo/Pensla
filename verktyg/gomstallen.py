"""Föreslår gömställen för keIWs kompisar (den gröna och den röda).

Ytorna tas fram som i appen: konturerna (bilder/farg/NAMN.svg) ritas i
bildens storlek i Chrome, och det som är svagare än LINE_ALPHA numreras i
sammanhängande ytor (4-grannar). Ett gömställe är en plats där kompisens
kropp (med ögonen) ligger nästan helt i en yta medan fötterna står bakom
dess underkant, så att han tittar fram bakom något: ett fönster, en buske,
ett moln eller en kulle. Ytan ska skilja sig tydligt i färg från kompisen
och platsen ska ligga en bit från keIWs och den andra kompisen.

Ut kommer förslagen (att klistra in i bilder.js) och förhandsbilder i
granskning/kompisar/NAMN.png med alla tre utritade så som de syns i appen.

    python verktyg/gomstallen.py              # alla aktiva och inaktiva bilder
    python verktyg/gomstallen.py 114 115      # bara de här numren
    python verktyg/gomstallen.py --rita 114   # bara förhandsbild av det som står i bilder.js

Kräver att `python -m http.server 8765` körs i repots rot.
"""
import base64
import json
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
from scipy import ndimage as nd

ROT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
UT = os.path.join(ROT, 'granskning', 'kompisar')
PAPER_H = 900
LINE_ALPHA = 200
URL = 'http://localhost:8765/'
S_MIN = 0.3   # mindre än så blir kompisarna svåra att se på en platta

src = open(os.path.join(ROT, 'keiws.js'), encoding='utf-8').read()
STILLA = json.loads(re.search(r'stilla: (\[\[.*?\]\]),', src).group(1))
# Samma färger som KOMPISAR i app.js
FARGER = {
    'keiws': {'bla': '#5685d7', 'ljus': '#6c99e4', 'oga': '#101628'},
    'gron': {'bla': '#50c499', 'ljus': '#64d2aa', 'oga': '#101628'},
    'rod': {'bla': '#d66d61', 'ljus': '#e38277', 'oga': '#101628'},
}


def bilder():
    """ALLA_BILDER, AKTIVA och BORTTAGNA ur bilder.js (via Chrome, så att JS-syntaxen inte spelar roll)."""
    return SIDA.evaluate("""async () => {
        const t = await (await fetch('bilder.js?' + Date.now())).text();
        return new Function(t + '; return [ALLA_BILDER, AKTIVA, BORTTAGNA];')();
    }""")


def ytor(fil):
    """(labels, färgbild) i bildens storlek, som labelRegions i app.js."""
    jpg = Image.open(os.path.join(ROT, 'bilder', 'farg', fil + '.jpg')).convert('RGB')
    W = round(PAPER_H * jpg.width / jpg.height)
    data = SIDA.evaluate("""async ([fil, W, H]) => {
        const im = new Image();
        im.src = 'bilder/farg/' + fil + '.svg';
        await im.decode();
        const c = document.createElement('canvas');
        c.width = W; c.height = H;
        const ctx = c.getContext('2d');
        ctx.drawImage(im, 0, 0, W, H);
        const d = ctx.getImageData(0, 0, W, H).data;
        const a = new Uint8Array(W * H);
        for (let i = 0; i < a.length; i++) a[i] = d[i * 4 + 3];
        let s = '';
        for (let i = 0; i < a.length; i += 0x8000) s += String.fromCharCode.apply(null, a.subarray(i, i + 0x8000));
        return btoa(s);
    }""", [fil, W, PAPER_H])
    alfa = np.frombuffer(base64.b64decode(data), np.uint8).reshape(PAPER_H, W)
    lab, _ = nd.label(alfa < LINE_ALPHA)
    return lab, np.asarray(jpg.resize((W, PAPER_H), Image.LANCZOS))


def lab_farg(rgb):
    """sRGB (0–255) -> CIE Lab."""
    c = np.asarray(rgb, float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192], [0.1805, 0.0722, 0.9505]])
    xyz /= [0.9505, 1.0, 1.089]
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.array([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])]).T


def hexlab(h):
    return lab_farg([int(h[i:i + 2], 16) for i in (1, 3, 5)])


def kandidater(lab, rgb, farg, s_lista):
    """Alla platser (poäng, x, y, s, yta) där kompisen kan titta fram."""
    H, W = lab.shape
    ut = []
    flab = hexlab(FARGER[farg]['bla'])
    storlek = np.bincount(lab.ravel())
    # Himlen (ytor som når överkanten) är inget gömställe: där svävar han bara
    himmel = set(np.unique(lab[0])) | set(np.unique(lab[:, 0][:H // 3])) | set(np.unique(lab[:, -1][:H // 3]))
    medel = {}
    for s in s_lista:
        b, kh, fh = round(160 * s), round(160 * s), round(44 * s)
        steg = max(6, b // 6)
        for y in range(round(204 * s) + 4, H - 2, steg):
            top = y - round(204 * s)
            for x in range(b // 2 + 30, W - b // 2 - 30, steg):
                x0 = x - b // 2
                l = lab[top + kh // 2, x]
                if l == 0 or l in himmel or storlek[l] > 0.3 * H * W:
                    continue
                kropp = lab[top:top + kh, x0:x0 + b] == l
                if kropp.mean() < 0.9:
                    continue
                ogon = lab[top + round(25 * s):top + round(61 * s), x0 + round(22 * s):x0 + round(138 * s)] == l
                if not ogon.all():
                    continue
                fotter = lab[y - fh:y, x0:x0 + b] == l
                if fotter.mean() > 0.4:
                    continue
                if l not in medel:
                    medel[l] = lab_farg(rgb[lab == l].mean(0))
                kontrast = np.linalg.norm(medel[l] - flab)
                if kontrast < 40:
                    continue
                ut.append((kontrast + 40 * s, x, y, s, int(l)))
    return ut


def valj(kand, upptagna, min_avst=260):
    """Bästa kandidaten som ligger minst min_avst från de upptagna platserna."""
    for p, x, y, s, l in sorted(kand, reverse=True):
        mitt = (x, y - 120 * s)
        if all(np.hypot(mitt[0] - ux, mitt[1] - uy) >= min_avst for ux, uy in upptagna):
            return x, y, s, l
    return None


def rita(lab, rgb, platser, fil):
    """Förhandsbild: färgbilden blekt, kompisarna maskade till sina ytor, ytorna markerade."""
    im = Image.fromarray((rgb * 0.55 + 255 * 0.45).astype(np.uint8))
    for namn, c in platser.items():
        if not c:
            continue
        s, x, y = c['s'], c['x'], c['y']
        lager = Image.new('RGBA', im.size)
        d = ImageDraw.Draw(lager)
        X = lambda v: round(x + (v - 80) * s)
        Y = lambda v: round(y + (v - 204) * s)
        for x0, y0, x1, y1, f in STILLA:
            d.rectangle([X(x0), Y(y0), X(x1) - 1, Y(y1) - 1], fill=FARGER[namn][f])
        mask = np.isin(lab, [lab[round(py), round(px)] for px, py in c['ytor']])
        a = np.asarray(lager).copy()
        a[..., 3] = np.where(mask, a[..., 3], 0)
        im.paste(Image.fromarray(a), (0, 0), Image.fromarray(a))
        ImageDraw.Draw(im).ellipse([x - 5, y - 5, x + 5, y + 5], outline=FARGER[namn]['bla'], width=3)
    im.save(os.path.join(UT, fil + '.png'))


def main():
    global SIDA
    arg = sys.argv[1:]
    bara_rita = '--rita' in arg
    nummer = {int(a) for a in arg if a.isdigit()}
    os.makedirs(UT, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        SIDA = b.new_page()
        SIDA.goto(URL + 'galleri.html')
        alla, aktiva, borttagna = bilder()
        for bild in alla:
            if bild['nr'] in borttagna or bild.get('utanFarg') or (nummer and bild['nr'] not in nummer):
                continue
            lab, rgb = ytor(bild['fil'])
            k = bild['keiws']
            platser = {'keiws': k, 'gron': bild.get('gron'), 'rod': bild.get('rod')}
            if not bara_rita:
                upptagna = [(k['x'], k['y'] - 120 * k['s'])]
                s_lista = sorted({max(S_MIN, round(k['s'] * f, 2)) for f in (0.8, 0.9, 1.0)})
                for farg in ('gron', 'rod'):
                    v = valj(kandidater(lab, rgb, farg, s_lista), upptagna)
                    if not v:
                        print(bild['nr'], bild['fil'], farg, 'INGET GÖMSTÄLLE')
                        platser[farg] = None
                        continue
                    x, y, s, l = v
                    py, px = map(int, np.argwhere(lab == l)[len(np.argwhere(lab == l)) // 2])
                    # ytpunkten: mitt i kroppen om den ligger i ytan
                    kx, ky = x, round(y - 120 * s)
                    if lab[ky, kx] == l:
                        px, py = kx, ky
                    platser[farg] = {'x': x, 'y': y, 's': s, 'ytor': [[px, py]]}
                    upptagna.append((x, y - 120 * s))
                    print(f"    {bild['nr']} {bild['fil']} {farg}: {{ x: {x}, y: {y}, s: {s}, ytor: [[{px}, {py}]] }}")
            rita(lab, rgb, platser, bild['fil'])
        b.close()


if __name__ == '__main__':
    main()
