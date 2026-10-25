"""Gömställen för keIWs och hans kompisar (den gröna och den röda).

Ytorna tas fram som i appen: konturerna (bilder/farg/NAMN.svg) ritas i
bildens storlek i Chrome, och det som är svagare än LINE_ALPHA numreras i
sammanhängande ytor (4-grannar). Figuren syns bara i sin yta.

Ett bra gömställe är där han tittar fram bakom något: kroppen och ögonen
ligger i en yta (himlen, ett fönster, en vägg) och precis under kroppen
börjar en sak som står framför honom (en buske, en höbal, fönsterkarmen,
motorhuven) och skymmer fötterna. Kanten han tittar fram bakom ska vara en
riktig, mörk kontur i färgbilden, inte bara en färgskiftning mellan två fält
(sådana kanter spårar TECKNING också, men där ser det ut som att han står
mitt i ett fält). Saken framför ska vara en och samma sak över hela hans
bredd.

Det går inte att avgöra helt automatiskt vad som är fint, så valet görs i
två steg:

    python verktyg/gomstallen.py --kandidater 114 115
        Söker gömställen och ritar numrerade kandidater i
        granskning/kompisar/kand-NAMN.png (kandidaterna sparas i
        granskning/kompisar/kandidater.json). Titta på bilderna.
    python verktyg/gomstallen.py --valj 114:keiws=3,gron=7,rod=1 115:gron=2
        Skriver de valda kandidaterna i bilder.js. keiws=- behåller den
        befintliga platsen, rod=B flyttar rod dit keIWs står nu och gron=@640,420,0.4 är en egen plats (x, y
        under fötterna, skala; ytan tas mitt i kroppen). Säger till om
        figuren är för lik ytan i färg.
    python verktyg/gomstallen.py --rita 114 115
        Förhandsbild av det som står i bilder.js (granskning/kompisar/NAMN.png).

Utan nummer gäller det alla bilder som inte är borttagna. Kräver att
`python -m http.server 8765` körs i repots rot.
"""
import base64
import json
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
from scipy import ndimage as nd

ROT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
UT = os.path.join(ROT, 'granskning', 'kompisar')
KANDIDATFIL = os.path.join(UT, 'kandidater.json')
PAPER_H = 900
LINE_ALPHA = 200
URL = 'http://localhost:8765/'
SKALOR = (0.3, 0.36, 0.42, 0.5)
KROPP_MIN = 0.85    # så stor del av kroppen som ska ligga i ytan
FOTTER_MAX = 0.25   # högst så stor del av fötterna får synas
MORK = 95           # konturen framför honom ska vara mörkare än så (luminans 0–255)
LINJE_MIN = 0.8     # andel av kanten under honom som ska vara mörk kontur
FRAMFOR_MIN = 0.6   # andel av bredden där samma sak står framför
KONTRAST_MIN = 30   # Lab-avstånd mellan figurens färg och ytan bakom
ANTAL = 16          # kandidater per bild

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


def kandidater(lab, rgb):
    """Platser där en figur tittar fram bakom något, bästa först och spridda över bilden."""
    H, W = lab.shape
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    flab = {k: hexlab(v['bla']) for k, v in FARGER.items()}
    medel = {}
    hitta = []
    for s in SKALOR:
        b, kh, fh, hel = round(160 * s), round(160 * s), round(44 * s), round(204 * s)
        steg = max(5, b // 7)
        for y in range(hel + 4, H - 2, steg):
            top = y - hel
            for x in range(b // 2 + 10, W - b // 2 - 10, steg):
                x0 = x - b // 2
                l = lab[top + kh // 2, x]
                if l == 0:
                    continue
                kropp = lab[top:top + kh, x0:x0 + b] == l
                if kropp.mean() < KROPP_MIN:
                    continue
                ogon = lab[top + round(25 * s):top + round(61 * s), x0 + round(22 * s):x0 + round(138 * s)] == l
                if not ogon.all():
                    continue
                if (lab[y - fh:y, x0:x0 + b] == l).mean() > FOTTER_MAX:
                    continue
                # Kanten under honom: första raden (från mitten av kroppen) som inte är ytan
                under = lab[top + kh // 2:y, x0:x0 + b] != l
                har = under.any(0)
                if har.mean() < 0.9:
                    continue
                kant = top + kh // 2 + under.argmax(0)
                kol = np.arange(x0, x0 + b)[har]
                kant = kant[har]
                # Är kanten en mörk kontur i färgbilden?
                mork = np.array([lum[max(0, r - 3):min(H, r + 9), c].min() for r, c in zip(kant, kol)])
                linje = (mork < MORK).mean()
                if linje < LINJE_MIN:
                    continue
                # Vad står framför: första yta under kanten i varje kolumn
                framfor = []
                for r, c in zip(kant, kol):
                    kolumn = lab[r:min(H, r + 16), c]
                    nz = kolumn[(kolumn != 0) & (kolumn != l)]
                    framfor.append(nz[0] if len(nz) else 0)
                framfor = np.array(framfor)
                m = np.bincount(framfor[framfor > 0]).argmax() if (framfor > 0).any() else 0
                andel = (framfor == m).mean() if m else 0
                if andel < FRAMFOR_MIN:
                    continue
                if l not in medel:
                    medel[l] = lab_farg(rgb[lab == l].mean(0))
                kontrast = {k: float(np.linalg.norm(medel[l] - v)) for k, v in flab.items()}
                if max(kontrast.values()) < KONTRAST_MIN:
                    continue
                poang = 100 * s + 25 * linje + 15 * andel + 0.1 * kropp.mean() * 100
                hitta.append((poang, x, y, s, int(l), int(m), round(top + kh // 2), kontrast))
    # Spridda: en per par av yta och sak framför, och en bit ifrån varandra
    valda, par = [], set()
    for p, x, y, s, l, m, my, k in sorted(hitta, key=lambda h: -h[0]):
        if (l, m) in par:
            continue
        mitt = (x, y - 120 * s)
        if any(np.hypot(mitt[0] - v['x'], mitt[1] - (v['y'] - 120 * v['s'])) < 130 for v in valda):
            continue
        par.add((l, m))
        valda.append({'x': x, 'y': y, 's': s, 'ytor': [[x, my]],
                      'kontrast': {kk: round(vv) for kk, vv in k.items()}})
        if len(valda) >= ANTAL:
            break
    return valda


def rita_figur(im, lab, c, farg, nummer=None):
    """Ritar figuren maskad till sina ytor (som i appen) och ev. ett nummer bredvid."""
    s, x, y = c['s'], c['x'], c['y']
    lager = Image.new('RGBA', im.size)
    d = ImageDraw.Draw(lager)
    X = lambda v: round(x + (v - 80) * s)
    Y = lambda v: round(y + (v - 204) * s)
    for x0, y0, x1, y1, f in STILLA:
        d.rectangle([X(x0), Y(y0), X(x1) - 1, Y(y1) - 1], fill=FARGER[farg][f])
    mask = np.isin(lab, [lab[round(py), round(px)] for px, py in c['ytor']])
    a = np.asarray(lager).copy()
    a[..., 3] = np.where(mask, a[..., 3], 0)
    im.paste(Image.fromarray(a), (0, 0), Image.fromarray(a))
    if nummer is not None:
        font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 30)
        dd = ImageDraw.Draw(im)
        tx, ty = X(160) + 4, Y(0) - 6
        dd.rectangle([tx - 3, ty, tx + 22 * len(str(nummer)) + 3, ty + 36], fill='white', outline='black')
        dd.text((tx, ty - 2), str(nummer), fill='black', font=font)


def blek(rgb):
    return Image.fromarray((rgb * 0.7 + 255 * 0.3).astype(np.uint8))


def satt_in(rader, nr, platser):
    """Byter keiws/gron/rod i bild nr:s rad i bilder.js."""
    for i, rad in enumerate(rader):
        if not re.match(r'\s*\{ nr: %d,' % nr, rad):
            continue
        for namn, c in platser.items():
            ny = '%s: { x: %d, y: %d, s: %s, ytor: %s }' % (namn, c['x'], c['y'], c['s'], json.dumps(c['ytor'], separators=(',', ':')).replace(',', ', '))
            gammal = re.search(r'%s: \{[^{}]*\[\[[^{}]*\]\][^{}]*\}' % namn, rad)
            if gammal:
                rad = rad[:gammal.start()] + ny + rad[gammal.end():]
            else:
                # sist i posten, före '}' (och en ev. kommentar)
                slut = rad.rindex('}')
                rad = rad[:slut].rstrip() + ', ' + ny + ' ' + rad[slut:]
        rader[i] = rad
        return
    raise SystemExit('Hittar inte nr %d i bilder.js' % nr)


def main():
    global SIDA
    arg = sys.argv[1:]
    os.makedirs(UT, exist_ok=True)
    if '--valj' in arg:
        kand = json.load(open(KANDIDATFIL, encoding='utf-8'))
        p = os.path.join(ROT, 'bilder.js')
        rader = open(p, encoding='utf-8').read().split('\n')
        for a in arg[arg.index('--valj') + 1:]:
            nr, val = a.split(':')
            platser = {}
            for namn, k in re.findall(r'(\w+)=(@[\d.]+,[\d.]+,[\d.]+|[\d-]+|B)', val):
                if k == 'B':
                    # den plats keIWs har nu (före ändringarna på raden)
                    rad = next(r for r in rader if re.match(r'\s*\{ nr: %s,' % nr, r))
                    g = re.search(r'keiws: \{ x: (\d+), y: (\d+), s: ([\d.]+), ytor: (\[\[.*?\]\]) \}', rad)
                    platser[namn] = {'x': int(g[1]), 'y': int(g[2]), 's': g[3], 'ytor': json.loads(g[4])}
                elif k.startswith('@'):
                    x, y, s = (float(t) for t in k[1:].split(','))
                    platser[namn] = {'x': round(x), 'y': round(y), 's': s, 'ytor': [[round(x), round(y - 124 * s)]]}
                elif k != '-':
                    c = kand[nr][int(k) - 1]
                    if c['kontrast'][namn] < KONTRAST_MIN:
                        print('OBS', nr, namn, k, 'lik ytan i färg', c['kontrast'][namn])
                    platser[namn] = {kk: c[kk] for kk in ('x', 'y', 's', 'ytor')}
            satt_in(rader, int(nr), platser)
        open(p, 'w', encoding='utf-8').write('\n'.join(rader))
        return
    nummer = {int(a) for a in arg if a.isdigit()}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        SIDA = b.new_page()
        SIDA.goto(URL + 'galleri.html')
        alla, aktiva, borttagna = bilder()
        kand = json.load(open(KANDIDATFIL, encoding='utf-8')) if os.path.exists(KANDIDATFIL) else {}
        for bild in alla:
            if bild['nr'] in borttagna or bild.get('utanFarg') or (nummer and bild['nr'] not in nummer):
                continue
            lab, rgb = ytor(bild['fil'])
            if '--kandidater' in arg:
                k = kandidater(lab, rgb)
                kand[str(bild['nr'])] = k
                im = blek(rgb)
                for i, c in enumerate(k):
                    rita_figur(im, lab, c, 'keiws', i + 1)
                im.save(os.path.join(UT, 'kand-' + bild['fil'] + '.png'))
                print(bild['nr'], bild['fil'], len(k), 'kandidater')
            else:
                im = blek(rgb)
                for namn in ('keiws', 'gron', 'rod'):
                    if bild.get(namn):
                        rita_figur(im, lab, bild[namn], namn)
                im.save(os.path.join(UT, bild['fil'] + '.png'))
        if '--kandidater' in arg:
            json.dump(kand, open(KANDIDATFIL, 'w', encoding='utf-8'))
        b.close()


if __name__ == '__main__':
    main()
