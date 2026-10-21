"""Uppdaterar sw.js efter AKTIVA i bilder.js.

Skriver in de aktiva bildernas svg och jpg i ASSETS (så att bara de cachas
för offline) och höjer VERSION. Kör efter att AKTIVA ändrats:

    python verktyg/aktiva.py
"""
import os
import re

ROT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def las(namn):
    return open(os.path.join(ROT, namn), encoding='utf-8').read()


def main():
    b = las('bilder.js')
    alla = {int(nr): fil for nr, fil in re.findall(r"nr: (\d+), namn: '[^']*', fil: '([^']+)'", b)}
    aktiva = [int(n) for n in re.findall(r'\d+', re.search(r'const AKTIVA = \[(.*?)\]', b, re.S).group(1))]
    saknas = [n for n in aktiva if n not in alla]
    if saknas:
        raise SystemExit(f'AKTIVA har nummer som inte finns i ALLA_BILDER: {saknas}')
    utan = [int(n) for n in re.findall(r"nr: (\d+), [^}]*utanFarg: true", b)]
    if set(aktiva) & set(utan):
        raise SystemExit(f'AKTIVA har bilder utan färgbild: {sorted(set(aktiva) & set(utan))}')
    filer = []
    for n in aktiva:
        for ext in ('svg', 'jpg'):
            f = f'bilder/farg/{alla[n]}.{ext}'
            if not os.path.exists(os.path.join(ROT, f)):
                raise SystemExit(f'Filen saknas: {f}')
            filer.append(f"  './{f}',")

    sw = las('sw.js')
    fasta = ['./', './index.html', './style.css', './app.js', './keiws.js', './bilder.js']
    slut = ['./manifest.json', './icon-192.png', './icon-512.png']
    rader = [f"  '{f}'," for f in fasta] + filer + [f"  '{f}'," for f in slut]
    rader[-1] = rader[-1].rstrip(',')
    sw = re.sub(r'const ASSETS = \[.*?\n\];', 'const ASSETS = [\n' + '\n'.join(rader) + '\n];', sw, flags=re.S)
    v = int(re.search(r"const VERSION = 'v(\d+)'", sw).group(1)) + 1
    sw = re.sub(r"const VERSION = 'v\d+'", f"const VERSION = 'v{v}'", sw)
    open(os.path.join(ROT, 'sw.js'), 'w', encoding='utf-8', newline='\n').write(sw)
    print(f'{len(aktiva)} aktiva av {len(alla)} bilder, sw.js -> v{v}')


if __name__ == '__main__':
    main()
