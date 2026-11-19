"""Syns armen när figurerna vinkar? Mäter, maskat som appen (ytorna i
bilder.js), hur stor del av den vinkande armen (vinka-rutorna med armen
uppe) som syns för keIWs och kompisarna i de aktiva bilderna.

    python verktyg/vinkarm.py [NR...]            # mät (alla aktiva om inga NR)
    python verktyg/vinkarm.py --forslag [NR...]  # + föreslå mindre s där armen klipps
    python verktyg/vinkarm.py --ark FIL.json     # före/efter-ark för ändringarna i FIL.json
                                                 #   {"NR": {"keiws": {"x", "y", "s", "ytor"?}, ...}}

Armen räknas som klippt när mindre än ARM_MIN av den syns. Förslaget är
den minsta ändringen som får armen att synas: s krymps högst KRYMP_MAX och
figuren flyttas högst 0,15 kroppsbredd, och kroppen ska synas nästan lika
mycket som förut; räcker inte det står "ny plats" och platsen får väljas
för hand (gomstallen.py). Förslagen sparas i granskning/granskare/vinka/forslag.json.
Arken hamnar i granskning/granskare/vinka/ (före stilla | före vinkar |
efter stilla | efter vinkar för varje ändrad figur, och hela bilden efter).
"""
import base64, json, os, re, sys
from playwright.sync_api import sync_playwright

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UT = os.path.join(P, 'granskning', 'granskare', 'vinka')
ARM_MIN = 0.9
KRYMP_MAX = 0.2
FLYTT = 0.15   # högst så stor flytt (andel av kroppens bredd); --langt: 0.6

def b64(p):
    return base64.b64encode(open(p, 'rb').read()).decode()

JS = open(os.path.join(P, 'keiws.js'), encoding='utf-8').read() + r"""
window.KEIWS = KEIWS;
window.FARG = {
  keiws: KEIWS.farger,
  gron: { bla: '#50c499', ljus: '#64d2aa', oga: '#101628' },
  rod: { bla: '#d66d61', ljus: '#e38277', oga: '#101628' },
};
// Vinka-bilderna med armen uppe (armen = rutan till höger om kroppen, x0 >= 160, y0 < 64)
window.ARMBILDER = KEIWS.vinka.map(b => b.rekt).filter(r => r.some(a => a[0] >= 160 && a[1] < 64));
window.VINKAR = ARMBILDER.find(r => r.some(a => a[0] === 180 && a[1] === -48)) || ARMBILDER[0];
window.ladda = src => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = src; });
window.ritaFig = (ctx, x, y, s, rekt, farger) => {
  const X = v => Math.round(x + (v - 80) * s), Y = v => Math.round(y + (v - 204) * s);
  rekt.forEach(([x0, y0, x1, y1, f]) => {
    ctx.fillStyle = farger[f] || farger.bla;
    ctx.fillRect(X(x0), Y(y0), X(x1) - X(x0), Y(y1) - Y(y0));
  });
};
// Bilden: linjer, ytnummer (som labelRegions i app.js) och färgbild
window.forbered = async (svg, jpg) => {
  const org = await ladda(jpg);
  const H = 900, W = Math.round(H * org.width / org.height);
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const l = c.getContext('2d'); l.drawImage(await ladda(svg), 0, 0, W, H);
  const alfa = l.getImageData(0, 0, W, H).data;
  const lab = new Int32Array(W * H);
  for (let i = 0; i < W * H; i++) lab[i] = alfa[i * 4 + 3] < 200 ? -1 : 0;
  let id = 0; const st = new Int32Array(W * H);
  for (let s0 = 0; s0 < W * H; s0++) {
    if (lab[s0] !== -1) continue; id++; let n = 0; st[n++] = s0; lab[s0] = id;
    while (n) { const p = st[--n], x = p % W;
      if (x > 0 && lab[p - 1] === -1) { lab[p - 1] = id; st[n++] = p - 1; }
      if (x < W - 1 && lab[p + 1] === -1) { lab[p + 1] = id; st[n++] = p + 1; }
      if (p >= W && lab[p - W] === -1) { lab[p - W] = id; st[n++] = p - W; }
      if (p < W * (H - 1) && lab[p + W] === -1) { lab[p + W] = id; st[n++] = p + W; } }
  }
  window.B = { W, H, lab, linjer: c, org };
};
window.ytset = k => new Set((k.ytor || [[k.x, k.y - 124 * k.s]]).map(([px, py]) => B.lab[Math.round(py) * B.W + Math.round(px)]).filter(v => v > 0));
// Andel synliga pixlar av rutorna (i figurens mått) för figuren k
window.syns = (k, rutor) => {
  const ok = ytset(k), { W, H, lab } = B;
  const X = v => Math.round(k.x + (v - 80) * k.s), Y = v => Math.round(k.y + (v - 204) * k.s);
  let tot = 0, ja = 0;
  for (const [a, b, c, d] of rutor)
    for (let y = Y(b); y < Y(d); y++) for (let x = X(a); x < X(c); x++) {
      tot++; if (x >= 0 && y >= 0 && x < W && y < H && ok.has(lab[y * W + x])) ja++;
    }
  return tot ? ja / tot : 0;
};
window.armRutor = () => {
  const ut = [];
  for (const r of ARMBILDER) for (const a of r) if (a[0] >= 160 && a[1] < 64 && !ut.some(b => b[0] === a[0] && b[1] === a[1])) ut.push(a);
  return ut;
};
window.matt = k => ({ arm: syns(k, armRutor()), kropp: syns(k, [[0, 0, 160, 160]]) });
// Minsta ändring (krymp högst kmax, flytta högst 0,15 kroppsbredd) där armen
// syns (armMin) och kroppen syns nästan lika mycket som förut.
window.sok = (k, armMin, kmax, flytt) => {
  const m0 = matt(k), steg = Math.max(2, Math.round(k.s * 160 * 0.05)), max = Math.round(k.s * 160 * (flytt || 0.15));
  let bast = null;
  for (let f = 1.0; f >= 1 - kmax - 1e-9; f -= 0.01) {
    const s = Math.round(k.s * f * 1000) / 1000;
    for (let dx = -max; dx <= max; dx += steg) for (let dy = -max; dy <= max; dy += steg) {
      const k2 = Object.assign({}, k, { x: k.x + dx, y: k.y + dy, s });
      const x0 = k2.x - 126 * s, x1 = k2.x + 138 * s, y0 = k2.y - 252 * s;
      if (x0 < 0 || y0 < 0 || x1 >= B.W) continue;
      const m = matt(k2);
      if (m.arm < armMin || m.kropp < Math.max(0.6, m0.kropp - 0.12)) continue;
      const kost = (1 - f) * 100 + (Math.abs(dx) + Math.abs(dy)) / (k.s * 160) * 60;
      if (!bast || kost < bast.kost) bast = { kost, k: k2, m };
    }
  }
  return bast;
};
// Färgbilden med figurerna maskade (rekt = stilla eller vinkar)
window.rita = (fig, rekt) => {
  const { W, H, lab } = B;
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const f = c.getContext('2d'); f.drawImage(B.org, 0, 0, W, H);
  for (const n of ['keiws', 'gron', 'rod']) {
    const k = fig[n]; if (!k) continue;
    const ok = ytset(k);
    const t = document.createElement('canvas'); t.width = W; t.height = H;
    const tc = t.getContext('2d'); ritaFig(tc, k.x, k.y, k.s, rekt, FARG[n]);
    const im = tc.getImageData(0, 0, W, H), d = im.data;
    for (let i = 0; i < W * H; i++) if (d[i * 4 + 3] && !ok.has(lab[i])) d[i * 4 + 3] = 0;
    tc.putImageData(im, 0, 0); f.drawImage(t, 0, 0);
  }
  f.drawImage(B.linjer, 0, 0);
  return c;
};
window.ark = (fore, efter, titel) => {
  const delar = [];
  const sF = rita(fore, KEIWS.stilla), vF = rita(fore, VINKAR), sE = rita(efter, KEIWS.stilla), vE = rita(efter, VINKAR);
  const Z = 230, g = 12, top = 44, rad = 30;
  const andrade = ['keiws', 'gron', 'rod'].filter(n => efter[n] && JSON.stringify(efter[n]) !== JSON.stringify(fore[n]));
  const helW = 4 * Z + 3 * g, helH = Math.round(helW * B.H / B.W);
  const c = document.createElement('canvas');
  c.width = helW + 2 * g; c.height = top + andrade.length * (Z + rad + g) + helH + rad + g;
  const x = c.getContext('2d');
  x.fillStyle = '#ddd'; x.fillRect(0, 0, c.width, c.height);
  x.fillStyle = '#000'; x.font = 'bold 22px Segoe UI, sans-serif'; x.fillText(titel, g, 30);
  x.font = 'bold 16px Segoe UI, sans-serif';
  let y = top;
  for (const n of andrade) {
    const a = fore[n], b = efter[n], ma = matt(a), mb = matt(b);
    x.fillText(`${n}: före ${Math.round(a.x)},${Math.round(a.y)},${a.s} (arm ${Math.round(100 * ma.arm)} %, kropp ${Math.round(100 * ma.kropp)} %)  ->  efter ${Math.round(b.x)},${Math.round(b.y)},${b.s} (arm ${Math.round(100 * mb.arm)} %, kropp ${Math.round(100 * mb.kropp)} %)`, g, y + 20);
    // samma utsnitt före/efter vid små flyttar, annars var sitt
    const r = Math.max(a.s, b.s) * 440, langt = Math.hypot(a.x - b.x, a.y - b.y) > r / 4;
    const ruta = k => [k.x + 10 * Math.max(a.s, b.s) - r / 2, k.y - 130 * Math.max(a.s, b.s) - r / 2, r, r];
    const mitt = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    const boxF = ruta(langt ? a : mitt), boxE = ruta(langt ? b : mitt);
    [sF, vF, sE, vE].forEach((im, i) => x.drawImage(im, ...(i < 2 ? boxF : boxE), g + i * (Z + g), y + rad, Z, Z));
    y += rad + Z + g;
  }
  x.fillText('Efter (stilla):', g, y + 20);
  x.drawImage(sE, g, y + rad, helW, helH);
  return c.toDataURL('image/png');
};
"""


def spara(url, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(base64.b64decode(url.split(',', 1)[1]))


def main():
    a = sys.argv[1:]
    forslag = '--forslag' in a
    global FLYTT
    if '--langt' in a:
        FLYTT = 0.6
    arkfil = a[a.index('--ark') + 1] if '--ark' in a else None
    nr = {int(v) for v in a if v.isdigit()}
    andringar = json.load(open(arkfil, encoding='utf-8')) if arkfil else {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        sida = b.new_page()
        sida.set_content('<html><body></body></html>')
        sida.add_script_tag(content=JS)
        t = open(os.path.join(P, 'bilder.js'), encoding='utf-8').read()
        alla, aktiva = sida.evaluate('t => new Function(t + "; return [ALLA_BILDER, AKTIVA];")()', t)
        ut = {}
        forslagen = {}
        for bild in alla:
            if bild['nr'] not in aktiva or (nr and bild['nr'] not in nr):
                continue
            if arkfil and str(bild['nr']) not in andringar:
                continue
            fil = bild['fil']
            sida.evaluate('([s, j]) => forbered(s, j)', [
                'data:image/svg+xml;base64,' + b64(os.path.join(P, 'bilder', 'farg', fil + '.svg')),
                'data:image/jpeg;base64,' + b64(os.path.join(P, 'bilder', 'farg', fil + '.jpg'))])
            fore = {n: bild[n] for n in ('keiws', 'gron', 'rod') if bild.get(n)}
            if arkfil:
                efter = dict(fore)
                for n, v in andringar[str(bild['nr'])].items():
                    efter[n] = dict(fore[n], **v)
                url = sida.evaluate('([f, e, t]) => ark(f, e, t)', [fore, efter, '%s (nr %d)' % (bild['namn'], bild['nr'])])
                spara(url, os.path.join(UT, '%03d-%s.png' % (bild['nr'], fil)))
                for n in andringar[str(bild['nr'])]:
                    m = sida.evaluate('k => matt(k)', efter[n])
                    print('ark %3d %-22s %-5s (%4d, %3d, %.3f)  arm %3.0f %%  kropp %3.0f %%' % (
                        bild['nr'], fil, n, efter[n]['x'], efter[n]['y'], efter[n]['s'],
                        100 * m['arm'], 100 * m['kropp']), flush=True)
                continue
            for n, k in fore.items():
                m = sida.evaluate('k => matt(k)', k)
                rad = '%3d %-22s %-5s (%4d, %3d, %.2f)  arm %3.0f %%  kropp %3.0f %%' % (
                    bild['nr'], fil, n, k['x'], k['y'], k['s'], 100 * m['arm'], 100 * m['kropp'])
                if m['arm'] < ARM_MIN:
                    rad += '  KLIPPS'
                    if forslag:
                        bast = sida.evaluate('([k, a, f, l]) => sok(k, a, f, l)', [k, ARM_MIN, KRYMP_MAX, FLYTT])
                        if bast:
                            k2, m2 = bast['k'], bast['m']
                            rad += '  -> (%d, %d, %.3f) arm %.0f %%, kropp %.0f %%' % (k2['x'], k2['y'], k2['s'], 100 * m2['arm'], 100 * m2['kropp'])
                            forslagen.setdefault(str(bild['nr']), {})[n] = {'x': k2['x'], 'y': k2['y'], 's': k2['s']}
                        else:
                            rad += '  -> ny plats'
                ut.setdefault(bild['nr'], []).append(rad)
                print(rad, flush=True)
        b.close()
        if forslag:
            p = os.path.join(UT, 'forslag-langt.json' if FLYTT > 0.15 else 'forslag.json')
            os.makedirs(UT, exist_ok=True)
            json.dump(forslagen, open(p, 'w', encoding='utf-8'), indent=1)
            print('förslag i', p)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
