"""Mäter hur figurerna i vektorbilderna syns i sin klippbana (som PenslaVy):

    python verktyg/matt_figurer.py [--ut MAPP] [NAMN ...]   # figurerna i JSON-filerna
    python verktyg/matt_figurer.py --sank NAMN ...          # föreslå hur långt de ska sänkas

kropp = andel av kroppen som syns (ca 100 % = sitter OVANPÅ saken framför,
fötterna skymda men kroppen hel; den ska skymmas en bit, KROPP_MAL i
vektorbild.py, ca 65–80 %), fotter = andel av fötterna som syns, arm =
andel av den vinkande armen (vinka-rutorna med armen uppe) som syns.
Förval för MAPP: native/bilder i repot.
"""
import json
import os
import sys

from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bildanalys as ba  # noqa: E402
import vektorbild as vb  # noqa: E402

F = vb.F


def main():
    a = sys.argv[1:]
    sank = '--sank' in a
    ut = os.path.join(ba.ROT, 'native', 'bilder')
    if '--ut' in a:
        i = a.index('--ut'); ut = a[i + 1]; del a[i:i + 2]
    a = [x for x in a if not x.startswith('--')]
    namn = a or sorted(f[:-5] for f in os.listdir(ut) if f.endswith('.json'))
    for fil in namn:
        data = json.load(open(os.path.join(ut, fil + '.json'), encoding='utf-8'))
        linje = vb.fyll_bana(data['linje']['d'], (data['h'] * F, data['b'] * F), F)
        linjeyta, _ = nd.label(~linje)
        for n, c in data.get('figurer', {}).items():
            m = vb.figurmatt(linjeyta, linje, c, klipp=c.get('klipp'))
            if m is None:
                print('%-16s %-5s saknar klippbana' % (fil, n))
                continue
            print('%-16s %-5s (%4d, %3d, %.3f)  kropp %3.0f %%  fötter %3.0f %%  arm %3.0f %%' % (
                fil, n, c['x'], c['y'], c['s'], 100 * m['kropp'], 100 * m['fotter'], 100 * m['arm']), flush=True)
            if sank:
                for dy in range(2, 60, 2):
                    c2 = dict(c, y=c['y'] + dy)
                    m2 = vb.figurmatt(linjeyta, linje, c2, klipp=c.get('klipp'))
                    if m2 and m2['kropp'] <= vb.KROPP_MAL[1]:
                        print('    sänk %d -> y %d: kropp %.0f %%, arm %.0f %%' % (dy, c2['y'], 100 * m2['kropp'], 100 * m2['arm']))
                        break


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
