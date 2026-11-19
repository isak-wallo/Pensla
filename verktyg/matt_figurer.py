"""Mäter hur figurerna i vektorbilderna syns i sin klippbana (som PenslaVy):

    python verktyg/matt_figurer.py [NAMN ...]          # GOMSTALLEN-platserna
    python verktyg/matt_figurer.py --sank NAMN ...     # föreslå hur långt de ska sänkas

kropp = andel av kroppen som syns (ca 100 % = sitter OVANPÅ saken framför,
fötterna skymda men kroppen hel; den ska skymmas en bit, ca 65–80 %),
fotter = andel av fötterna som syns, arm = andel av den vinkande armen
(vinka-rutorna med armen uppe) som syns.
"""
import json
import os
import sys

import numpy as np
from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bildanalys as ba  # noqa: E402
import vektorbild as vb  # noqa: E402

F = vb.F
KROPP = [[0, 0, 160, 160, 'bla']]
FOTTER = [[0, 168, 160, 204, 'bla']]


def armrutor():
    """Armen i vinka-bilderna där den är uppe (y0 < 64)."""
    ut = []
    for r in ba.VINKA:
        for a in r:
            if a[0] >= 160 and a[1] < 64 and a[:4] not in [b[:4] for b in ut]:
                ut.append(a)
    return ut


def matt(linjeyta, linje, c):
    H, W = linje.shape
    cc = vb.skalad(c, F)
    klipp = vb.klippbana(linjeyta, c)
    if not klipp:
        return None
    k = vb.fyll_bana(klipp, (H, W), F) & ~linje
    # PenslaVy klipper också till rutan under fötterna
    k[int(round(c['y'] * F)):] = False
    ut = {}
    for namn, rekt in (('kropp', KROPP), ('fotter', FOTTER), ('arm', armrutor())):
        m = ba.figurmask(cc, (H, W), rekt)
        ut[namn] = (m & k).sum() / max(1, m.sum())
    return ut


def main():
    a = sys.argv[1:]
    sank = '--sank' in a
    a = [x for x in a if not x.startswith('--')]
    namn = a or sorted(vb.GOMSTALLEN)
    for fil in namn:
        data = json.load(open(os.path.join(vb.UT_FORVAL, fil + '.json'), encoding='utf-8'))
        linje = vb.fyll_bana(data['linje']['d'], (data['h'] * F, data['b'] * F), F)
        linjeyta, _ = nd.label(~linje)
        for n, v in vb.GOMSTALLEN.get(fil, {}).items():
            c = {'x': v[0], 'y': v[1], 's': v[2]}
            m = matt(linjeyta, linje, c)
            print('%-14s %-5s (%4d, %3d, %.2f)  kropp %3.0f %%  fötter %3.0f %%  arm %3.0f %%' % (
                fil, n, c['x'], c['y'], c['s'], 100 * m['kropp'], 100 * m['fotter'], 100 * m['arm']), flush=True)
            if sank:
                for dy in range(2, 60, 2):
                    c2 = dict(c, y=c['y'] + dy)
                    m2 = matt(linjeyta, linje, c2)
                    if m2 and m2['kropp'] <= 0.78:
                        print('    sänk %d -> y %d: kropp %.0f %%, arm %.0f %%' % (dy, c2['y'], 100 * m2['kropp'], 100 * m2['arm']))
                        break


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
