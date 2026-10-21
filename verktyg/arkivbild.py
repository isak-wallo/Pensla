"""Gör om de gamla bilderna i arkiv/ till bilder i bildbanken.

Användning:  python verktyg/arkivbild.py

För varje arkiv/NN-namn-linjer.png skrivs bilder/farg/arkiv-NN-namn.svg
(konturerna spårade med potrace). Finns färgbilden arkiv/NN-namn.png blir
den bilder/farg/arkiv-NN-namn.jpg. De utan färgbild står i ALLA_BILDER med
`utanFarg: true`: de syns i galleriet men kan inte väljas förrän någon
färglagt dem.
"""
import os
import numpy as np
from PIL import Image
from fargbild import svg, UT

ARKIV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'arkiv')


def main():
    for fil in sorted(os.listdir(ARKIV)):
        if not fil.endswith('-linjer.png'):
            continue
        namn = fil[:-len('-linjer.png')]
        L = np.asarray(Image.open(os.path.join(ARKIV, fil)).convert('L'))
        open(os.path.join(UT, f'arkiv-{namn}.svg'), 'w').write(svg(L < 140))
        farg = os.path.join(ARKIV, namn + '.png')
        if os.path.exists(farg):
            Image.open(farg).convert('RGB').save(os.path.join(UT, f'arkiv-{namn}.jpg'), quality=88)
        print(namn, 'färg' if os.path.exists(farg) else 'bara konturer')


if __name__ == '__main__':
    main()
