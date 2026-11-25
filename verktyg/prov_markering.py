"""Prov av den hemliga markeringen i webbappen (app.js, "Hemlig markering").

Kör appen i headless Chromium (Playwright) med riktiga flerfingerhändelser
(CDP Input.dispatchTouchEvent) och kontrollerar:

  - gesten: öppnar efter 3 s (v116; 5 s förut), i olika ordning och även när den görs långsamt
    (pil, FÄRGLÄGG, den andra pilen först efter 2,5 s), och öppnar inte när
    den avbryts (2 s, 2,5 s, 2,7 s, bara pilarna, FÄRGLÄGG + en pil, lyft och åter,
    finger som glider av),
  - att ingen bild byts och inget färgläggs av gesten: bilden som visas och
    båda grannbilderna jämförs pixel för pixel med hur de såg ut före
    (0 pixlars skillnad),
  - läget: texten och knapparna ligger i panelen och inget ligger över
    bilden, i liggande och stående och på liten telefon,
  - att man kan markera i bildens överkant (draget ritas där och kommer med
    i det som skickas), och att KLAR och AVBRYT fungerar,
  - knapptryck vid släpp (v114): ◀ ▶ FÄRGLÄGG i alla sex ordningar
    (långsamt, snabbt, öppnat, avbrutet, släpp i olika ordning) ger samma
    bild och 0 pixlar; en pil ensam byter vid släpp (inte när den glider av);
    pil eller FÄRGLÄGG + en annan knapp gör ingenting; FÄRGLÄGG ensam ger
    tipset eller färglägger vid släpp; samma med mus.

    python verktyg/prov_markering.py                 # arbetskopian
    python verktyg/prov_markering.py --mapp MAPP     # en annan kopia av appen
    python verktyg/prov_markering.py --adress https://test.pensla.keiws.com/index.html
    python verktyg/prov_markering.py --bilder MAPP   # sparar skärmbilder där
    python verktyg/prov_markering.py --bara langsam  # bara fall vars namn innehåller ordet
    python verktyg/prov_markering.py --grupp tre regler   # bara knappreglerna (v114)

Inget skickas någonstans: anropen till api/markering fångas i webbläsaren
(svaret "sparad" härmas), även med --adress. Service workern är avstängd i
provet. Kräver `pip install playwright` och Playwrights Chromium.
"""
import argparse
import functools
import http.server
import json
import os
import sys
import threading
import time

from playwright.sync_api import sync_playwright

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Hjälp i sidan: spara bilden på skärmen och räkna pixlar som skiljer.
HJALP = r"""
window.__ref = {};
window.__px = () => {
    const c = document.getElementById('viewCanvas');
    return c.getContext('2d').getImageData(0, 0, c.width, c.height);
};
window.__hash = () => {
    const d = window.__px().data;
    let h = 0, linjer = 0;
    for (let i = 0; i < d.length; i += 4) {
        h = (h * 31 + d[i] * 65536 + d[i + 1] * 256 + d[i + 2]) | 0;
        if (d[i] < 90 && d[i + 1] < 90 && d[i + 2] < 90) linjer++;
    }
    return [h, linjer];
};
window.__spara = namn => { window.__ref[namn] = window.__px(); };
window.__skillnad = namn => {
    const a = window.__ref[namn], b = window.__px();
    if (!a || a.width !== b.width || a.height !== b.height) return -1;
    let n = 0;
    for (let i = 0; i < a.data.length; i += 4) {
        if (a.data[i] !== b.data[i] || a.data[i + 1] !== b.data[i + 1] || a.data[i + 2] !== b.data[i + 2]) n++;
    }
    return n;
};
// Bildens ruta på skärmen: allt i ritytan som inte är bakgrunden runt bilden.
window.__bildruta = () => {
    const c = document.getElementById('viewCanvas'), r = c.getBoundingClientRect(), im = window.__px(), d = im.data;
    let x0 = im.width, y0 = im.height, x1 = -1, y1 = -1;
    for (let y = 0; y < im.height; y++) for (let x = 0; x < im.width; x++) {
        const i = 4 * (y * im.width + x);
        if (d[i] !== 220 || d[i + 1] !== 236 || d[i + 2] !== 248) {
            if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
        }
    }
    return { left: r.left + x0, top: r.top + y0, right: r.left + x1 + 1, bottom: r.top + y1 + 1 };
};
window.__ruta = id => {
    const r = document.getElementById(id).getBoundingClientRect();
    return { left: r.left, top: r.top, right: r.right, bottom: r.bottom };
};
// Andel av sträckan x0..x1 på skärmraden y där markeringslagret är målat.
window.__markRad = (x0, x1, y) => {
    const c = document.getElementById('markCanvas'), r = c.getBoundingClientRect();
    const rad = Math.min(c.height - 1, Math.max(0, Math.round(y - r.top)));
    const a = Math.max(0, Math.round(x0 - r.left)), b = Math.min(c.width, Math.round(x1 - r.left));
    const d = c.getContext('2d').getImageData(a, rad, b - a, 1).data;
    let n = 0;
    for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
    return n / (b - a);
};
window.__markKol = (x, y0, y1) => {
    const c = document.getElementById('markCanvas'), r = c.getBoundingClientRect();
    const kol = Math.min(c.width - 1, Math.max(0, Math.round(x - r.left)));
    const a = Math.max(0, Math.round(y0 - r.top)), b = Math.min(c.height, Math.round(y1 - r.top));
    const d = c.getContext('2d').getImageData(kol, a, 1, b - a).data;
    let n = 0;
    for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
    return n / (b - a);
};
"""


class Tyst(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class Server(http.server.ThreadingHTTPServer):
    request_queue_size = 256        # webbläsaren hämtar många filer på en gång


def servera(mapp):
    srv = Server(('127.0.0.1', 0), functools.partial(Tyst, directory=mapp))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


class Fingrar:
    """Riktiga flerfingerhändelser via CDP. touchStart och touchMove tar alla
    fingrar som är nere, touchEnd bara dem som släpps."""

    def __init__(self, cdp):
        self.cdp = cdp
        self.nere = {}

    def _punkter(self, vilka):
        return [{'x': x, 'y': y, 'id': i, 'radiusX': 5, 'radiusY': 5, 'force': 1} for i, (x, y) in vilka.items()]

    def ner(self, i, x, y):
        self.nere[i] = (x, y)
        self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': self._punkter(self.nere)})

    def flytta(self, i, x, y):
        self.nere[i] = (x, y)
        self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': self._punkter(self.nere)})

    def upp(self, *vilka):
        slappta = {i: self.nere.pop(i) for i in vilka}
        self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': self._punkter(slappta)})

    def alla_upp(self):
        if self.nere:
            self.upp(*list(self.nere))


class Prov:
    def __init__(self, arg):
        self.arg = arg
        self.resultat = []      # (fall, kontroll, ok, detalj)
        self.fall = ''
        self.skickat = []

    # --- grund ---
    def kolla(self, kontroll, ok, detalj=''):
        self.resultat.append((self.fall, kontroll, bool(ok), str(detalj)))
        print('  %s %s%s' % ('ok  ' if ok else 'FEL ', kontroll, ('  [%s]' % detalj) if detalj != '' else ''), flush=True)

    def oppna(self, bredd, hojd, android=False):
        """Ny webbläsarmiljö (tomt minne), appen startad, bilderna A (visas), B (nästa) och C (föregående) sparade."""
        ua = ('Mozilla/5.0 (Linux; Android 12; Tablet) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/120.0 Safari/537.36') if android else None
        self.ctx = self.webblasare.new_context(viewport={'width': bredd, 'height': hojd}, has_touch=True,
                                               service_workers='block', user_agent=ua)
        self.skickat = []

        def fanga(route):
            self.skickat.append(route.request.post_data)
            route.fulfill(status=204, headers={'X-Pensla-Markering': 'sparad', 'Cache-Control': 'no-store'})
        self.ctx.route('**/api/markering', fanga)
        self.sida = self.ctx.new_page()
        self.sida.add_init_script(HJALP)
        self.sida.goto(self.adress)
        self.f = Fingrar(self.ctx.new_cdp_session(self.sida))
        self.sida.click('#start-btn')
        self.stilla()
        self.sida.evaluate("__spara('A')")
        self.tryck('next-btn')
        self.sida.evaluate("__spara('B')")
        self.tryck('prev-btn')
        self.tryck('prev-btn')
        self.sida.evaluate("__spara('C')")
        self.tryck('next-btn')
        s = {n: self.skillnad(n) for n in 'ABC'}
        if s['A'] != 0 or s['B'] == 0 or s['C'] == 0:
            raise RuntimeError('Bilderna gick inte att skilja åt i början: %s' % s)

    def stang(self):
        self.f.alla_upp()
        self.ctx.close()

    def stilla(self, langst=15):
        """Väntar tills bilden på skärmen är laddad och inte ändras."""
        slut = time.time() + langst
        forra = None
        while time.time() < slut:
            self.sida.wait_for_timeout(250)
            h = self.sida.evaluate('__hash()')
            if h == forra and h[1] > 500:
                return
            forra = h
        raise RuntimeError('Bilden blev aldrig stilla')

    def mitt(self, id_):
        r = self.sida.evaluate('__ruta(%s)' % json.dumps(id_))
        return (r['left'] + r['right']) / 2, (r['top'] + r['bottom']) / 2

    def tryck(self, id_, ms=80, vanta=True):
        """Ett tryck med ett finger. På en pil: väntar tills bilden har bytts och är stilla."""
        pil = vanta and id_ in ('prev-btn', 'next-btn')
        fore = self.sida.evaluate('__hash()') if pil else None
        x, y = self.mitt(id_)
        self.f.ner(9, x, y)
        self.sida.wait_for_timeout(ms)
        self.f.upp(9)
        if pil:
            slut = time.time() + 15
            while self.sida.evaluate('__hash()') == fore:
                if time.time() > slut:
                    raise RuntimeError('Bilden byttes inte av %s' % id_)
                self.sida.wait_for_timeout(100)
        if vanta:
            self.stilla()

    def ner(self, finger, id_):
        x, y = self.mitt(id_)
        self.f.ner(finger, x, y)

    def vanta(self, ms):
        self.sida.wait_for_timeout(ms)

    def skillnad(self, namn):
        return self.sida.evaluate('__skillnad(%s)' % json.dumps(namn))

    def oppet(self):
        return self.sida.evaluate("!document.getElementById('mark-lage').hidden")

    def text(self, id_):
        return self.sida.evaluate("document.getElementById(%s).textContent.trim()" % json.dumps(id_))

    def bild(self, namn):
        if self.arg.bilder:
            os.makedirs(self.arg.bilder, exist_ok=True)
            self.sida.screenshot(path=os.path.join(self.arg.bilder, namn + '.png'))

    def orort(self, visas='A'):
        """Bilden som visas ska vara `visas`, och A, B och C ska alla se ut precis som före (0 pixlar)."""
        self.f.alla_upp()
        if self.oppet():
            self.tryck('mark-avbryt', vanta=False)
            self.vanta(600)
        self.vanta(1700)        # en färgläggning som ändå startat hinner synas
        self.stilla()
        s = self.skillnad(visas)
        self.kolla('bilden som visas är %s, orörd (0 pixlar)' % visas, s == 0, s)
        if s != 0:
            self.kolla('grannbilderna orörda', False, 'kunde inte jämföras: fel bild visas')
            return
        steg = {'A': [('prev-btn', 'C'), ('next-btn', 'A'), ('next-btn', 'B'), ('prev-btn', 'A')],
                'B': [('prev-btn', 'A'), ('prev-btn', 'C'), ('next-btn', 'A'), ('next-btn', 'B')],
                'C': [('next-btn', 'A'), ('next-btn', 'B'), ('prev-btn', 'A'), ('prev-btn', 'C')]}[visas]
        for knapp, namn in steg:
            self.tryck(knapp)
            self.vanta(300)
            self.stilla()
            if namn != visas or (knapp, namn) == steg[-1]:
                s = self.skillnad(namn)
                self.kolla('bild %s orörd (0 pixlars skillnad)' % namn, s == 0, s)

    # --- gesten ---
    def fall_(self, namn, gor, bredd, hojd, android=False):
        """Kör ett fall i en ny webbläsarmiljö. Går något snett räknas det som ett fel och nästa fall körs."""
        self.fall = namn
        print(namn, flush=True)
        self.ctx = None
        try:
            self.oppna(bredd, hojd, android)
            gor()
        except Exception as e:
            self.kolla('fallet gick att köra', False, str(e).splitlines()[0])
        finally:
            if self.ctx:
                try:
                    self.stang()
                except Exception:
                    pass

    def gest(self, namn, steg, oppnar, visas='A', bredd=1280, hojd=800, efter=None, farglagd=False):
        """steg: lista av ('ner', finger, knapp) | ('upp', finger...) | ('vanta', ms) | ('glid', finger, dx, dy)
        | ('oppet', väntat, text) | ('ner3',) | ('bild', namn, text) | ('farglagd', namn, text) | ('stilla',)
        | ('klass', klass, väntat, text) | ('text', id, väntat, text).
        farglagd: bilden blir färglagd i fallet; BÖRJA OM tömmer den innan bilderna jämförs."""
        self.fall_(namn, lambda: self.gest_(steg, oppnar, visas, efter, farglagd), bredd, hojd)

    def gest_(self, steg, oppnar, visas, efter, farglagd=False):
        if True:
            for s in steg:
                if s[0] == 'ner':
                    self.ner(s[1], s[2])
                elif s[0] == 'upp':
                    self.f.upp(*s[1:])
                elif s[0] == 'vanta':
                    self.vanta(s[1])
                elif s[0] == 'glid':
                    x, y = self.f.nere[s[1]]
                    for k in range(1, 6):
                        self.f.flytta(s[1], x + s[2] * k / 5, y + s[3] * k / 5)
                        self.vanta(30)
                elif s[0] == 'oppet':
                    self.kolla(s[2], self.oppet() == s[1], self.oppet())
                elif s[0] == 'ner3':      # ◀ ▶ FÄRGLÄGG i samma touchStart
                    for i, k in ((1, 'prev-btn'), (2, 'next-btn'), (3, 'fill-btn')):
                        self.f.nere[i] = self.mitt(k)
                    self.f.ner(3, *self.f.nere[3])
                elif s[0] == 'bild':
                    n = self.skillnad(s[1])
                    self.kolla(s[2], n == 0, n)
                elif s[0] == 'farglagd':
                    n = self.skillnad(s[1])
                    self.kolla(s[2], n > 50000, n)
                elif s[0] == 'stilla':
                    self.stilla()
                elif s[0] == 'klass':     # ('klass', klass, väntat, text[, knapp]) – förvald knapp FÄRGLÄGG
                    knapp = s[4] if len(s) > 4 else 'fill-btn'
                    har = self.sida.evaluate("document.getElementById(%s).classList.contains(%s)"
                                             % (json.dumps(knapp), json.dumps(s[1])))
                    self.kolla(s[3], har == s[2], har)
                elif s[0] == 'punkt':     # ('punkt', finger, x, y): ett finger ner på en skärmpunkt
                    self.f.ner(s[1], s[2], s[3])
                elif s[0] == 'text':
                    self.kolla(s[3], self.text(s[1]) == s[2], self.text(s[1]))
            self.kolla('läget öppnat' if oppnar else 'läget inte öppnat', self.oppet() == oppnar)
            if efter:
                efter()
            if farglagd:
                self.f.alla_upp()
                if self.oppet():
                    self.tryck('mark-avbryt', vanta=False)
                    self.vanta(600)
                self.ner(4, 'restart-btn')
                self.vanta(1200)
                self.f.upp(4)
                self.vanta(4500)
                self.stilla()
            self.orort(visas)

    def alla_gester(self):
        P, N, F, B = 'prev-btn', 'next-btn', 'fill-btn', 'restart-btn'
        g = self.gest
        # Öppnar
        g('gest: ◀ ▶ FÄRGLÄGG snabbt, 3,4 s',
          [('ner', 1, P), ('vanta', 150), ('ner', 2, N), ('vanta', 150), ('ner', 3, F), ('vanta', 2500),
           ('oppet', False, 'inte öppet efter 2,5 s'), ('vanta', 900)], True)
        g('gest: FÄRGLÄGG ▶ ◀ snabbt, 3,4 s',
          [('ner', 3, F), ('vanta', 150), ('ner', 2, N), ('vanta', 150), ('ner', 1, P), ('vanta', 3400)], True)
        # Gränsen (v116: GEST_MS = 3 s)
        g('gränsen: alla tre 2,7 s och släpp (öppnar inte)',
          [('ner', 1, P), ('vanta', 100), ('ner', 2, N), ('vanta', 100), ('ner', 3, F), ('vanta', 2500),
           ('oppet', False, 'inte öppet efter 2,5 s'), ('vanta', 200), ('upp', 1, 2, 3), ('vanta', 2000)], False)
        g('gränsen: öppnar mellan 2,8 och 3,2 s',
          [('ner', 1, P), ('vanta', 100), ('ner', 2, N), ('vanta', 100), ('ner', 3, F), ('vanta', 2800),
           ('oppet', False, 'inte öppet efter 2,8 s'), ('vanta', 400), ('oppet', True, 'öppet efter 3,2 s')], True)
        g('gest långsam: ◀, FÄRGLÄGG, ▶ först efter 2,5 s',
          [('ner', 1, P), ('vanta', 300), ('ner', 3, F), ('vanta', 2500), ('ner', 2, N), ('vanta', 3400)], True,
          efter=lambda: self.bild('gest-langsam-laget-oppet'))
        g('gest långsam: ▶, FÄRGLÄGG, ◀ först efter 2,5 s',
          [('ner', 2, N), ('vanta', 300), ('ner', 3, F), ('vanta', 2500), ('ner', 1, P), ('vanta', 3400)], True)
        g('gest långsam, stående: ◀, FÄRGLÄGG, ▶ först efter 2,5 s',
          [('ner', 1, P), ('vanta', 300), ('ner', 3, F), ('vanta', 2500), ('ner', 2, N), ('vanta', 3400)], True,
          bredd=800, hojd=1280)
        # Öppnar inte
        g('avbruten: alla tre i 2 s',
          [('ner', 1, P), ('vanta', 100), ('ner', 2, N), ('vanta', 100), ('ner', 3, F), ('vanta', 2000),
           ('upp', 1, 2, 3), ('vanta', 4000)], False)
        g('avbruten: alla tre i 2,5 s',
          [('ner', 1, P), ('vanta', 100), ('ner', 2, N), ('vanta', 100), ('ner', 3, F), ('vanta', 2500),
           ('upp', 1, 2, 3), ('vanta', 2000)], False)
        g('avbruten långsam: ◀ och FÄRGLÄGG i 4 s, ingen andra pil',
          [('ner', 1, P), ('vanta', 300), ('ner', 3, F), ('vanta', 4000), ('upp', 1, 3), ('vanta', 500)], False,
          efter=lambda: self.kolla('inget tips på FÄRGLÄGG', self.text('fill-btn') == 'FÄRGLÄGG',
                                              self.text('fill-btn')))
        g('avbruten långsam: ◀, FÄRGLÄGG 2,5 s, ▶, släpp efter 2 s',
          [('ner', 1, P), ('vanta', 300), ('ner', 3, F), ('vanta', 2500), ('ner', 2, N), ('vanta', 2000),
           ('upp', 1, 2, 3), ('vanta', 4000)], False)
        g('bara pilarna i 6 s',
          [('ner', 1, P), ('vanta', 150), ('ner', 2, N), ('vanta', 6000)], False)
        g('FÄRGLÄGG, sedan en pil (▶), 6 s',
          [('ner', 3, F), ('vanta', 400), ('ner', 2, N), ('vanta', 6000)], False)
        g('en pil (▶), sedan FÄRGLÄGG, 6 s',
          [('ner', 2, N), ('vanta', 400), ('ner', 3, F), ('vanta', 6000)], False)
        g('lyft FÄRGLÄGG efter 2 s och åter: tiden börjar om',
          [('ner', 1, P), ('vanta', 100), ('ner', 2, N), ('vanta', 100), ('ner', 3, F), ('vanta', 2000),
           ('upp', 3), ('vanta', 300), ('ner', 3, F), ('vanta', 2200), ('oppet', False, 'inte öppet 4,7 s efter start'),
           ('vanta', 1200)], True)
        g('lyft en pil efter 2 s och åter: tiden börjar om',
          [('ner', 1, P), ('vanta', 100), ('ner', 2, N), ('vanta', 100), ('ner', 3, F), ('vanta', 2000),
           ('upp', 2), ('vanta', 300), ('ner', 2, N), ('vanta', 2200), ('oppet', False, 'inte öppet 4,7 s efter start'),
           ('vanta', 1200)], True)
        g('lyft en pil efter 2 s, åter först efter 2,5 s',
          [('ner', 1, P), ('vanta', 100), ('ner', 2, N), ('vanta', 100), ('ner', 3, F), ('vanta', 2000),
           ('upp', 2), ('vanta', 2500), ('ner', 2, N), ('vanta', 2000), ('upp', 1, 2, 3), ('vanta', 500)], False)
        g('finger glider av ▶ efter 2 s',
          [('ner', 1, P), ('vanta', 100), ('ner', 2, N), ('vanta', 100), ('ner', 3, F), ('vanta', 2000),
           ('glid', 2, -260, 0), ('vanta', 3500)], False)
        g('finger glider av FÄRGLÄGG efter 2 s',
          [('ner', 1, P), ('vanta', 100), ('ner', 2, N), ('vanta', 100), ('ner', 3, F), ('vanta', 2000),
           ('glid', 3, -260, 0), ('vanta', 3500)], False)
        g('alla fyra knapparna i 6 s (BÖRJA OM sist)',
          [('ner', 1, P), ('vanta', 100), ('ner', 2, N), ('vanta', 100), ('ner', 3, F), ('vanta', 100),
           ('ner', 4, B), ('vanta', 500), ('upp', 4), ('vanta', 2500),
           ('oppet', False, 'inte öppet 2,5 s efter att BÖRJA OM släppts'), ('vanta', 1500)], True)

    def tre_i_alla_ordningar(self):
        """Alla sex ordningar av ◀ ▶ FÄRGLÄGG, snabbt och långsamt, öppnade och
        avbrutna, med släpp i olika ordning: alltid samma bild, och 0 pixlar
        utom när FÄRGLÄGG hålls ensam först i mer än 1,5 s (v115: då
        färgläggs bilden medan fingret ligger kvar, men pilarna byter inte)."""
        import itertools
        K = {'P': 'prev-btn', 'N': 'next-btn', 'F': 'fill-btn'}
        nr = {'P': 1, 'N': 2, 'F': 3}
        tecken = {'P': '◀', 'N': '▶', 'F': 'FÄRGLÄGG'}
        for i, ordning in enumerate(itertools.permutations('PNF')):
            namn = ' '.join(tecken[k] for k in ordning)
            # långsamt (1,7 s mellan, mer än FARGA_HOLD_MS), hålls 2,5 s, släpps i omvänd ordning
            forst = ordning[0] == 'F'
            # v117: en pil som hålls ensam 1,7 s först byter bild en gång (vid 0,7 s)
            bytt = {'P': 'C', 'N': 'B', 'F': 'A'}[ordning[0]]
            steg = []
            for k in ordning:
                steg += [('ner', nr[k], K[k]), ('vanta', 1700)]
            steg += [('vanta', 800)] + [('upp', nr[k]) for k in reversed(ordning)] + [('vanta', 600)]
            if forst:
                steg += [('stilla',), ('farglagd', 'A', 'färglagt (FÄRGLÄGG ensam 1,7 s först), samma bild')]
            else:
                steg += [('stilla',), ('bild', bytt, 'pilen ensam 1,7 s först: bytt en gång, till %s' % bytt)]
            self.gest('tre, långsam och avbruten: %s, släpp omvänt' % namn, steg, False,
                      efter=self.inget_tips, farglagd=forst, visas=bytt)
            # snabbt, släpps ett i taget i samma ordning med 0,8 s mellan (den sista hålls ensam en stund)
            steg = []
            for k in ordning:
                steg += [('ner', nr[k], K[k]), ('vanta', 60)]
            steg += [('vanta', 2000)]
            for k in ordning:
                steg += [('upp', nr[k]), ('vanta', 800)]
            self.gest('tre, snabb och avbruten: %s, släpp ett i taget' % namn, steg, False,
                      efter=self.inget_tips)
            # öppnar (varannan långsam), och den sista knappen släpps först 2 s efter de andra.
            # Långsam med en pil först: andra fingret efter 0,5 s (före PIL_HALL_MS), sedan 1,7 s.
            steg = []
            for j, k in enumerate(ordning):
                ms = (500 if j == 0 and not forst else 1700) if i % 2 else 300
                steg += [('ner', nr[k], K[k]), ('vanta', ms)]
            steg += [('vanta', 3400), ('oppet', True, 'läget öppet'), ('upp', nr[ordning[0]], nr[ordning[1]]),
                     ('vanta', 2000), ('upp', nr[ordning[2]]), ('vanta', 600)]
            farg = forst and i % 2 == 1
            if farg:
                steg += [('farglagd', 'A', 'färglagt (FÄRGLÄGG ensam 1,7 s först), samma bild')]
            self.gest('tre, öppnar: %s (%s)' % (namn, 'långsam' if i % 2 else 'snabb'), steg, True,
                      efter=self.inget_tips, farglagd=farg)
        P, N, F = K['P'], K['N'], K['F']
        self.gest('FÄRGLÄGG ensam 2 s först (färglagt), sedan ◀ och ▶: inget byte',
                  [('ner', 3, F), ('vanta', 2000), ('farglagd', 'A', 'färglagt medan FÄRGLÄGG hålls'),
                   ('ner', 1, P), ('vanta', 200), ('ner', 2, N), ('vanta', 1000),
                   ('upp', 3), ('vanta', 300), ('upp', 1, 2), ('vanta', 600), ('stilla',),
                   ('farglagd', 'A', 'samma bild, färglagd')], False, efter=self.inget_tips, farglagd=True)
        self.gest('FÄRGLÄGG ensam 2 s först (färglagt), sedan hela gesten (öppnar)',
                  [('ner', 3, F), ('vanta', 2000), ('ner', 1, P), ('vanta', 200), ('ner', 2, N), ('vanta', 3400)],
                  True, efter=self.inget_tips, farglagd=True)
        self.gest('FÄRGLÄGG 1 s, sedan ◀ och ▶ (före 1,5 s), släpp efter 2 s: 0 pixlar',
                  [('ner', 3, F), ('vanta', 1000), ('ner', 1, P), ('vanta', 200), ('ner', 2, N), ('vanta', 2000),
                   ('upp', 3), ('vanta', 300), ('upp', 1, 2), ('vanta', 600)], False, efter=self.inget_tips)
        self.gest('alla tre ner i samma ögonblick, 1 s, upp i samma ögonblick',
                  [('ner3',), ('vanta', 1000), ('upp', 1, 2, 3), ('vanta', 600)], False, efter=self.inget_tips)

    def inget_tips(self):
        self.kolla('inget tips på FÄRGLÄGG', self.text('fill-btn') == 'FÄRGLÄGG', self.text('fill-btn'))

    def regler(self):
        """Reglerna för pilarna och FÄRGLÄGG var för sig (v114)."""
        P, N, F, B = 'prev-btn', 'next-btn', 'fill-btn', 'restart-btn'
        g = self.gest
        # Pil ensam: kort tryck byter vid släpp; hålls den 0,7 s byts bilden direkt (v117, se pilhall)
        g('pil ensam: ▶ hålls 3 s, bytt en gång medan den hålls, inget mer vid släpp',
          [('ner', 2, N), ('vanta', 3000), ('bild', 'B', 'nästa bild medan ▶ hålls'), ('upp', 2),
           ('vanta', 400), ('stilla',), ('bild', 'B', 'samma bild efter släppet')], False, visas='B')
        g('pil ensam: ◀ kort tryck, byter vid släpp',
          [('ner', 1, P), ('vanta', 120), ('bild', 'A', 'samma bild medan ◀ hålls'), ('upp', 1), ('vanta', 400),
           ('stilla',)], False, visas='C')
        g('pil ensam: ▶ glider av knappen och släpps, inget byte',
          [('ner', 2, N), ('vanta', 300), ('glid', 2, -260, 0), ('upp', 2), ('vanta', 600)], False)
        g('pil ensam: två fingrar på ▶, ett steg när det sista släpps',
          [('ner', 2, N), ('vanta', 200), ('ner', 5, N), ('vanta', 200), ('upp', 2), ('vanta', 400),
           ('bild', 'A', 'samma bild när det första fingret släppts'), ('upp', 5), ('vanta', 400), ('stilla',)],
          False, visas='B')
        g('pil ensam: ▶ och sedan ◀ var för sig, tillbaka',
          [('ner', 2, N), ('vanta', 150), ('upp', 2), ('vanta', 400), ('stilla',), ('bild', 'B', '▶ ett steg'),
           ('ner', 1, P), ('vanta', 150), ('upp', 1), ('vanta', 400), ('stilla',), ('bild', 'A', '◀ tillbaka')],
          False)
        # Pil + annan knapp: inget byte
        g('pil + pil: ◀ och ▶, släpps i samma ordning',
          [('ner', 1, P), ('vanta', 300), ('ner', 2, N), ('vanta', 300), ('upp', 1), ('vanta', 300), ('upp', 2),
           ('vanta', 600)], False)
        g('pil + pil: ▶ hålls, ◀ kort tryck, ▶ släpps',
          [('ner', 2, N), ('vanta', 300), ('ner', 1, P), ('vanta', 100), ('upp', 1), ('vanta', 500), ('upp', 2),
           ('vanta', 600)], False)
        g('pil + FÄRGLÄGG: ▶ hålls, FÄRGLÄGG kort tryck, ▶ släpps',
          [('ner', 2, N), ('vanta', 300), ('ner', 3, F), ('vanta', 100), ('upp', 3), ('vanta', 500), ('upp', 2),
           ('vanta', 600)], False, efter=self.inget_tips)
        g('pil + FÄRGLÄGG: ◀ hålls, FÄRGLÄGG 2 s, ◀ släpps sist',
          [('ner', 1, P), ('vanta', 300), ('ner', 3, F), ('vanta', 2000), ('upp', 3), ('vanta', 500), ('upp', 1),
           ('vanta', 600)], False, efter=self.inget_tips)
        g('pil + BÖRJA OM: ▶ hålls, BÖRJA OM kort tryck, ▶ släpps',
          [('ner', 2, N), ('vanta', 300), ('ner', 4, B), ('vanta', 150), ('upp', 4), ('vanta', 500), ('upp', 2),
           ('vanta', 600)], False)
        g('pil + BÖRJA OM: BÖRJA OM hålls 0,5 s, ◀ kort tryck under tiden',
          [('ner', 4, B), ('vanta', 200), ('ner', 1, P), ('vanta', 100), ('upp', 1), ('vanta', 200), ('upp', 4),
           ('vanta', 600)], False)
        # FÄRGLÄGG + annan knapp före 1,5 s: fyllningen bort, inget färgläggs (v115)
        g('FÄRGLÄGG + pil före 1,5 s: FÄRGLÄGG 1 s, ▶ kort tryck, FÄRGLÄGG hålls till 3 s',
          [('ner', 3, F), ('vanta', 1000), ('ner', 2, N), ('vanta', 100), ('upp', 2), ('vanta', 300),
           ('klass', 'holding', False, 'ingen fyllning i FÄRGLÄGG efter pilen'), ('vanta', 1600),
           ('bild', 'A', 'inget färglagt när FÄRGLÄGG hållits 3 s'), ('upp', 3), ('vanta', 600)],
          False, efter=self.inget_tips)
        g('FÄRGLÄGG + pil: FÄRGLÄGG kort, ◀ under tiden, ◀ släpps sist',
          [('ner', 3, F), ('vanta', 100), ('ner', 1, P), ('vanta', 100), ('upp', 3), ('vanta', 300), ('upp', 1),
           ('vanta', 600)], False, efter=self.inget_tips)
        g('FÄRGLÄGG + BÖRJA OM före 1,5 s: FÄRGLÄGG 1 s, BÖRJA OM kort tryck, FÄRGLÄGG hålls till 3 s',
          [('ner', 3, F), ('vanta', 1000), ('ner', 4, B), ('vanta', 150), ('upp', 4), ('vanta', 1850),
           ('bild', 'A', 'inget färglagt när FÄRGLÄGG hållits 3 s'), ('upp', 3), ('vanta', 600)],
          False, efter=self.inget_tips)
        # Pil efter att färgläggningen startat: färglagt, ingen bildväxling
        g('FÄRGLÄGG 2 s (färglagt), sedan ▶ kort tryck: ▶ byter inte',
          [('ner', 3, F), ('vanta', 2000), ('farglagd', 'A', 'färglagt medan FÄRGLÄGG hålls'),
           ('ner', 2, N), ('vanta', 100), ('upp', 2), ('vanta', 600), ('upp', 3), ('vanta', 600), ('stilla',),
           ('farglagd', 'A', 'samma bild, färglagd')], False, efter=self.inget_tips, farglagd=True)
        g('FÄRGLÄGG 2 s (färglagt), ◀ hålls, FÄRGLÄGG släpps, ◀ släpps: ◀ byter inte',
          [('ner', 3, F), ('vanta', 2000), ('ner', 1, P), ('vanta', 300), ('upp', 3), ('vanta', 300), ('upp', 1),
           ('vanta', 600), ('stilla',), ('farglagd', 'A', 'samma bild, färglagd')], False,
          efter=self.inget_tips, farglagd=True)
        # FÄRGLÄGG ensam
        g('FÄRGLÄGG ensam 2,5 s: färgläggs vid 1,5 s medan fingret ligger kvar',
          [('ner', 3, F), ('vanta', 300), ('klass', 'holding', True, 'fyllningen växer i FÄRGLÄGG'),
           ('vanta', 900), ('bild', 'A', 'inget färglagt efter 1,2 s'),
           ('vanta', 1300), ('farglagd', 'A', 'färglagt medan FÄRGLÄGG hålls (2,5 s)'), ('upp', 3), ('vanta', 600),
           ('stilla',), ('farglagd', 'A', 'färglagt efter släppet'), ('text', 'fill-btn', 'FÄRGLÄGG', 'inget tips')],
          False, farglagd=True)
        g('FÄRGLÄGG ensam 1,2 s: tipset, inget färglagt',
          [('ner', 3, F), ('vanta', 1200), ('upp', 3), ('vanta', 300),
           ('text', 'fill-btn', 'HÅLL INNE FÖR ATT FÄRGLÄGGA', 'tipset efter 1,2 s'), ('vanta', 1000),
           ('bild', 'A', 'inget färglagt efter tipset')], False)
        g('FÄRGLÄGG ensam 1 s, glider av knappen och hålls till 3 s: inget',
          [('ner', 3, F), ('vanta', 1000), ('glid', 3, -260, 0), ('vanta', 1800),
           ('bild', 'A', 'inget färglagt'), ('upp', 3), ('vanta', 600)], False,
          efter=self.inget_tips)
        self.fall_('mus: pilar och FÄRGLÄGG', self.mus_, 1280, 800)

    def pilhall(self):
        """En pil som hålls ensam i 0,7 s byter bild medan fingret ligger kvar (v117).
        Ett nytt finger var som helst före dess (knapp, samma pil, bilden) eller
        ett finger som glider av avbryter hållningen. Körs i 1600 × 800, så att
        det finns en bit rityta utanför bilden där ett finger inte målar (x = 5)."""
        P, N, F, B = 'prev-btn', 'next-btn', 'fill-btn', 'restart-btn'
        W, H = 1600, 800
        g = lambda namn, steg, visas='A', **kw: self.gest('pilhåll: ' + namn, steg, False, visas=visas,
                                                          bredd=W, hojd=H, **kw)
        g('▶ hålls 1,5 s: fyllning, bytt vid 0,7 s, inget mer vid släpp',
          [('ner', 2, N), ('vanta', 400), ('klass', 'holding', True, 'fyllningen växer i ▶', N),
           ('bild', 'A', 'samma bild efter 0,4 s'), ('vanta', 700), ('stilla',),
           ('bild', 'B', 'nästa bild medan ▶ hålls'), ('klass', 'holding', False, 'ingen fyllning efter bytet', N),
           ('upp', 2), ('vanta', 600), ('stilla',), ('bild', 'B', 'samma bild efter släppet (inget dubbelbyte)')],
          visas='B')
        g('◀ hålls 1,2 s: bytt bakåt en gång',
          [('ner', 1, P), ('vanta', 1200), ('stilla',), ('bild', 'C', 'föregående bild medan ◀ hålls'),
           ('upp', 1), ('vanta', 600), ('stilla',), ('bild', 'C', 'samma bild efter släppet')], visas='C')
        g('▶ hålls 5 s: bara en bild (ingen upprepning)',
          [('ner', 2, N), ('vanta', 5000), ('stilla',), ('bild', 'B', 'en bild fram efter 5 s'),
           ('upp', 2), ('vanta', 600), ('stilla',)], visas='B')
        g('▶ släpps efter 0,5 s: byter vid släpp som förut',
          [('ner', 2, N), ('vanta', 500), ('upp', 2), ('vanta', 400), ('stilla',),
           ('bild', 'B', 'nästa bild efter släppet')], visas='B')
        g('▶ och ett finger på bilden efter 0,3 s, hålls 1,5 s: inget byte medan den hålls, byter vid släpp',
          [('ner', 2, N), ('vanta', 300), ('punkt', 6, 5, 400),
           ('klass', 'holding', False, 'fyllningen borta i ▶', N), ('vanta', 1200),
           ('bild', 'A', 'samma bild medan ▶ hålls'), ('upp', 6), ('vanta', 300), ('bild', 'A', 'samma bild'),
           ('upp', 2), ('vanta', 400), ('stilla',), ('bild', 'B', 'nästa bild vid släppet (som förut)')], visas='B')
        g('ett finger på bilden först, ▶ hålls 1,5 s: inget byte medan den hålls',
          [('punkt', 6, 5, 400), ('vanta', 200), ('ner', 2, N), ('vanta', 1500),
           ('bild', 'A', 'samma bild medan ▶ hålls'), ('upp', 2), ('vanta', 400), ('stilla',),
           ('bild', 'B', 'nästa bild vid släppet (som förut)'), ('upp', 6)], visas='B')
        g('två fingrar på ▶ (det andra efter 0,3 s), hålls 1,5 s: ett steg vid släpp',
          [('ner', 2, N), ('vanta', 300), ('ner', 5, N), ('vanta', 1200), ('bild', 'A', 'samma bild medan ▶ hålls'),
           ('upp', 2), ('vanta', 300), ('upp', 5), ('vanta', 400), ('stilla',), ('bild', 'B', 'ett steg vid släppet')],
          visas='B')
        g('▶ och ◀ efter 0,3 s, hålls 2 s: inget',
          [('ner', 2, N), ('vanta', 300), ('ner', 1, P), ('vanta', 2000), ('bild', 'A', 'samma bild medan båda hålls'),
           ('upp', 1), ('vanta', 1500), ('bild', 'A', 'samma bild när ▶ hållits ensam igen 1,5 s'),
           ('upp', 2), ('vanta', 600)])
        g('▶ och FÄRGLÄGG efter 0,5 s, hålls 2,5 s: inget',
          [('ner', 2, N), ('vanta', 500), ('ner', 3, F), ('vanta', 2500), ('bild', 'A', 'samma bild, inget färglagt'),
           ('upp', 3), ('vanta', 300), ('upp', 2), ('vanta', 600)], efter=self.inget_tips)
        g('▶ och BÖRJA OM kort efter 0,5 s, ▶ hålls 2 s: inget',
          [('ner', 2, N), ('vanta', 500), ('ner', 4, B), ('vanta', 150), ('upp', 4), ('vanta', 1500),
           ('bild', 'A', 'samma bild'), ('upp', 2), ('vanta', 600)])
        g('▶ glider av efter 0,4 s och hålls kvar 1,5 s: inget',
          [('ner', 2, N), ('vanta', 400), ('glid', 2, -400, 0), ('vanta', 1500), ('bild', 'A', 'samma bild'),
           ('upp', 2), ('vanta', 600)])
        g('▶ hålls 1 s (bytt), sedan FÄRGLÄGG 2,5 s: färgläggs inte, ingen mer bild',
          [('ner', 2, N), ('vanta', 1000), ('stilla',), ('bild', 'B', 'bytt medan ▶ hålls'),
           ('ner', 3, F), ('vanta', 2500), ('bild', 'B', 'inget färglagt'), ('upp', 3), ('vanta', 300),
           ('upp', 2), ('vanta', 600), ('stilla',), ('bild', 'B', 'samma bild efter släppen')],
          visas='B', efter=self.inget_tips)
        g('▶ hålls 1 s (bytt), sedan ◀ kort: inget mer',
          [('ner', 2, N), ('vanta', 1000), ('stilla',), ('ner', 1, P), ('vanta', 150), ('upp', 1), ('vanta', 400),
           ('upp', 2), ('vanta', 600), ('stilla',), ('bild', 'B', 'samma bild efter släppen')], visas='B')
        self.gest('pilhåll: gesten ▶, ◀ och FÄRGLÄGG inom 0,5 s, 3,4 s: öppnar, ingen bild byts',
                  [('ner', 2, N), ('vanta', 250), ('ner', 1, P), ('vanta', 250), ('ner', 3, F), ('vanta', 3400)],
                  True, bredd=W, hojd=H)
        self.gest('pilhåll: gesten med ◀ ▶ FÄRGLÄGG i samma ögonblick, 3,4 s: öppnar, ingen bild byts',
                  [('ner3',), ('vanta', 3400)], True, bredd=W, hojd=H)

    def mus_(self):
        m = self.sida.mouse
        x, y = self.mitt('next-btn')
        m.move(x, y)
        m.down()
        self.vanta(800)
        self.kolla('mus: samma bild medan musknappen hålls på ▶', self.skillnad('A') == 0, self.skillnad('A'))
        m.up()
        self.vanta(400)
        self.stilla()
        self.kolla('mus: ▶ byter vid släpp', self.skillnad('B') == 0, self.skillnad('B'))
        m.click(*self.mitt('prev-btn'))
        self.vanta(400)
        self.stilla()
        self.kolla('mus: ◀ byter tillbaka', self.skillnad('A') == 0, self.skillnad('A'))
        x, y = self.mitt('fill-btn')
        m.move(x, y)
        m.down()
        self.vanta(200)
        m.up()
        self.vanta(300)
        self.kolla('mus: kort klick på FÄRGLÄGG ger tipset', self.text('fill-btn') == 'HÅLL INNE FÖR ATT FÄRGLÄGGA',
                   self.text('fill-btn'))
        self.vanta(5200)
        m.down()
        self.vanta(1000)
        m.move(x - 300, y, steps=5)
        self.vanta(1500)
        m.up()
        self.vanta(1000)
        self.kolla('mus: FÄRGLÄGG 1 s och av knappen, inget färglagt', self.skillnad('A') == 0, self.skillnad('A'))
        m.move(x, y)
        m.down()
        self.vanta(1200)
        self.kolla('mus: inget färglagt efter 1,2 s', self.skillnad('A') == 0, self.skillnad('A'))
        self.vanta(1300)
        n = self.skillnad('A')
        self.kolla('mus: färglagt medan musknappen hålls (2,5 s)', n > 50000, n)
        m.up()
        self.vanta(600)
        self.kolla('mus: inget tips efter släppet', self.text('fill-btn') == 'FÄRGLÄGG', self.text('fill-btn'))

    def som_forut(self):
        """FÄRGLÄGG ensam, kort tryck och pilarna fungerar som förut."""
        self.fall_('som förut: FÄRGLÄGG ensam, tips, pilar', self.som_forut_, 1280, 800)

    def som_forut_(self):
        if True:
            self.tryck('fill-btn', ms=150, vanta=False)
            self.vanta(300)
            self.kolla('kort tryck på FÄRGLÄGG ger tipset', self.text('fill-btn') == 'HÅLL INNE FÖR ATT FÄRGLÄGGA',
                       self.text('fill-btn'))
            self.kolla('inget färglagt av kort tryck', self.skillnad('A') == 0, self.skillnad('A'))
            self.ner(3, 'fill-btn')
            self.vanta(1300)
            self.kolla('inget färglagt efter 1,3 s', self.skillnad('A') == 0, self.skillnad('A'))
            self.vanta(1200)
            n = self.skillnad('A')
            self.kolla('FÄRGLÄGG ensam färglägger medan den hålls (2,5 s)', n > 50000, n)
            self.f.upp(3)
            self.vanta(600)
            self.stilla()
            n = self.skillnad('A')
            self.kolla('färglagt efter släppet', n > 50000, n)
            self.ner(4, 'restart-btn')
            self.vanta(1200)
            self.f.upp(4)
            self.vanta(4500)        # knappen slutar erbjuda "nollställ alla"
            self.stilla()
            self.kolla('BÖRJA OM tömmer bilden igen', self.skillnad('A') == 0, self.skillnad('A'))
            self.tryck('next-btn')
            self.kolla('▶ med finger: ett steg', self.skillnad('B') == 0, self.skillnad('B'))
            self.tryck('prev-btn')
            self.tryck('prev-btn')
            self.kolla('◀ ◀ med finger: två steg', self.skillnad('C') == 0, self.skillnad('C'))
            self.vanta(1100)
            fore = self.sida.evaluate('__hash()')
            self.sida.mouse.click(*self.mitt('next-btn'))
            slut = time.time() + 15
            while self.sida.evaluate('__hash()') == fore and time.time() < slut:
                self.vanta(100)
            self.stilla()
            self.kolla('▶ med mus: ett steg', self.skillnad('A') == 0, self.skillnad('A'))

    # --- läget ---
    def oppna_laget(self):
        self.ner(1, 'prev-btn')
        self.vanta(120)
        self.ner(2, 'next-btn')
        self.vanta(120)
        self.ner(3, 'fill-btn')
        self.vanta(3500)
        self.f.upp(1, 2, 3)
        self.vanta(300)

    def laget(self, namn, bredd, hojd, android=False):
        self.fall_('läget %s (%d×%d%s)' % (namn, bredd, hojd, ', Android' if android else ''),
                   lambda: self.laget_(namn, bredd, hojd), bredd, hojd, android)

    def laget_(self, namn, bredd, hojd):
        if True:
            self.oppna_laget()
            self.kolla('läget öppnat', self.oppet())
            if not self.oppet():
                return
            v = self.sida.evaluate("""() => {
                const r = id => { const b = document.getElementById(id).getBoundingClientRect();
                                  return { left: b.left, top: b.top, right: b.right, bottom: b.bottom }; };
                const t = document.getElementById('mark-text'), p = document.getElementById('mark-panel');
                return { bild: __bildruta(), yta: r('viewCanvas'), lager: r('markCanvas'), text: r('mark-text'),
                         panel: r('mark-panel'), knappar: r('button-container'), klar: r('mark-klar'),
                         avbryt: r('mark-avbryt'), app: r('app'),
                         textKlipps: t.scrollWidth > t.clientWidth + 1 || t.scrollHeight > t.clientHeight + 1,
                         panelKlipps: p.scrollWidth > p.clientWidth + 1 || p.scrollHeight > p.clientHeight + 1,
                         textInnehall: t.textContent, fonster: [innerWidth, innerHeight] };
            }""")
            bild, text, panel, klar, avbryt = v['bild'], v['text'], v['panel'], v['klar'], v['avbryt']

            def skar(a, b):
                return a['left'] < b['right'] - 0.5 and b['left'] < a['right'] - 0.5 and \
                    a['top'] < b['bottom'] - 0.5 and b['top'] < a['bottom'] - 0.5

            def inom(a, b):
                return a['left'] >= b['left'] - 0.5 and a['right'] <= b['right'] + 0.5 and \
                    a['top'] >= b['top'] - 0.5 and a['bottom'] <= b['bottom'] + 0.5

            def matt(r):
                return '%d×%d' % (round(r['right'] - r['left']), round(r['bottom'] - r['top']))

            self.kolla('texten är "Markera områden som ska ses över"',
                       v['textInnehall'] == 'Markera områden som ska ses över', v['textInnehall'])
            self.kolla('texten ligger utanför bilden', not skar(text, bild))
            self.kolla('texten ligger utanför ritytan', not skar(text, v['yta']))
            self.kolla('texten ligger i panelen', inom(text, panel), matt(text))
            self.kolla('texten klipps inte', not v['textKlipps'] and not v['panelKlipps'])
            self.kolla('panelen täcker knapp-panelen', inom(v['knappar'], panel) and inom(panel, v['knappar']))
            self.kolla('texten står överst (över KLAR och AVBRYT)',
                       text['bottom'] <= klar['top'] + 0.5 and text['bottom'] <= avbryt['top'] + 0.5)
            for id_, r in (('KLAR', klar), ('AVBRYT', avbryt)):
                self.kolla('%s ligger i panelen, utanför bilden' % id_, inom(r, panel) and not skar(r, bild), matt(r))
                self.kolla('%s är minst 36 px hög och 56 px bred' % id_,
                           r['bottom'] - r['top'] >= 36 and r['right'] - r['left'] >= 56, matt(r))
            self.kolla('KLAR och AVBRYT överlappar inte', not skar(klar, avbryt))
            self.kolla('lagret täcker hela bilden', inom(bild, v['lager']))
            # Inget annat än markeringslagret ligger över bilden, särskilt längs överkanten
            fel = self.sida.evaluate("""b => {
                const fel = [];
                for (let i = 0; i <= 20; i++) for (const y of [b.top + 1, b.top + 12, b.top + 30, (b.top + b.bottom) / 2, b.bottom - 2]) {
                    const x = b.left + 2 + (b.right - b.left - 4) * i / 20;      // ritytans bredd kan vara en bråkdel av en pixel
                    const e = document.elementFromPoint(x, y);
                    if (!e || e.id !== 'markCanvas') fel.push([Math.round(x), Math.round(y), e && (e.id || e.tagName)]);
                }
                return fel;
            }""", bild)
            self.kolla('hela bilden nås (bara markeringslagret över den, 105 punkter)', not fel, fel[:3] if fel else '')
            self.bild('laget-%s' % namn)

            # Markera längs bildens överkant
            bb = bild['right'] - bild['left']
            x0, x1, y = bild['left'] + 0.1 * bb, bild['right'] - 0.1 * bb, bild['top'] + 1
            self.f.ner(5, x0, y)
            for k in range(1, 13):
                self.f.flytta(5, x0 + (x1 - x0) * k / 12, y)
                self.vanta(25)
            self.f.upp(5)
            self.vanta(1100)
            andel = self.sida.evaluate('([a, b, y]) => __markRad(a, b, y)', [x0, x1, y])
            self.kolla('draget syns i bildens översta pixelrad', andel > 0.95, '%.0f %%' % (100 * andel))
            # Ett drag rakt ner genom platsen där skylten låg förut (mitt i överkanten)
            xm = (bild['left'] + bild['right']) / 2
            hb = bild['bottom'] - bild['top']
            self.f.ner(6, xm, bild['top'] + 1)
            for k in range(1, 9):
                self.f.flytta(6, xm, bild['top'] + 1 + 0.25 * hb * k / 8)
                self.vanta(25)
            self.f.upp(6)
            self.vanta(300)
            andel = self.sida.evaluate('([x, a, b]) => __markKol(x, a, b)', [xm, bild['top'], bild['top'] + 0.25 * hb])
            self.kolla('draget ner från överkanten syns hela vägen', andel > 0.95, '%.0f %%' % (100 * andel))
            self.kolla('barnets bild orörd av dragen', self.skillnad('A') == 0, self.skillnad('A'))
            self.bild('laget-%s-overkant' % namn)

            self.kolla('inget skickat före KLAR', len(self.skickat) == 0, len(self.skickat))
            self.tryck('mark-klar', vanta=False)
            self.vanta(500)
            kv = self.sida.evaluate("""() => { const t = document.getElementById('mark-text'), b = t.getBoundingClientRect();
                return { text: t.textContent, ruta: { left: b.left, top: b.top, right: b.right, bottom: b.bottom },
                         knappar: getComputedStyle(document.getElementById('mark-klar')).display }; }""")
            self.kolla('kvittot "Skickat ✓" i panelen, utanför bilden',
                       kv['text'] == 'Skickat ✓' and inom(kv['ruta'], panel) and not skar(kv['ruta'], bild), kv['text'])
            self.kolla('knapparna borta under kvittot', kv['knappar'] == 'none')
            self.bild('laget-%s-kvitto' % namn)
            self.kolla('en markering skickad', len(self.skickat) == 1, len(self.skickat))
            if self.skickat:
                m = json.loads(self.skickat[0])
                d = m['drag']
                self.kolla('två drag i markeringen', len(d) == 2, len(d))
                if len(d) == 2:
                    xs, ys = d[0][0::2], d[0][1::2]
                    if bredd > hojd:        # liggande: skärmens överkant = bildens y = 0
                        kant, langs = ys, xs
                    else:                   # stående: bilden är roterad, skärmens överkant = bildens x = 0
                        kant, langs = xs, ys
                    self.kolla('draget ligger i bildens överkant (högst 0,005 från kanten)', max(kant) <= 0.005,
                               'max %.3f' % max(kant))
                    self.kolla('draget går längs kanten (0,1–0,9)', abs(min(langs) - 0.1) < 0.01 and abs(max(langs) - 0.9) < 0.01,
                               '%.3f–%.3f' % (min(langs), max(langs)))
                    xs2, ys2 = d[1][0::2], d[1][1::2]
                    tvars = ys2 if bredd > hojd else xs2
                    self.kolla('det andra draget börjar i kanten och går 25 % in', min(tvars) <= 0.005 and abs(max(tvars) - 0.25) < 0.01,
                               '%.3f–%.3f' % (min(tvars), max(tvars)))
                self.kolla('fälten som förut', sorted(m) == ['bredd', 'drag', 'id', 'namn', 'nr', 'plattform', 'tid', 'version']
                           and m['plattform'] == 'webb' and m['bredd'] == 0.05, sorted(m))
            self.vanta(2200)
            self.kolla('läget stängt efter kvittot', not self.oppet())
            self.stilla()
            self.kolla('barnets bild orörd efter KLAR', self.skillnad('A') == 0, self.skillnad('A'))

            # AVBRYT: inget skickas, samma bild
            self.vanta(800)
            self.oppna_laget()
            self.kolla('läget öppnat igen', self.oppet())
            x, y = (bild['left'] + bild['right']) / 2, bild['top'] + 2
            self.f.ner(5, x - 60, y)
            self.f.flytta(5, x + 60, y)
            self.f.upp(5)
            self.tryck('mark-avbryt', vanta=False)
            self.vanta(700)
            self.kolla('AVBRYT stänger läget', not self.oppet())
            self.kolla('AVBRYT skickar inget', len(self.skickat) == 1, len(self.skickat))
            ko = self.sida.evaluate("localStorage.getItem('pensla-markeringar')")
            self.kolla('kön tom', ko is None, ko)
            self.vanta(800)
            self.orort('A')

    def alla_lagen(self):
        self.laget('liggande', 1280, 800)
        self.laget('staende', 800, 1280)
        self.laget('telefon-liggande', 640, 360)
        self.laget('telefon-staende', 360, 640)
        self.laget('liten-telefon-liggande', 568, 320)
        self.laget('liten-telefon-staende', 320, 568)
        self.laget('android-telefon-liggande', 640, 360, android=True)
        self.laget('android-platta-liggande', 1280, 800, android=True)

    def kor(self):
        srv = None
        if self.arg.adress:
            self.adress = self.arg.adress
        else:
            srv = servera(self.arg.mapp)
            self.adress = 'http://127.0.0.1:%d/index.html' % srv.server_address[1]
        print('Provar', self.adress)
        with sync_playwright() as pw:
            self.webblasare = pw.chromium.launch()
            grupper = [('gest', self.alla_gester), ('tre', self.tre_i_alla_ordningar), ('regler', self.regler),
                       ('pilhall', self.pilhall), ('forut', self.som_forut), ('laget', self.alla_lagen)]
            for namn, gor in grupper:
                if self.arg.grupp and namn not in self.arg.grupp:
                    continue
                gor()
            self.webblasare.close()
        if srv:
            srv.shutdown()
        fel = [r for r in self.resultat if not r[2]]
        fall = sorted({r[0] for r in self.resultat})
        print('\n%d kontroller i %d fall: %d som väntat, %d fel' % (len(self.resultat), len(fall),
                                                                   len(self.resultat) - len(fel), len(fel)))
        for r in fel:
            print('FEL: %s: %s [%s]' % (r[0], r[1], r[3]))
        return 1 if fel else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(description='Prov av den hemliga markeringen i webbappen.')
    ap.add_argument('--mapp', default=ROT, help='mappen med appen (förval: arbetskopian)')
    ap.add_argument('--adress', help='prova en publicerad adress i stället, t.ex. testmiljöns index.html')
    ap.add_argument('--bilder', help='spara skärmbilder i den här mappen')
    ap.add_argument('--grupp', nargs='*', choices=['gest', 'tre', 'regler', 'pilhall', 'forut', 'laget'],
                    help='bara de här grupperna')
    ap.add_argument('--bara', help='bara gestfall vars namn innehåller texten')
    arg = ap.parse_args()
    prov = Prov(arg)
    if arg.bara:
        hel = prov.gest
        prov.gest = lambda namn, *a, **k: hel(namn, *a, **k) if arg.bara in namn else None
        arg.grupp = arg.grupp or ['gest', 'tre', 'regler', 'pilhall']
    sys.exit(prov.kor())
