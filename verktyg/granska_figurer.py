"""Granskningsark för Pensla: native-vektorbilder och webbens bilder.

python verktyg/granska_figurer.py native [MAPP [PREFIX]]
                                     -> granskning/granskare/PREFIXnative-NAMN.png
                                        (MAPP: vektorbilderna, förval pensla-native)
python verktyg/granska_figurer.py webb [NR...]      -> granskning/granskare/webb/NR-NAMN.png
python verktyg/granska_figurer.py forslag FIL.json  -> ark med föreslagna platser (native/webb)

Webbarket: svartvitt | färglagd med figurerna maskade som i appen | original,
och hur stor del av varje figur som syns (fötterna ska vara skymda, så runt
80–95 %; 96–100 % betyder ofta att saken framför hänger ihop med ytan bakom).
"""
import base64, json, os, re, sys
from playwright.sync_api import sync_playwright

KW = r'C:\Dropbox\Isak\Program\AI\Claude\keIWs'
P = os.path.join(KW, 'Pensla')
NATIVE = os.path.join(KW, 'pensla-native', 'app', 'src', 'main', 'assets', 'bilder')
UT = os.path.join(P, 'granskning', 'granskare')

def b64(p):
    return base64.b64encode(open(p, 'rb').read()).decode()

JS_FELLES = open(os.path.join(P, 'keiws.js'), encoding='utf-8').read() + r"""
window.KEIWS = KEIWS;
window.FARG = {
  keiws: KEIWS.farger,
  gron: { bla: '#50c499', ljus: '#64d2aa', oga: '#101628' },
  rod: { bla: '#d66d61', ljus: '#e38277', oga: '#101628' },
};
window.NFARG = {  // native: BLA, MELLAN, MORK, LJUS, OGA
  keiws: KEIWS.farger,
  gron: { bla:'#50c499', mellan:'#50c499', mork:'#50c499', ljus:'#64d2aa', oga:'#101628' },
  rod: { bla:'#d66d61', mellan:'#d66d61', mork:'#d66d61', ljus:'#e38277', oga:'#101628' },
};
window.ritaFig = (ctx, x, y, s, farger) => {
  const X = v => Math.round(x + (v - 80) * s), Y = v => Math.round(y + (v - 204) * s);
  KEIWS.stilla.forEach(([x0, y0, x1, y1, f]) => {
    ctx.fillStyle = farger[f] || farger.bla;
    ctx.fillRect(X(x0), Y(y0), X(x1) - X(x0), Y(y1) - Y(y0));
  });
};
window.etikett = (ctx, txt, x, y) => {
  ctx.font = 'bold 26px Segoe UI, sans-serif';
  const w = ctx.measureText(txt).width + 10;
  ctx.fillStyle = 'rgba(255,255,255,0.9)'; ctx.fillRect(x, y, w, 32);
  ctx.strokeStyle = '#000'; ctx.lineWidth = 2; ctx.strokeRect(x, y, w, 32);
  ctx.fillStyle = '#000'; ctx.fillText(txt, x + 5, y + 25);
};
window.ladda = src => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = src; });
// Tre delar bredvid varandra + rubrik
window.ark = (delar, rubriker, titel) => {
  const W = delar[0].width, H = delar[0].height, g = 20, top = 50;
  const c = document.createElement('canvas');
  c.width = W * delar.length + g * (delar.length + 1); c.height = H + top + g;
  const x = c.getContext('2d');
  x.fillStyle = '#ddd'; x.fillRect(0, 0, c.width, c.height);
  x.font = 'bold 30px Segoe UI, sans-serif'; x.fillStyle = '#000';
  delar.forEach((d, i) => {
    x.drawImage(d, g + i * (W + g), top);
    x.fillText(rubriker[i], g + i * (W + g), 36);
  });
  x.fillText(titel, c.width - x.measureText(titel).width - g, 36);
  return c.toDataURL('image/png');
};
"""

JS_NATIVE = r"""
async ([data, jpg, figurer, titel]) => {
  const W = data.b, H = data.h;
  const mk = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; };
  const linje = new Path2D(data.linje.d);
  // svartvitt
  const sv = mk(), s = sv.getContext('2d');
  s.fillStyle = '#fff'; s.fillRect(0, 0, W, H);
  s.fillStyle = data.linje.f; s.fill(linje, 'evenodd');
  // färglagd med figurer
  const fl = mk(), f = fl.getContext('2d');
  f.fillStyle = '#fff'; f.fillRect(0, 0, W, H);
  for (const y of data.ytor) {
    const p = new Path2D(y.d);
    if (typeof y.f === 'string') f.fillStyle = y.f;
    else { const gr = f.createLinearGradient(...y.g); gr.addColorStop(0, y.f[0]); gr.addColorStop(1, y.f[1]); f.fillStyle = gr; }
    f.fill(p, 'evenodd');
  }
  const fig = figurer || data.figurer || {};
  for (const n of ['keiws', 'gron', 'rod']) {
    const k = fig[n]; if (!k) continue;
    f.save(); f.beginPath(); f.rect(k.x - 200 * k.s, k.y - 400 * k.s, 450 * k.s, 400 * k.s); f.clip();
    if (k.klipp && !figurer) f.clip(new Path2D(k.klipp), 'evenodd');  // som PenslaVy (native-v3)
    ritaFig(f, k.x, k.y, k.s, NFARG[n]); f.restore();
  }
  f.fillStyle = data.linje.f; f.fill(linje, 'evenodd');
  // Variant med ytmask (som webben): figuren bara i ytan där kroppens mitt är
  let mk2 = null;
  if (figurer) {
    mk2 = mk(); const m = mk2.getContext('2d');
    const banor = data.ytor.map(y => new Path2D(y.d));
    for (let i = 0; i < data.ytor.length; i++) { const y = data.ytor[i];
      if (typeof y.f === 'string') m.fillStyle = y.f;
      else { const gr = m.createLinearGradient(...y.g); gr.addColorStop(0, y.f[0]); gr.addColorStop(1, y.f[1]); m.fillStyle = gr; }
      m.fill(banor[i], 'evenodd'); }
    for (const n of ['keiws', 'gron', 'rod']) {
      const k = fig[n]; if (!k) continue;
      const px = k.x, py = k.y - 124 * k.s; let hit = -1;
      for (let i = 0; i < banor.length; i++) if (m.isPointInPath(banor[i], px, py, 'evenodd')) hit = i;
      m.save(); if (hit >= 0) m.clip(banor[hit], 'evenodd'); ritaFig(m, k.x, k.y, k.s, NFARG[n]); m.restore();
    }
    m.fillStyle = data.linje.f; m.fill(linje, 'evenodd');
    for (const n of ['keiws', 'gron', 'rod']) { const k = fig[n]; if (k) etikett(m, n + ' ' + Math.round(k.x) + ',' + Math.round(k.y) + ',' + k.s, k.x + 70 * k.s, k.y - 250 * k.s - 34); }
  }
  for (const n of ['keiws', 'gron', 'rod']) {
    const k = fig[n]; if (!k) continue;
    if (figurer) etikett(f, n + ' ' + Math.round(k.x) + ',' + Math.round(k.y) + ',' + k.s, k.x + 70 * k.s, k.y - 250 * k.s - 34);
  }
  const org = await ladda(jpg);
  const o = mk();
  if (data.beskar) {  // beskuren färgbild (vektorbild.py BESKAR): x0..x1 vid 900 px höjd
    const k = org.height / H, [x0, x1] = data.beskar;
    o.getContext('2d').drawImage(org, x0 * k, 0, (x1 - x0) * k, org.height, 0, 0, W, H);
  } else o.getContext('2d').drawImage(org, 0, 0, W, H);
  if (figurer) return ark([fl, mk2, o], ['Förslag, så som native ritar i dag', 'Förslag med ytmask (som webben)', 'Original'], titel);
  return ark([sv, fl, o], ['Svartvitt (native)', 'Färglagd + figurer (native)', 'Original'], titel);
}
"""

JS_WEBB = r"""
async ([svg, jpg, bild, figurer, titel]) => {
  const org = await ladda(jpg);
  const H = 900, W = Math.round(H * org.width / org.height);
  const mk = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; };
  const sv = await ladda(svg);
  const lc = mk(), l = lc.getContext('2d'); l.drawImage(sv, 0, 0, W, H);
  const alfa = l.getImageData(0, 0, W, H).data;
  // ytor som i labelRegions (4-grannar, alfa < 200)
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
  const svc = mk(), s = svc.getContext('2d'); s.fillStyle = '#fff'; s.fillRect(0, 0, W, H); s.drawImage(lc, 0, 0);
  const fl = mk(), f = fl.getContext('2d'); f.drawImage(org, 0, 0, W, H);
  const fig = figurer || bild;
  const info = {};
  for (const n of ['keiws', 'gron', 'rod']) {
    const k = fig[n]; if (!k) continue;
    const ytor = k.ytor || [[k.x, k.y - 124 * k.s]];
    const ok = new Set(ytor.map(([px, py]) => lab[Math.round(py) * W + Math.round(px)]).filter(v => v > 0));
    const t = mk(), tc = t.getContext('2d'); ritaFig(tc, k.x, k.y, k.s, FARG[n]);
    const im = tc.getImageData(0, 0, W, H); const d = im.data;
    let syns = 0, tot = 0;
    for (let i = 0; i < W * H; i++) if (d[i * 4 + 3]) { tot++; if (ok.has(lab[i])) syns++; else d[i * 4 + 3] = 0; }
    tc.putImageData(im, 0, 0); f.drawImage(t, 0, 0);
    info[n] = Math.round(100 * syns / Math.max(1, tot));
  }
  f.drawImage(lc, 0, 0);
  for (const n of ['keiws', 'gron', 'rod']) {
    const k = fig[n]; if (!k) continue;
    if (figurer) etikett(f, n + ' ' + Math.round(k.x) + ',' + Math.round(k.y) + ',' + k.s, k.x + 70 * k.s, k.y - 250 * k.s - 34);
  }
  const o = mk(); o.getContext('2d').drawImage(org, 0, 0, W, H);
  const delar = figurer ? [fl, o] : [svc, fl, o];
  const rub = figurer ? ['FÖRSLAG (webb, maskad)', 'Original'] : ['Svartvitt (webb)', 'Färglagd + figurer (webb, maskad)', 'Original'];
  return [ark(delar, rub, titel), info];
}
"""


def spara(url, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(base64.b64decode(url.split(',', 1)[1]))


def webbilder(sida):
    t = open(os.path.join(P, 'bilder.js'), encoding='utf-8').read()
    return sida.evaluate('t => new Function(t + "; return [ALLA_BILDER, AKTIVA];")()', t)


def main():
    arg = sys.argv[1:]
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        sida = b.new_page()
        sida.set_content('<html><body></body></html>')
        sida.add_script_tag(content=JS_FELLES)
        if arg[0] == 'native':
            mapp = arg[1] if len(arg) > 1 else NATIVE
            prefix = arg[2] if len(arg) > 2 else ''
            for fn in sorted(f for f in os.listdir(mapp) if f.endswith('.json')):
                data = json.load(open(os.path.join(mapp, fn), encoding='utf-8'))
                jpg = 'data:image/jpeg;base64,' + b64(os.path.join(P, 'bilder', 'farg', data['fil'] + '.jpg'))
                url = sida.evaluate(JS_NATIVE, [data, jpg, None, '%s (nr %d)' % (data['namn'], data['nr'])])
                spara(url, os.path.join(UT, prefix + 'native-%s.png' % data['fil']))
                print(fn, {k: (v['x'], v['y'], v['s'], 'klipp' in v) for k, v in data['figurer'].items()})
        elif arg[0] == 'webb':
            alla, aktiva = webbilder(sida)
            nr = {int(a) for a in arg[1:]}
            for bild in alla:
                if bild['nr'] not in aktiva or (nr and bild['nr'] not in nr):
                    continue
                fil = bild['fil']
                svg = 'data:image/svg+xml;base64,' + b64(os.path.join(P, 'bilder', 'farg', fil + '.svg'))
                jpg = 'data:image/jpeg;base64,' + b64(os.path.join(P, 'bilder', 'farg', fil + '.jpg'))
                url, info = sida.evaluate(JS_WEBB, [svg, jpg, bild, None, '%s (nr %d)' % (bild['namn'], bild['nr'])])
                spara(url, os.path.join(UT, 'webb', '%03d-%s.png' % (bild['nr'], fil)))
                print(bild['nr'], fil, 'synligt %:', info, flush=True)
        elif arg[0] == 'forslag':
            fs = json.load(open(arg[1], encoding='utf-8'))
            for nyckel, fig in fs.get('native', {}).items():
                data = json.load(open(os.path.join(NATIVE, nyckel + '.json'), encoding='utf-8'))
                jpg = 'data:image/jpeg;base64,' + b64(os.path.join(P, 'bilder', 'farg', data['fil'] + '.jpg'))
                url = sida.evaluate(JS_NATIVE, [data, jpg, fig, 'Förslag: %s' % data['namn']])
                spara(url, os.path.join(UT, 'forslag-native-%s.png' % nyckel))
            alla, aktiva = webbilder(sida)
            per = {str(x['nr']): x for x in alla}
            for nr, fig in fs.get('webb', {}).items():
                bild = per[nr]
                full = {n: bild[n] for n in ('keiws', 'gron', 'rod') if bild.get(n)}
                full.update(fig)
                fil = bild['fil']
                svg = 'data:image/svg+xml;base64,' + b64(os.path.join(P, 'bilder', 'farg', fil + '.svg'))
                jpg = 'data:image/jpeg;base64,' + b64(os.path.join(P, 'bilder', 'farg', fil + '.jpg'))
                url, info = sida.evaluate(JS_WEBB, [svg, jpg, bild, full, 'Förslag: %s (nr %s)' % (bild['namn'], nr)])
                spara(url, os.path.join(UT, 'webb', 'forslag-%03d-%s.png' % (int(nr), fil)))
                print(nr, fil, info)
        b.close()


main()
