"""Släpper Pensla på pensla.keiws.com, eller testversionen.

https://test.pensla.keiws.com är testmiljön och publiceras efter varje push
med --test, med VERSION i sw.js som den är (v90, v91 ...), galleriet
(galleri.html och alla bilder i banken, även inaktiva) och en robots.txt som
stänger ute sökmotorerna. Testversionen heter "Pensla test", så att båda går
att installera, och har en GALLERI-knapp på startskärmen (galleriet går inte
att installera som egen app bredvid den).

pensla.keiws.com byts bara när det här skriptet körs med --skarpt. Den skarpa
sidan har egna versionsnummer: i den släppta sw.js byts VERSION mot
släppnumret (v1, v2 ...), så installerade appar hämtar den nya versionen.
Varje släpp märks med en tagg i git (slapp-1, slapp-2 ...).

Skriptet tar appens filer (ASSETS i sw.js, plus sw.js) från den pushade koden
(origin/main), inte från arbetskopian. Inget annat i repot publiceras.

    python verktyg/slapp.py            # visar vad som är släppt och vad som är nytt
    python verktyg/slapp.py --test     # publicerar testversionen (efter varje push)
    python verktyg/slapp.py --skarpt   # släpper origin/main

Kräver Node och att man loggat in en gång med `npx wrangler login`.
"""
import os
import re
import shutil
import subprocess
import sys

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEBB = os.path.join(ROT, 'webb')


def git(*arg):
    return subprocess.run(['git', *arg], cwd=ROT, check=True, capture_output=True,
                          text=True, encoding='utf-8').stdout.strip()


def slapp():
    """Senaste släppet: (nummer, tagg), eller (0, None) om inget släppts."""
    alla = [(int(m[1]), t) for t in git('tag', '--list', 'slapp-*').split()
            if (m := re.fullmatch(r'slapp-(\d+)', t))]
    return max(alla) if alla else (0, None)


def version(ref):
    return re.search(r"const VERSION = '([^']*)'", git('show', ref + ':sw.js')).group(1)


def status():
    git('fetch', '-q', '--tags', 'origin')
    nr, tagg = slapp()
    print('test.pensla.keiws.com:', version('origin/main'))
    if not tagg:
        print('pensla.keiws.com: inget släppt än')
        return
    print('pensla.keiws.com: v%d (%s från %s)' % (nr, tagg, version(tagg)))
    print('Nytt sedan dess:\n' + (git('log', '--oneline', tagg + '..origin/main') or '  inget'))


def bygg(nr):
    """webb/ med appens filer från origin/main och VERSION = vNR (None: testversionen,
    med galleriet, VERSION som den är och inga sökmotorer)."""
    shutil.rmtree(WEBB, ignore_errors=True)
    sw = git('show', 'origin/main:sw.js')
    filer = [f for f in re.findall(r"'\./([^']*)'", re.search(r'const ASSETS = \[(.*?)\];', sw, re.S).group(1)) if f]
    filer.append('sw.js')
    if nr is None:
        filer += ['galleri.html'] + git('ls-tree', '-r', '--name-only', 'origin/main', 'bilder/').split('\n')
    for fil in dict.fromkeys(filer):
        mal = os.path.join(WEBB, fil)
        os.makedirs(os.path.dirname(mal), exist_ok=True)
        data = subprocess.run(['git', 'show', 'origin/main:' + fil], cwd=ROT, check=True,
                              capture_output=True).stdout
        if fil == 'sw.js' and nr is not None:
            data = re.sub(rb"const VERSION = '[^']*'", b"const VERSION = 'v%d'" % nr, data, count=1)
        with open(mal, 'wb') as f:
            f.write(data)
    if nr is None:
        with open(os.path.join(WEBB, 'robots.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('User-agent: *\nDisallow: /\n')
        # Eget namn, så att testversionen och den skarpa går att skilja åt när båda är installerade
        for fil, fran, till in [('manifest.json', '"name": "Pensla"', '"name": "Pensla test"'),
                                ('manifest.json', '"short_name": "Pensla"', '"short_name": "Pensla test"'),
                                ('index.html', '<title>Pensla</title>', '<title>Pensla test</title>'),
                                # Galleriet går inte att installera bredvid Pensla test (samma
                                # webbplats), så testversionen har en knapp till det på startskärmen
                                ('index.html', '<button id="start-btn">BÖRJA PENSLA</button>',
                                 '<button id="start-btn">BÖRJA PENSLA</button>\n    <a href="galleri.html" '
                                 'style="position: absolute; right: 24px; bottom: 24px; padding: 14px 28px; '
                                 'font: bold 22px sans-serif; color: #fff; background: #5b6b7b; '
                                 'border-radius: 14px; text-decoration: none;">GALLERI</a>')]:
            with open(os.path.join(WEBB, fil), encoding='utf-8') as f:
                text = f.read()
            if fran not in text:
                sys.exit('Hittar inte %s i %s' % (fran, fil))
            with open(os.path.join(WEBB, fil), 'w', encoding='utf-8', newline='') as f:
                f.write(text.replace(fran, till, 1))


def skarpt():
    git('fetch', '-q', '--tags', 'origin')
    if git('rev-parse', 'HEAD') != git('rev-parse', 'origin/main') or git('status', '--porcelain', '--untracked-files=no'):
        sys.exit('Arbetskopian ska vara lika med origin/main (pusha eller hämta först).')
    nr = slapp()[0] + 1
    bygg(nr)
    try:
        subprocess.run('npx -y wrangler@4 deploy', shell=True, cwd=ROT, check=True)
    finally:
        shutil.rmtree(WEBB, ignore_errors=True)
    tagg = 'slapp-%d' % nr
    git('tag', '-a', tagg, 'origin/main', '-m', 'Släpp v%d på pensla.keiws.com (från %s)' % (nr, version('origin/main')))
    git('push', '-q', 'origin', tagg)
    print('Släppt: v%d på https://pensla.keiws.com (%s, från %s)' % (nr, tagg, version('origin/main')))


def test():
    git('fetch', '-q', 'origin')
    bygg(None)
    try:
        subprocess.run('npx -y wrangler@4 deploy --env test', shell=True, cwd=ROT, check=True)
    finally:
        shutil.rmtree(WEBB, ignore_errors=True)
    print('Testversionen: %s på https://test.pensla.keiws.com (galleriet: '
          'https://test.pensla.keiws.com/galleri.html)' % version('origin/main'))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    skarpt() if '--skarpt' in sys.argv else test() if '--test' in sys.argv else status()
