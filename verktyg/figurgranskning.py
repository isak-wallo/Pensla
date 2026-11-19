"""Granskningsark för alla figurer i de aktiva bilderna, stilla och vinkande.

Ritar varje aktiv bild färdigmålad med keIWs och kompisarna, maskade till
sina ytor som i appen (samma ytnumrering och mask som vinkarm.py, som
labelRegions/prepKeiws i app.js), och mäter hur stor del av kroppen och den
vinkande armen som syns.

    python verktyg/figurgranskning.py [NR...]                 # alla aktiva om inga NR
    python verktyg/figurgranskning.py --forslag FIL.json [NR...]
        # FIL.json: {"NR": {"keiws": {"x", "y", "s", "ytor"?}, ...}} ritas i stället
        # för platserna i bilder.js (bilder.js ändras inte). Utan "ytor" tas
        # punkten (x, y − 124 s) som i gomstallen.py.
    --ut MAPP     var arken hamnar (förval granskning/figurgranskning/, inte i git)
    --par         två bilder per ark (färre filer att bläddra i)
    --kvalitet Q  JPEG-kvalitet (förval 70)

Varje ark: hela bilden med figurerna stilla (vänster) och vinkande (mitten),
och till höger en rad per figur: utsnitt stilla | utsnitt vinkande med
andelen synlig kropp, arm och
fötter (fötter nära 100 % = figuren står fritt, kan se ut att sväva). Mätvärdena skrivs också till matt.json i
samma mapp. Chromium: sätt PENSLA_CHROME om Playwrights egen inte hittas.
"""
import base64, glob, io, json, os, sys
from playwright.sync_api import sync_playwright
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vinkarm import JS, P, b64   # samma mask och mätning som vinkarm.py

JS_ARK = r"""
// Fötterna = stilla-klossarna under kroppen (y >= 160)
window.fot = k => syns(k, KEIWS.stilla.filter(r => r[1] >= 160));
window.helbild = (fig, rekt) => rita(fig, rekt).toDataURL('image/png');
// Utsnitt runt figuren k (stilla och vinkande), Z × Z px
window.utsnitt = (fig, n, Z) => {
  const k = fig[n], r = Math.max(k.s * 600, 150);
  const box = [k.x + 10 * k.s - r / 2, k.y - 120 * k.s - r / 2, r, r];
  return [KEIWS.stilla, VINKAR].map(rekt => {
    const c = document.createElement('canvas'); c.width = Z; c.height = Z;
    const x = c.getContext('2d'); x.fillStyle = '#888'; x.fillRect(0, 0, Z, Z);
    x.drawImage(rita(fig, rekt), ...box, 0, 0, Z, Z);
    return c.toDataURL('image/png');
  });
};
"""


def chromium(pw):
    exe = os.environ.get('PENSLA_CHROME')
    if not exe:
        for m in sorted(glob.glob('/opt/pw-browsers/chromium-*/chrome-linux64/chrome')):
            exe = m
    try:
        return pw.chromium.launch()
    except Exception:
        return pw.chromium.launch(executable_path=exe)


def bild_av(url):
    return Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGB')


def main():
    a = sys.argv[1:]
    def flagga(namn, forval=None):
        if namn in a:
            i = a.index(namn); v = a[i + 1]; del a[i:i + 2]; return v
        return forval
    fsfil = flagga('--forslag')
    ut = flagga('--ut', os.path.join(P, 'granskning', 'figurgranskning'))
    kval = int(flagga('--kvalitet', '70'))
    par = '--par' in a
    nr = {int(v) for v in a if v.isdigit()}
    forslag = json.load(open(fsfil, encoding='utf-8')) if fsfil else {}
    if forslag and not nr:
        nr = {int(k) for k in forslag}
    os.makedirs(ut, exist_ok=True)
    from PIL import ImageDraw, ImageFont
    try:
        font = ImageFont.truetype('DejaVuSans-Bold.ttf', 15)
        stor = ImageFont.truetype('DejaVuSans-Bold.ttf', 20)
    except OSError:
        font = stor = ImageFont.load_default()
    matt_ut = {}
    ark = []
    with sync_playwright() as pw:
        b = chromium(pw)
        sida = b.new_page()
        sida.set_content('<html><body></body></html>')
        sida.add_script_tag(content=JS + JS_ARK)
        t = open(os.path.join(P, 'bilder.js'), encoding='utf-8').read()
        alla, aktiva = sida.evaluate('t => new Function(t + "; return [ALLA_BILDER, AKTIVA];")()', t)
        for bild in alla:
            if bild['nr'] not in aktiva or (nr and bild['nr'] not in nr):
                continue
            fil = bild['fil']
            sida.evaluate('([s, j]) => forbered(s, j)', [
                'data:image/svg+xml;base64,' + b64(os.path.join(P, 'bilder', 'farg', fil + '.svg')),
                'data:image/jpeg;base64,' + b64(os.path.join(P, 'bilder', 'farg', fil + '.jpg'))])
            fig = {n: dict(bild[n]) for n in ('keiws', 'gron', 'rod') if bild.get(n)}
            for n, v in forslag.get(str(bild['nr']), {}).items():
                ny = dict(fig.get(n, {}), **v)
                if 'ytor' not in v:
                    ny['ytor'] = [[ny['x'], round(ny['y'] - 124 * ny['s'])]]
                fig[n] = ny
            HB = 560
            stilla = bild_av(sida.evaluate('f => helbild(f, KEIWS.stilla)', fig))
            vinkar = bild_av(sida.evaluate('f => helbild(f, VINKAR)', fig))
            hh = round(HB * stilla.height / stilla.width)
            Z = 200
            rader = []
            for n in fig:
                m = sida.evaluate('k => Object.assign(matt(k), { fot: fot(k) })', fig[n])
                s_, v_ = sida.evaluate('([f, n, Z]) => utsnitt(f, n, Z)', [fig, n, Z])
                rader.append((n, m, bild_av(s_), bild_av(v_)))
                k = fig[n]
                matt_ut.setdefault(str(bild['nr']), {})[n] = {
                    'x': k['x'], 'y': k['y'], 's': k['s'],
                    'kropp': round(100 * m['kropp']), 'arm': round(100 * m['arm']), 'fot': round(100 * m['fot'])}
                print('%3d %-22s %-5s (%4d, %3d, %.3f)  kropp %3.0f %%  arm %3.0f %%  fot %3.0f %%' % (
                    bild['nr'], fil, n, k['x'], k['y'], k['s'], 100 * m['kropp'], 100 * m['arm'], 100 * m['fot']), flush=True)
            top = 30
            hojd = max(hh, len(rader) * (Z + 22)) + top + 8
            c = Image.new('RGB', (2 * HB + 2 * Z + 40, hojd), (221, 221, 221))
            d = ImageDraw.Draw(c)
            titel = '%s (nr %d)%s' % (bild['namn'], bild['nr'], '  FÖRSLAG' if forslag else '')
            d.text((8, 4), titel, fill=(0, 0, 0), font=stor)
            c.paste(stilla.resize((HB, hh), Image.LANCZOS), (8, top))
            c.paste(vinkar.resize((HB, hh), Image.LANCZOS), (HB + 16, top))
            x0 = 2 * HB + 24
            for i, (n, m, im_s, im_v) in enumerate(rader):
                y = top + i * (Z + 22)
                k = fig[n]
                d.text((x0, y), '%s %d,%d,%g  kr %d%% arm %d%% fot %d%%' % (
                    n, k['x'], k['y'], k['s'], round(100 * m['kropp']), round(100 * m['arm']), round(100 * m['fot'])),
                    fill=(170, 0, 0) if m['arm'] < 0.9 else (0, 0, 0), font=font)
                c.paste(im_s, (x0, y + 18))
                c.paste(im_v, (x0 + Z + 8, y + 18))
            ark.append((bild['nr'], fil, c))
        b.close()
    namn = 'forslag-' if forslag else ''
    if par:
        for i in range(0, len(ark), 2):
            delar = ark[i:i + 2]
            W = max(x[2].width for x in delar); H = sum(x[2].height for x in delar) + 6 * (len(delar) - 1)
            c = Image.new('RGB', (W, H), (90, 90, 90)); y = 0
            for _, _, im in delar:
                c.paste(im, (0, y)); y += im.height + 6
            c.save(os.path.join(ut, '%s%03d-%03d.jpg' % (namn, delar[0][0], delar[-1][0])), quality=kval, optimize=True)
    else:
        for n, fil, im in ark:
            im.save(os.path.join(ut, '%s%03d-%s.jpg' % (namn, n, fil)), quality=kval, optimize=True)
    json.dump(matt_ut, open(os.path.join(ut, namn + 'matt.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ark i', ut)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
