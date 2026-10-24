// Pensla — alla bilder. Laddas före app.js (och av galleri.html).
//
// Varje bild har ett fast löpnummer `nr` som aldrig återanvänds. Bara
// bilderna vars nummer står i AKTIVA visas i appen (och cachas av sw.js —
// kör `python verktyg/aktiva.py` efter att AKTIVA ändrats). Välj bilder på
// galleri.html. Nummer i BORTTAGNA visas inte i galleriet (och kan inte
// vara aktiva), men bilderna och numren ligger kvar.
//
// `utanFarg: true` = bara konturer, ingen färgbild än (kan inte vara aktiv).
// `fil` = NAMN i bilder/farg/ (NAMN.svg = konturerna, NAMN.jpg = färgbilden).
// `keiws` = var den lilla kompisen keIWs gömmer sig: (x, y) = mitt under
// fötterna, s = skala, `ytor` = punkter i de ytor han syns i (han ritas bara
// där, så det som ligger framför skymmer honom). `gron` och `rod` = samma
// sak för hans gröna och röda kompis (förslag från verktyg/gomstallen.py);
// en bild utan dem har bara keIWs.
const ALLA_BILDER = [
    { nr: 1, namn: 'Traktor', fil: 'traktor', keiws: { x: 420, y: 455, s: 0.32, ytor: [[420, 380]] } }, // i bakre rutan
    { nr: 2, namn: 'Grävare', fil: 'gravare', keiws: { x: 720, y: 462, s: 0.4, ytor: [[720, 400]] } }, // i hyttens fönster
    { nr: 3, namn: 'Sopbil', fil: 'sopbil', keiws: { x: 855, y: 512, s: 0.32, ytor: [[855, 420]] } }, // i hytten, bakom ratten
    { nr: 4, namn: 'Sopbil snett', fil: 'sopbil-snett', keiws: { x: 765, y: 505, s: 0.32, ytor: [[765, 440]] }, gron: { x: 1111, y: 669, s: 0.32, ytor: [[1111, 631]] }, rod: { x: 63, y: 493, s: 0.32, ytor: [[63, 455]] } }, // i vindrutan
    { nr: 5, namn: 'Traktor 2', fil: 'traktor2', keiws: { x: 781, y: 410, s: 0.32, ytor: [[781, 340]] } }, // i bakre rutan
    { nr: 6, namn: 'Flygplan', fil: 'flygplan', keiws: { x: 455, y: 476, s: 0.4, ytor: [[455, 420]] }, gron: { x: 806, y: 671, s: 0.36, ytor: [[806, 628]] }, rod: { x: 162, y: 476, s: 0.4, ytor: [[162, 428]] } }, // i cockpitrutan
    { nr: 7, namn: 'Flygplan 2', fil: 'flygplan2', keiws: { x: 760, y: 450, s: 0.4, ytor: [[760, 400]] } }, // i cockpitrutan
    { nr: 8, namn: 'Helikopter', fil: 'helikopter', keiws: { x: 440, y: 530, s: 0.45, ytor: [[440, 450]] }, gron: { x: 690, y: 636, s: 0.45, ytor: [[690, 582]] }, rod: { x: 138, y: 696, s: 0.45, ytor: [[138, 642]] } }, // i glaskupan
    { nr: 9, namn: 'Helikopter 2', fil: 'helikopter2', keiws: { x: 705, y: 468, s: 0.38, ytor: [[705, 410]] } }, // i fönstret, bredvid stolen
    { nr: 10, namn: 'Tåg', fil: 'tag', keiws: { x: 520, y: 505, s: 0.28, ytor: [[520, 450]] }, gron: { x: 1110, y: 345, s: 0.3, ytor: [[1110, 309]] }, rod: { x: 854, y: 633, s: 0.3, ytor: [[854, 597]] } }, // i lokets fönster
    { nr: 11, namn: 'Tåg 2', fil: 'tag2', keiws: { x: 712, y: 498, s: 0.28, ytor: [[712, 450]] }, gron: { x: 1006, y: 649, s: 0.3, ytor: [[1006, 613]] }, rod: { x: 478, y: 625, s: 0.3, ytor: [[478, 589]] } }, // i lokets fönster
    { nr: 12, namn: 'Båt', fil: 'bat', keiws: { x: 730, y: 488, s: 0.25, ytor: [[730, 445]] } }, // i styrhyttens fönster
    { nr: 13, namn: 'Båt 2', fil: 'bat2', keiws: { x: 605, y: 446, s: 0.2, ytor: [[605, 420]] }, gron: { x: 478, y: 697, s: 0.3, ytor: [[478, 661]] }, rod: { x: 838, y: 729, s: 0.3, ytor: [[838, 693]] } }, // i styrhyttens fönster
    { nr: 14, namn: 'Stort flygplan', fil: 'flygplan-stort', keiws: { x: 880, y: 420, s: 0.25, ytor: [[880, 390]] } }, // i cockpit
    { nr: 15, namn: 'Stort flygplan 2', fil: 'flygplan-stort2', keiws: { x: 300, y: 383, s: 0.22, ytor: [[300, 352]] } }, // i cockpit
    { nr: 16, namn: 'Raket', fil: 'raket', keiws: { x: 670, y: 330, s: 0.25, ytor: [[660, 310]] }, gron: { x: 646, y: 601, s: 0.3, ytor: [[646, 565]] }, rod: { x: 918, y: 225, s: 0.3, ytor: [[918, 189]] } }, // i övre fönstret
    { nr: 17, namn: 'Segelbåt', fil: 'segelbat', keiws: { x: 517, y: 662, s: 0.2, ytor: [[505, 652]] }, gron: { x: 838, y: 689, s: 0.3, ytor: [[838, 653]] }, rod: { x: 254, y: 193, s: 0.3, ytor: [[254, 157]] } }, // i runda fönstret
    { nr: 18, namn: 'Segelbåt 2', fil: 'segelbat2', keiws: { x: 537, y: 682, s: 0.18, ytor: [[527, 672]] } }, // i runda fönstret
    { nr: 19, namn: 'Polisbil', fil: 'polisbil', keiws: { x: 490, y: 570, s: 0.28, ytor: [[490, 520]] } }, // i bakre fönstret
    { nr: 20, namn: 'Polisbil 2', fil: 'polisbil2', keiws: { x: 400, y: 515, s: 0.28, ytor: [[400, 450]] } }, // i bakre fönstret
    { nr: 21, namn: 'Polisbil 3', fil: 'polisbil3', keiws: { x: 425, y: 495, s: 0.3, ytor: [[425, 420]] } }, // i bakre fönstret
    { nr: 22, namn: 'Ambulans', fil: 'ambulans', keiws: { x: 705, y: 495, s: 0.28, ytor: [[705, 400]] } }, // i dörrfönstret
    { nr: 23, namn: 'Ambulans 2', fil: 'ambulans2', keiws: { x: 525, y: 510, s: 0.25, ytor: [[525, 440]] } }, // i sidofönstret
    { nr: 24, namn: 'Betongbil', fil: 'betongbil', keiws: { x: 630, y: 485, s: 0.26, ytor: [[630, 400]] } }, // i hyttfönstret
    { nr: 25, namn: 'Betongbil 2', fil: 'betongbil2', keiws: { x: 505, y: 505, s: 0.3, ytor: [[505, 420]] }, gron: { x: 166, y: 689, s: 0.3, ytor: [[166, 653]] }, rod: { x: 422, y: 217, s: 0.3, ytor: [[422, 181]] } }, // i hyttfönstret
    { nr: 26, namn: 'Kranbil', fil: 'kranbil', keiws: { x: 650, y: 495, s: 0.25, ytor: [[650, 420]] }, gron: { x: 390, y: 553, s: 0.3, ytor: [[390, 517]] }, rod: { x: 62, y: 625, s: 0.3, ytor: [[62, 589]] } }, // i hyttfönstret
    { nr: 27, namn: 'Kranbil 2', fil: 'kranbil2', keiws: { x: 750, y: 515, s: 0.28, ytor: [[750, 440]] }, gron: { x: 94, y: 697, s: 0.3, ytor: [[94, 661]] }, rod: { x: 1142, y: 433, s: 0.3, ytor: [[1142, 397]] } }, // i hyttfönstret
    { nr: 28, namn: 'Buss', fil: 'buss', keiws: { x: 765, y: 560, s: 0.28, ytor: [[765, 470]] }, gron: { x: 510, y: 249, s: 0.3, ytor: [[510, 213]] }, rod: { x: 262, y: 345, s: 0.3, ytor: [[262, 309]] } }, // i ett sidofönster
    { nr: 29, namn: 'Buss 2', fil: 'buss2', keiws: { x: 360, y: 500, s: 0.26, ytor: [[360, 420], [360, 490]] } }, // i främre sidofönstret
    { nr: 30, namn: 'Brandbil', fil: 'brandbil', keiws: { x: 445, y: 620, s: 0.28, ytor: [[440, 550]] } }, // i hyttfönstret
    { nr: 31, namn: 'Brandbil 2', fil: 'brandbil2', keiws: { x: 725, y: 472, s: 0.24, ytor: [[720, 430]] } }, // i hyttfönstret
    { nr: 32, namn: 'Dumper', fil: 'dumper', keiws: { x: 720, y: 505, s: 0.3, ytor: [[720, 420]] }, gron: { x: 470, y: 601, s: 0.3, ytor: [[470, 565]] }, rod: { x: 958, y: 217, s: 0.3, ytor: [[958, 181]] } }, // i hyttfönstret
    { nr: 33, namn: 'Dumper 2', fil: 'dumper2', keiws: { x: 780, y: 450, s: 0.25, ytor: [[780, 390]] }, gron: { x: 446, y: 553, s: 0.3, ytor: [[446, 517]] }, rod: { x: 70, y: 609, s: 0.3, ytor: [[70, 573]] } }, // i hyttfönstret
    { nr: 34, namn: 'Stort flygplan 3', fil: 'flygplan-stort3', keiws: { x: 995, y: 445, s: 0.25, ytor: [[995, 380]] } }, // i terminalfönstret
    { nr: 35, namn: 'Stort flygplan 4', fil: 'flygplan-stort4', keiws: { x: 1075, y: 200, s: 0.25, ytor: [[1075, 160]] } }, // i tornet
    { nr: 36, namn: 'Sopbil 3', fil: 'sopbil3', keiws: { x: 480, y: 495, s: 0.3, ytor: [[480, 400]] }, gron: { x: 1014, y: 785, s: 0.3, ytor: [[1014, 749]] }, rod: { x: 230, y: 569, s: 0.3, ytor: [[230, 533]] } }, // i sidorutan
    { nr: 37, namn: 'Sopbil 4', fil: 'sopbil4', keiws: { x: 505, y: 565, s: 0.3, ytor: [[505, 480]] } }, // i sidorutan
    { nr: 38, namn: 'Flygplan 3', fil: 'flygplan3', keiws: { x: 560, y: 445, s: 0.35, ytor: [[560, 330]] } }, // i cockpit
    { nr: 39, namn: 'Flygplan 4', fil: 'flygplan4', keiws: { x: 500, y: 460, s: 0.35, ytor: [[500, 330]] } }, // i cockpit
    { nr: 40, namn: 'Flygplan 5', fil: 'flygplan5', keiws: { x: 600, y: 465, s: 0.3, ytor: [[600, 390]] } }, // i cockpit
    { nr: 41, namn: 'Grävare 2', fil: 'gravare2', keiws: { x: 825, y: 520, s: 0.32, ytor: [[825, 430]] } }, // i hyttfönstret
    { nr: 42, namn: 'Grävare 3', fil: 'gravare3', keiws: { x: 850, y: 470, s: 0.3, ytor: [[850, 400]] }, gron: { x: 518, y: 353, s: 0.3, ytor: [[518, 317]] }, rod: { x: 302, y: 193, s: 0.3, ytor: [[302, 157]] } }, // i hyttfönstret
    { nr: 43, namn: 'Traktor 3', fil: 'traktor3', keiws: { x: 490, y: 415, s: 0.35, ytor: [[490, 300]] } }, // i mittrutan
    { nr: 44, namn: 'Traktor 4', fil: 'traktor4', keiws: { x: 520, y: 400, s: 0.32, ytor: [[520, 300]] } }, // i dörrutan
    { nr: 45, namn: 'Grävare 4', fil: 'gravare4', keiws: { x: 535, y: 450, s: 0.3, ytor: [[540, 300]] } }, // i hyttfönstret
    { nr: 46, namn: 'Raket 2', fil: 'raket2', keiws: { x: 705, y: 380, s: 0.25, ytor: [[705, 330]] } }, // i stora fönstret
    { nr: 47, namn: 'Raket 3', fil: 'raket3', keiws: { x: 650, y: 330, s: 0.2, ytor: [[650, 300]] } }, // i övre fönstret
    { nr: 48, namn: 'Grävare 5', fil: 'gravare5', keiws: { x: 830, y: 475, s: 0.3, ytor: [[840, 330], [830, 445], [830, 410]] } }, // i hyttfönstret
    { nr: 49, namn: 'Traktor 5', fil: 'traktor5', keiws: { x: 420, y: 330, s: 0.28, ytor: [[420, 260], [420, 310]] } }, // i hyttfönstret
    { nr: 50, namn: 'Flygplan 6', fil: 'flygplan6', keiws: { x: 610, y: 440, s: 0.2, ytor: [[610, 410]] } }, // i ett runt fönster
    { nr: 51, namn: 'Sopbil 5', fil: 'sopbil5', keiws: { x: 375, y: 480, s: 0.28, ytor: [[375, 400]] } }, // i sidorutan
    { nr: 52, namn: 'Stort flygplan 5', fil: 'flygplan-stort5', keiws: { x: 860, y: 172, s: 0.25, ytor: [[850, 140], [875, 140]] } }, // i tornet
    { nr: 53, namn: 'Kranbil 3', fil: 'kranbil3', keiws: { x: 770, y: 380, s: 0.3, ytor: [[770, 310]] } }, // i kranhytten
    { nr: 54, namn: 'Traktor 6', fil: 'traktor6', keiws: { x: 380, y: 320, s: 0.3, ytor: [[380, 250], [380, 300], [405, 305]] } }, // i hyttfönstret
    { nr: 55, namn: 'Betongbil 3', fil: 'betongbil3', keiws: { x: 365, y: 380, s: 0.28, ytor: [[365, 320]] } }, // i sidorutan
    { nr: 56, namn: 'Brandbil 3', fil: 'brandbil3', keiws: { x: 445, y: 460, s: 0.25, ytor: [[445, 400]] } }, // i sidorutan
    { nr: 57, namn: 'Ambulans 3', fil: 'ambulans3', keiws: { x: 370, y: 450, s: 0.3, ytor: [[370, 360]] } }, // i sidofönstret
    { nr: 58, namn: 'Polisbil 4', fil: 'polisbil4', keiws: { x: 280, y: 400, s: 0.28, ytor: [[280, 330]] } }, // i bakre rutan
    { nr: 59, namn: 'Brandbil 4', fil: 'brandbil4', keiws: { x: 530, y: 470, s: 0.22, ytor: [[530, 410]] } }, // i sidorutan
    { nr: 60, namn: 'Räddningsbåt', fil: 'raddningsbat', keiws: { x: 515, y: 430, s: 0.3, ytor: [[515, 370]] } }, // i styrhytten
    { nr: 61, namn: 'Sopbil 6', fil: 'sopbil6', keiws: { x: 425, y: 480, s: 0.28, ytor: [[425, 380]] } }, // i sidorutan
    { nr: 62, namn: 'Helikopter 3', fil: 'helikopter3', keiws: { x: 680, y: 480, s: 0.3, ytor: [[680, 420]] } }, // i kabinfönstret
    { nr: 63, namn: 'Dumper 3', fil: 'dumper3', keiws: { x: 240, y: 400, s: 0.3, ytor: [[240, 320]] } }, // i vindrutan
    { nr: 64, namn: 'Skördetröska', fil: 'skordetroska', keiws: { x: 450, y: 360, s: 0.3, ytor: [[440, 290]] } }, // i hytten
    { nr: 65, namn: 'Dumper 4', fil: 'dumper4', keiws: { x: 1000, y: 400, s: 0.3, ytor: [[1000, 320]] } }, // i vindrutan
    { nr: 66, namn: 'Plogbil', fil: 'plogbil', keiws: { x: 680, y: 380, s: 0.3, ytor: [[680, 300]] } }, // i vindrutan
    { nr: 67, namn: 'Bärgningsbil', fil: 'bargningsbil', keiws: { x: 180, y: 430, s: 0.3, ytor: [[130, 400], [195, 400], [260, 400]] } }, // i vindrutan
    { nr: 68, namn: 'Postbil', fil: 'postbil', keiws: { x: 800, y: 420, s: 0.3, ytor: [[800, 320]] } }, // i vindrutan
    { nr: 69, namn: 'Traktor 7', fil: 'traktor7', keiws: { x: 790, y: 400, s: 0.3, ytor: [[720, 300], [790, 300], [760, 360], [830, 360]] } }, // i hyttfönstret
    { nr: 70, namn: 'Lastfartyg', fil: 'lastfartyg', keiws: { x: 400, y: 250, s: 0.18, ytor: [[400, 230]] } }, // på bryggan
    { nr: 71, namn: 'Sopbil 7', fil: 'sopbil7', keiws: { x: 1060, y: 460, s: 0.3, ytor: [[1060, 380]] } }, // i vindrutan
    { nr: 72, namn: 'Buss 3', fil: 'buss3', keiws: { x: 515, y: 500, s: 0.3, ytor: [[515, 400], [515, 470]] } }, // i ett sidofönster
    { nr: 73, namn: 'Brandbil 5', fil: 'brandbil5', keiws: { x: 950, y: 490, s: 0.3, ytor: [[950, 380]] } }, // i vindrutan
    { nr: 74, namn: 'Polisbil 5', fil: 'polisbil5', keiws: { x: 245, y: 400, s: 0.25, ytor: [[220, 360], [260, 370], [280, 320]] } }, // i bakre rutan
    // Gamla bilder ur arkiv/ (verktyg/arkivbild.py). De utan färgbild
    // (utanFarg) syns i galleriet men kan inte väljas.
    { nr: 75, namn: 'Traktor (arkiv 1)', fil: 'arkiv-01-traktor', utanFarg: true },
    { nr: 76, namn: 'Grävare (arkiv 2)', fil: 'arkiv-02-gravmaskin', utanFarg: true },
    { nr: 77, namn: 'Traktor (arkiv 3)', fil: 'arkiv-03-traktor', keiws: { x: 750, y: 390, s: 0.4, ytor: [[700, 300], [800, 260]] } }, // i bakre rutan
    { nr: 78, namn: 'Grävare (arkiv 4)', fil: 'arkiv-04-gravmaskin', keiws: { x: 580, y: 470, s: 0.35, ytor: [[550, 380]] } }, // i hytten
    { nr: 79, namn: 'Traktor (arkiv 5)', fil: 'arkiv-05-traktor', keiws: { x: 480, y: 430, s: 0.4, ytor: [[460, 300], [540, 300]] } }, // i hytten
    { nr: 80, namn: 'Grävare (arkiv 6)', fil: 'arkiv-06-gravmaskin', keiws: { x: 650, y: 590, s: 0.4, ytor: [[630, 480], [700, 480]] } }, // i hyttens fönster
    { nr: 81, namn: 'Stort flygplan (arkiv 7)', fil: 'arkiv-07-flygplan', keiws: { x: 150, y: 610, s: 0.35, ytor: [[150, 520]] } }, // bakom molnet
    { nr: 82, namn: 'Traktor (arkiv 8)', fil: 'arkiv-08-traktor-snett', keiws: { x: 570, y: 320, s: 0.4, ytor: [[560, 220], [620, 260]] } }, // i hytten
    { nr: 83, namn: 'Grävare (arkiv 9)', fil: 'arkiv-09-gravmaskin', keiws: { x: 650, y: 590, s: 0.4, ytor: [[630, 480], [700, 480]] } }, // i hyttens fönster
    { nr: 84, namn: 'Helikopter (arkiv 10)', fil: 'arkiv-10-helikopter', keiws: { x: 470, y: 450, s: 0.4, ytor: [[470, 380]] } }, // i fönstret
    { nr: 85, namn: 'Grävare (arkiv 11)', fil: 'arkiv-11-gravmaskin-verklig', keiws: { x: 780, y: 520, s: 0.45, ytor: [[720, 400], [800, 380], [760, 470]] } }, // i hytten
    { nr: 86, namn: 'Traktor (arkiv 12)', fil: 'arkiv-12-traktor-verklig', keiws: { x: 600, y: 300, s: 0.45, ytor: [[560, 180], [640, 200]] } }, // i hytten
    { nr: 87, namn: 'Grävare (arkiv 13)', fil: 'arkiv-13-gravmaskin-verklig', keiws: { x: 730, y: 500, s: 0.4, ytor: [[720, 400]] } }, // i hyttens fönster
    { nr: 88, namn: 'Stort flygplan (arkiv 14)', fil: 'arkiv-14-flygplan', utanFarg: true },
    { nr: 89, namn: 'Traktor (arkiv 15)', fil: 'arkiv-15-traktor', utanFarg: true },
    { nr: 90, namn: 'Grävare (arkiv 16)', fil: 'arkiv-16-gravmaskin', utanFarg: true },
    { nr: 91, namn: 'Helikopter (arkiv 17)', fil: 'arkiv-17-helikopter', utanFarg: true },
    { nr: 92, namn: 'Grävare (arkiv 18)', fil: 'arkiv-18-gravmaskin-snett', utanFarg: true },
    { nr: 93, namn: 'Flygplan (arkiv 19)', fil: 'arkiv-19-propellerplan', utanFarg: true },
    { nr: 94, namn: 'Traktor (arkiv 20)', fil: 'arkiv-20-traktor-snett', utanFarg: true },
    { nr: 95, namn: 'Flygplan (arkiv 21)', fil: 'arkiv-21-litet-flygplan', keiws: { x: 470, y: 500, s: 0.35, ytor: [[470, 430]] } }, // i cockpitrutan
    { nr: 96, namn: 'Helikopter (arkiv 22)', fil: 'arkiv-22-helikopter', utanFarg: true },
    { nr: 97, namn: 'Stort flygplan (arkiv 23)', fil: 'arkiv-23-flygplan-snett', utanFarg: true },
    { nr: 98, namn: 'Helikopter (arkiv 24)', fil: 'arkiv-24-helikopter-pa-stigen', keiws: { x: 380, y: 520, s: 0.45, ytor: [[310, 470], [380, 450], [430, 450]] } }, // i glaskupan
    { nr: 99, namn: 'Helikopter (arkiv 25)', fil: 'arkiv-25-helikopter-i-luften', keiws: { x: 595, y: 655, s: 0.3, ytor: [[595, 600]] } }, // i sidofönstret
    { nr: 100, namn: 'Flygplan (arkiv 26)', fil: 'arkiv-26-flygplan-vid-faltet', keiws: { x: 530, y: 560, s: 0.25, ytor: [[525, 530]] } }, // i cockpitrutan
    { nr: 101, namn: 'Brandbil (arkiv 27)', fil: 'arkiv-27-brandbil', utanFarg: true },
    { nr: 102, namn: 'Dumper (arkiv 28)', fil: 'arkiv-28-dumper', utanFarg: true },
    { nr: 103, namn: 'Sopbil (arkiv 29)', fil: 'arkiv-29-sopbil', utanFarg: true },
    { nr: 104, namn: 'Tåg (arkiv 30)', fil: 'arkiv-30-tag', utanFarg: true },
    { nr: 105, namn: 'Båt (arkiv 31)', fil: 'arkiv-31-bat', utanFarg: true },
    // Traktorer mittemellan tecknat och verkligt (2026-10-21): 106–107 Gemini, 108 ChatGPT.
    { nr: 106, namn: 'Traktor 8', fil: 'traktor8', keiws: { x: 650, y: 355, s: 0.45, ytor: [[650, 280], [700, 230]] }, gron: { x: 824, y: 635, s: 0.36, ytor: [[824, 592]] }, rod: { x: 1122, y: 756, s: 0.45, ytor: [[1122, 702]] } }, // i framrutan
    { nr: 107, namn: 'Traktor 9', fil: 'traktor9', keiws: { x: 520, y: 440, s: 0.45, ytor: [[540, 260], [520, 360]] }, gron: { x: 810, y: 552, s: 0.45, ytor: [[810, 498]] }, rod: { x: 138, y: 588, s: 0.45, ytor: [[138, 534]] } }, // i hytten
    { nr: 108, namn: 'Traktor 10', fil: 'traktor10', keiws: { x: 440, y: 410, s: 0.4, ytor: [[400, 260], [460, 330]] } }, // i hytten
    // Betongbilar och ambulanser i mellanstil (2026-10-21).
    { nr: 109, namn: 'Betongbil 4', fil: 'betongbil4', keiws: { x: 885, y: 515, s: 0.35, ytor: [[860, 500], [910, 470], [880, 440]] }, gron: { x: 366, y: 489, s: 0.3, ytor: [[366, 453]] }, rod: { x: 54, y: 561, s: 0.3, ytor: [[54, 525]] } }, // i hyttfönstret
    { nr: 110, namn: 'Betongbil 5', fil: 'betongbil5', keiws: { x: 420, y: 500, s: 0.4, ytor: [[400, 400], [440, 470], [380, 470]] } }, // i sidofönstret
    { nr: 111, namn: 'Ambulans 4', fil: 'ambulans4', keiws: { x: 690, y: 450, s: 0.4, ytor: [[690, 360], [660, 420]] } }, // i framrutan
    { nr: 112, namn: 'Ambulans 5', fil: 'ambulans5', keiws: { x: 600, y: 500, s: 0.4, ytor: [[560, 420], [640, 400], [620, 470]] } }, // i sidofönstret
    { nr: 113, namn: 'Stort flygplan 6', fil: 'flygplan-stort6', keiws: { x: 1245, y: 336, s: 0.35, ytor: [[1250, 300]] }, gron: { x: 400, y: 435, s: 0.35, ytor: [[400, 393]] }, rod: { x: 895, y: 408, s: 0.35, ytor: [[895, 366]] } }, // i terminalfönstret
    { nr: 114, namn: 'Plogbil 2', fil: 'plogbil2', keiws: { x: 835, y: 336, s: 0.42, ytor: [[812, 312]] }, gron: { x: 404, y: 442, s: 0.42, ytor: [[404, 392]] }, rod: { x: 272, y: 156, s: 0.42, ytor: [[272, 106]] } }, // i framrutan
    { nr: 115, namn: 'Plogbil 3', fil: 'plogbil3', keiws: { x: 562, y: 364, s: 0.42, ytor: [[525, 325]] }, gron: { x: 1010, y: 432, s: 0.38, ytor: [[1010, 386]] }, rod: { x: 1152, y: 167, s: 0.42, ytor: [[1152, 117]] } }, // i framrutan
    { nr: 116, namn: 'Bärgningsbil 2', fil: 'bargningsbil2', keiws: { x: 277, y: 413, s: 0.42, ytor: [[225, 350]] }, gron: { x: 1141, y: 167, s: 0.42, ytor: [[1141, 117]] }, rod: { x: 1207, y: 662, s: 0.42, ytor: [[1207, 612]] } }, // i framrutan
    { nr: 117, namn: 'Bärgningsbil 3', fil: 'bargningsbil3', keiws: { x: 1093, y: 406, s: 0.42, ytor: [[1112, 375]] }, gron: { x: 932, y: 178, s: 0.42, ytor: [[932, 128]] }, rod: { x: 170, y: 582, s: 0.38, ytor: [[170, 536]] } }, // i framrutan
];

const BORTTAGNA = [1, 2, 3, 5, 7, 9, 12, 14, 15, 18, 19, 20, 21, 22, 23, 24, 29, 30, 31, 34, 35, 37, 38, 39, 40, 41, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 108, 110, 111, 112];

const AKTIVA = [4, 6, 8, 10, 11, 13, 16, 17, 27, 28, 32, 33, 36, 42, 106, 107, 109, 113, 114, 115, 116, 117];
