"""Bildöversyn: går igenom de aktiva bilderna (eller de nummer man anger) och
letar efter glapp i konturerna och efter keIWs/kompisar som skärs av eller
ligger bakom streck.

    python verktyg/bildoversyn.py            # alla aktiva
    python verktyg/bildoversyn.py 4 26 114   # bara de numren

Skriver granskning/oversyn/NAMN.png (konturerna över en blek färgbild: röda
ringar = glapp, orange = streck som slutar fritt, figurerna inritade med det
som döljs i dag rödtonat), granskning/oversyn/resultat.json och en tabell i
markdown (granskning/oversyn/tabell.md) som rapporten
docs/utredningar/bildoversyn.md bygger på. Ändrar inga bilder.

Glapp: konturerna tunnas till ett skelett (som TECKNING i fargbild.py) och
varje fri ände undersöks. Finns en annan linje inom GLAPP_RADIE px framför
änden är det ett glapp (två ytor rinner ihop), annars ett streck som slutar
fritt (glansstreck, skuggstreck eller en kontur som tar slut). Ändar vid
bildkanten räknas inte.

Figurerna: som i appen ritas de bara i sina ytor och ovanför fötterna.
`dold` = andel av figuren (stilla) som inte syns, `kropp` = andel av
kroppen, `streck` = ett streck går över kroppen, `arm` = andel av den
vinkande armen som klipps, `står` = andel av fötternas bredd som har något
under sig (0 = svävar mitt i sin yta).
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bildanalys as ba  # noqa: E402

UT = os.path.join(ba.ROT, 'granskning', 'oversyn')
GLAPP_RADIE = 20
DOLD_GRANS = 2.0      # % av figuren som får döljas innan den räknas som delvis dold


def forhandsbild(rgb, alfa, andar, figurer):
    blek = (rgb * 0.45 + 255 * 0.55).astype(np.uint8)
    a = (alfa / 255.0)[..., None]
    im = (blek * (1 - a) + np.array([58, 58, 68]) * a).astype(np.uint8)
    lab_kopia = None
    bild = Image.fromarray(im)
    d = ImageDraw.Draw(bild, 'RGBA')
    for namn, c, syns in figurer:
        farg = ba.FARGER[namn]
        for x0, y0, x1, y1, f in ba.rektanglar(c, ba.STILLA):
            d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=farg[f] if f in farg else farg['bla'])
        # det som döljs i appen: rött raster över
        fig = ba.figurmask(c, alfa.shape)
        dold = fig & ~syns
        if dold.any():
            ov = np.zeros(alfa.shape + (4,), np.uint8)
            ov[dold] = (230, 30, 30, 150)
            bild.paste(Image.fromarray(ov), (0, 0), Image.fromarray(ov))
            d = ImageDraw.Draw(bild, 'RGBA')
    for y, x, typ, _, mal in andar:
        if typ == 'glapp':
            d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(230, 0, 0, 255), width=3)
            d.line([x, y, mal[1], mal[0]], fill=(230, 0, 0, 255), width=2)
        else:
            d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(255, 140, 0, 255), width=2)
    del lab_kopia
    return bild


def main():
    nummer = {int(a) for a in sys.argv[1:] if a.isdigit()}
    alla, aktiva, borttagna = ba.bilder()
    valda = [b for b in alla if (b['nr'] in nummer) if nummer] or [b for b in alla if b['nr'] in aktiva]
    os.makedirs(UT, exist_ok=True)
    resultat = []
    with ba.Ritare() as r:
        for b in valda:
            alfa, rgb = ba.las_bild(r, b['fil'])
            linje = alfa >= ba.LINE_ALPHA
            sk = ba.skelett(linje)
            andar = ba.andar(sk, radie=GLAPP_RADIE)
            lab, _ = nd.label(~linje)
            figurer, fres = [], {}
            for namn in ('keiws', 'gron', 'rod'):
                c = b.get(namn)
                if not c:
                    continue
                k = ba.kolla_figur(c, alfa, lab)
                fres[namn] = k
                H, W = lab.shape
                ytor = {int(lab[min(H - 1, round(py)), min(W - 1, round(px))]) for px, py in c['ytor']} - {0}
                syns = np.isin(lab, list(ytor))
                syns[int(c['y']) + 1:] = False
                figurer.append((namn, c, syns))
            # två figurer på samma plats
            platser = [(n, c) for n, c, _ in figurer]
            krock = []
            for i in range(len(platser)):
                for j in range(i + 1, len(platser)):
                    m1 = ba.figurmask(platser[i][1], lab.shape)
                    m2 = ba.figurmask(platser[j][1], lab.shape)
                    if (m1 & m2).any():
                        krock.append(platser[i][0] + '+' + platser[j][0])
            rad = {
                'nr': b['nr'], 'fil': b['fil'], 'namn': b['namn'],
                'glapp': sum(1 for a in andar if a[2] == 'glapp'),
                'losa': sum(1 for a in andar if a[2] == 'lös'),
                'figurer': fres, 'krock': krock,
            }
            resultat.append(rad)
            forhandsbild(rgb, alfa, andar, figurer).save(os.path.join(UT, b['fil'] + '.png'))
            print(b['nr'], b['fil'], 'glapp', rad['glapp'], 'lösa', rad['losa'],
                  {n: (k['dold'], k['kropp_dold'], k['streck_over_kropp']) for n, k in fres.items()}, krock or '')
    json.dump(resultat, open(os.path.join(UT, 'resultat.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(os.path.join(UT, 'tabell.md'), 'w', encoding='utf-8').write(tabell(resultat))


def figurtext(k):
    if not k:
        return '–'
    delar = []
    if k['utanfor']:
        delar.append('utanför bilden')
    if k['dold'] > DOLD_GRANS:
        delar.append('%d %% dold' % round(k['dold']))
    if k['kropp_dold'] > DOLD_GRANS:
        delar.append('kroppen %d %%' % round(k['kropp_dold']))
    if k['streck_over_kropp']:
        delar.append('streck över kroppen')
    if k['arm_dold'] > 30:
        delar.append('armen klipps')
    if k['star_pa'] < 0.5:
        delar.append('svävar')
    return ', '.join(delar) or 'ok'


def tabell(resultat):
    rader = ['| Nr | Bild | Glapp | Lösa streck | keIWs | Grön | Röd |',
             '|---:|---|---:|---:|---|---|---|']
    for r in resultat:
        f = r['figurer']
        rad = '| %d | %s | %d | %d | %s | %s | %s |' % (
            r['nr'], r['namn'], r['glapp'], r['losa'],
            figurtext(f.get('keiws')), figurtext(f.get('gron')), figurtext(f.get('rod')))
        if r['krock']:
            rad = rad[:-2] + ' (krockar: ' + ', '.join(r['krock']) + ') |'
        rader.append(rad)
    return '\n'.join(rader) + '\n'


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
