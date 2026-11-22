"""Läser de hemliga markeringarna (CLAUDE.md, "Hemlig markering").

Ägaren märker ut bilder som ska ses över genom att måla grovt runt det som
ska kollas (håll ◀, ▶ och FÄRGLÄGG i 5 s). Markeringarna kommer från

  --fil FIL.jsonl      plattans fil från Pensla N (en rad JSON per markering),
                       hämtad med adb pull; flera filer går
  --adb                hämtar plattans fil med adb och läser den
  --server             mottagarens databas (D1) på Cloudflare, via
                       npx wrangler d1 execute --remote (kräver inloggning)
  --lokal MAPP         en lokal D1 (wrangler dev --persist-to MAPP), för prov;
                       --konfig pekar ut en wrangler-fil med D1-bindningen

Skriptet listar markeringarna per bild och ritar en översiktsbild per bild
med dragen ovanpå färgbilden: granskning/markeringar/NR-FIL.png (--ut MAPP).
En markering utan drag gäller hela bilden (ritas som en ram).

    python verktyg/markeringar.py --fil markeringar.jsonl
    python verktyg/markeringar.py --server            (bara ohanterade)
    python verktyg/markeringar.py --server --alla

Format (samma i webbappen, Pensla N och mottagaren):
    {"id": "16 hex", "nr": 22, "namn": "Ambulans",
     "drag": [[x0, y0, x1, y1, ...], ...], "bredd": 0.05,
     "tid": "2026-11-22T20:15:03Z", "version": "v110-test", "plattform": "webb"}
Punkterna är normerade 0–1 (x mot bildens bredd, y mot höjden) och bredd är
penselns bredd som andel av bildens höjd.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
DATABAS = 'pensla-markeringar'
PLATTFIL = '/sdcard/Android/data/com.keiws.pensla.nativ/files/markeringar.jsonl'
FARGER = [(230, 0, 126), (0, 114, 206), (0, 150, 90), (240, 130, 0), (120, 60, 200), (200, 30, 30)]
GENOMSYN = 115      # 0–255, som i apparna (0,45)


def bilder():
    """nr -> (namn, fil) ur bilder.js."""
    text = open(os.path.join(ROT, 'bilder.js'), encoding='utf-8').read()
    return {int(nr): (namn, fil) for nr, namn, fil in
            re.findall(r"\{ nr: (\d+), namn: '([^']*)', fil: '([^']+)'", text)}


def kontrollera(m):
    """Markeringen i fast form, eller None om raden inte är en markering."""
    try:
        drag = []
        for d in m['drag']:
            if not isinstance(d, list) or len(d) < 2 or len(d) % 2:
                return None
            drag.append([min(1.0, max(0.0, float(v))) for v in d])
        bredd = float(m.get('bredd', 0.05))
        return {'id': str(m['id']), 'nr': int(m['nr']), 'namn': str(m.get('namn', '')), 'drag': drag,
                'bredd': min(0.2, max(0.005, bredd)), 'tid': str(m.get('tid', '')),
                'version': str(m.get('version', '')), 'plattform': str(m.get('plattform', '')),
                'miljo': str(m.get('miljo', '')), 'hanterad': int(m.get('hanterad', 0) or 0)}
    except (KeyError, TypeError, ValueError):
        return None


def las_fil(sokvag, kalla=None):
    ut, fel = [], 0
    with open(sokvag, encoding='utf-8') as f:
        for rad in f:
            rad = rad.strip()
            if not rad:
                continue
            try:
                m = kontrollera(json.loads(rad))
            except ValueError:
                m = None
            if m is None:
                fel += 1
                continue
            m['kalla'] = kalla or os.path.basename(sokvag)
            ut.append(m)
    if fel:
        print(f'OBS: {fel} rader i {sokvag} gick inte att läsa och hoppades över', file=sys.stderr)
    return ut


def las_adb(ut_mapp):
    """Hämtar plattans fil med adb (ingen root behövs) och läser den."""
    os.makedirs(ut_mapp, exist_ok=True)
    mal = os.path.join(ut_mapp, 'markeringar-platta.jsonl')
    r = subprocess.run(['adb', 'pull', PLATTFIL, mal], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('adb pull gick inte: ' + (r.stderr or r.stdout).strip())
    return las_fil(mal, 'plattan')


def wrangler_fraga(extra, alla):
    sql = 'SELECT id, nr, namn, drag, bredd, tid, version, plattform, miljo, hanterad FROM markering'
    if not alla:
        sql += ' WHERE hanterad = 0'
    sql += ' ORDER BY mottagen'
    kommando = ['npx', 'wrangler@4', 'd1', 'execute', DATABAS, '--json', '--command', sql] + extra
    if os.name == 'nt':
        kommando = ['cmd', '/c'] + kommando
    r = subprocess.run(kommando, cwd=ROT, capture_output=True, text=True, encoding='utf-8',
                       env=dict(os.environ, WRANGLER_SEND_METRICS='false'))
    if r.returncode != 0:
        raise SystemExit('wrangler gick inte:\n' + (r.stdout + r.stderr).strip())
    text = r.stdout
    svar = json.loads(text[text.index('['):])
    ut = []
    for rad in svar[0]['results']:
        rad = dict(rad)
        rad['drag'] = json.loads(rad['drag'])
        m = kontrollera(rad)
        if m:
            m['kalla'] = 'servern' if '--remote' in extra else 'lokal D1'
            ut.append(m)
    return ut


def rita(nr, namn, fil, lista, ut_mapp):
    """Översiktsbild: färgbilden med alla markeringars drag ovanpå."""
    from PIL import Image, ImageDraw, ImageFont
    bild = Image.open(os.path.join(ROT, 'bilder', 'farg', fil + '.jpg')).convert('RGB')
    W, H = bild.size
    try:
        font = ImageFont.truetype('arialbd.ttf', max(16, H // 34))
    except OSError:
        font = ImageFont.load_default()
    skyltar = []
    for i, m in enumerate(lista):
        farg = FARGER[i % len(FARGER)]
        # Ett lager per markering, heltäckande och sedan halvgenomskinligt
        # (som i apparna), så att överlapp inom en markering inte blir mörkare.
        mask = Image.new('L', (W, H), 0)
        d = ImageDraw.Draw(mask)
        b = max(2, round(m['bredd'] * H))
        if not m['drag']:
            k = max(6, H // 60)
            d.rectangle([k // 2, k // 2, W - 1 - k // 2, H - 1 - k // 2], outline=255, width=k)
            skyltar.append((i, 3 * k, 3 * k + i * (H // 22), farg, ' hela bilden'))
        for drag in m['drag']:
            p = [(drag[j] * W, drag[j + 1] * H) for j in range(0, len(drag), 2)]
            # Sträcka för sträcka med runda ändar (Pillows joint='curve' fyller
            # igen skarpa svängar).
            for q in range(len(p) - 1):
                d.line([p[q], p[q + 1]], fill=255, width=b)
            for x, y in p:
                d.ellipse([x - b / 2, y - b / 2, x + b / 2, y + b / 2], fill=255)
            skyltar.append((i, p[0][0], p[0][1], farg, ''))
        bild.paste(Image.new('RGB', (W, H), farg), (0, 0), mask.point(lambda v: v * GENOMSYN // 255))
    d = ImageDraw.Draw(bild)
    for i, x, y, farg, extra in skyltar:
        text = str(i + 1) + extra
        l, t, r, b2 = d.textbbox((0, 0), text, font=font)
        tw, th = r - l, b2 - t
        x = min(max(10, x - tw / 2), W - tw - 12)
        y = min(max(8, y - th / 2), H - th - 14)
        d.rounded_rectangle([x - 6, y - 4, x + tw + 6, y + th + 8], radius=6, fill=(255, 255, 255), outline=farg, width=2)
        d.text((x - l, y - t), text, fill=farg, font=font)
    os.makedirs(ut_mapp, exist_ok=True)
    mal = os.path.join(ut_mapp, f'{nr:03d}-{fil}.png')
    bild.save(mal)
    return mal


def main():
    p = argparse.ArgumentParser(description='Läser de hemliga markeringarna och ritar översiktsbilder.')
    p.add_argument('--fil', action='append', default=[], help='JSONL-fil från plattan (kan anges flera gånger)')
    p.add_argument('--adb', action='store_true', help='hämta plattans fil med adb pull')
    p.add_argument('--server', action='store_true', help='läs mottagarens databas på Cloudflare (wrangler --remote)')
    p.add_argument('--lokal', metavar='MAPP', help='läs en lokal D1 (wrangler dev --persist-to MAPP)')
    p.add_argument('--konfig', metavar='FIL', help='wrangler-fil med D1-bindningen (till --lokal)')
    p.add_argument('--alla', action='store_true', help='ta även med dem som är hanterade (servern)')
    p.add_argument('--ut', default=os.path.join(ROT, 'granskning', 'markeringar'), help='mapp för översiktsbilderna')
    p.add_argument('--inga-bilder', action='store_true', help='lista bara, rita inget')
    a = p.parse_args()
    if not (a.fil or a.adb or a.server or a.lokal):
        p.error('ange minst en källa: --fil, --adb, --server eller --lokal')

    alla = []
    for f in a.fil:
        alla += las_fil(f)
    if a.adb:
        alla += las_adb(a.ut)
    if a.server:
        alla += wrangler_fraga(['--remote'], a.alla)
    if a.lokal:
        extra = ['--local', '--persist-to', os.path.abspath(a.lokal)]
        if a.konfig:
            extra += ['-c', os.path.abspath(a.konfig)]
        alla += wrangler_fraga(extra, a.alla)

    # Samma markering från två källor (eller skriven två gånger) räknas en gång.
    sedda, unika = set(), []
    for m in alla:
        if m['id'] not in sedda:
            sedda.add(m['id'])
            unika.append(m)
    kanda = bilder()
    per_bild = {}
    for m in unika:
        per_bild.setdefault(m['nr'], []).append(m)

    print(f'{len(unika)} markeringar på {len(per_bild)} bilder'
          + (f' ({len(alla) - len(unika)} dubbletter borttagna)' if len(alla) != len(unika) else ''))
    for nr in sorted(per_bild):
        lista = sorted(per_bild[nr], key=lambda m: m['tid'])
        namn, fil = kanda.get(nr, (lista[0]['namn'] or '?', None))
        print(f'\nNr {nr} {namn}' + (f' (bilder/farg/{fil}.jpg)' if fil else ' (finns inte i bilder.js)'))
        for i, m in enumerate(lista):
            vad = 'hela bilden' if not m['drag'] else \
                f"{len(m['drag'])} drag, {sum(len(d) // 2 for d in m['drag'])} punkter"
            ovrigt = ' '.join(x for x in (m['plattform'], m['version'], m['miljo'], m['kalla'],
                                          'HANTERAD' if m['hanterad'] else '') if x)
            print(f"  {i + 1}. {m['tid']}  {vad}  [{ovrigt}]  id {m['id']}")
        if fil and not a.inga_bilder:
            if os.path.exists(os.path.join(ROT, 'bilder', 'farg', fil + '.jpg')):
                print('  -> ' + rita(nr, namn, fil, lista, a.ut))
            else:
                print(f'  (ingen färgbild bilder/farg/{fil}.jpg, ingen översiktsbild)')


if __name__ == '__main__':
    main()
