// Pensla — alla bilder. Laddas före app.js (och av galleri.html).
//
// Varje bild har ett fast löpnummer `nr` som aldrig återanvänds. Bara
// bilderna vars nummer står i AKTIVA visas i appen (och cachas av sw.js —
// kör `python verktyg/aktiva.py` efter att AKTIVA ändrats). Välj bilder på
// galleri.html.
//
// `fil` = NAMN i bilder/farg/ (NAMN.svg = konturerna, NAMN.jpg = färgbilden).
// `keiws` = var den lilla kompisen keIWs gömmer sig: (x, y) = mitt under
// fötterna, s = skala, `ytor` = punkter i de ytor han syns i (han ritas bara
// där, så det som ligger framför skymmer honom).
const ALLA_BILDER = [
    { nr: 1, namn: 'Traktor', fil: 'traktor', keiws: { x: 420, y: 455, s: 0.32, ytor: [[420, 380]] } }, // i bakre rutan
    { nr: 2, namn: 'Grävare', fil: 'gravare', keiws: { x: 720, y: 462, s: 0.4, ytor: [[720, 400]] } }, // i hyttens fönster
    { nr: 3, namn: 'Sopbil', fil: 'sopbil', keiws: { x: 855, y: 512, s: 0.32, ytor: [[855, 420]] } }, // i hytten, bakom ratten
    { nr: 4, namn: 'Sopbil snett', fil: 'sopbil-snett', keiws: { x: 765, y: 505, s: 0.32, ytor: [[765, 440]] } }, // i vindrutan
    { nr: 5, namn: 'Traktor 2', fil: 'traktor2', keiws: { x: 781, y: 410, s: 0.32, ytor: [[781, 340]] } }, // i bakre rutan
    { nr: 6, namn: 'Flygplan', fil: 'flygplan', keiws: { x: 455, y: 476, s: 0.4, ytor: [[455, 420]] } }, // i cockpitrutan
    { nr: 7, namn: 'Flygplan 2', fil: 'flygplan2', keiws: { x: 760, y: 450, s: 0.4, ytor: [[760, 400]] } }, // i cockpitrutan
    { nr: 8, namn: 'Helikopter', fil: 'helikopter', keiws: { x: 440, y: 530, s: 0.45, ytor: [[440, 450]] } }, // i glaskupan
    { nr: 9, namn: 'Helikopter 2', fil: 'helikopter2', keiws: { x: 705, y: 468, s: 0.38, ytor: [[705, 410]] } }, // i fönstret, bredvid stolen
    { nr: 10, namn: 'Tåg', fil: 'tag', keiws: { x: 520, y: 505, s: 0.28, ytor: [[520, 450]] } }, // i lokets fönster
    { nr: 11, namn: 'Tåg 2', fil: 'tag2', keiws: { x: 712, y: 498, s: 0.28, ytor: [[712, 450]] } }, // i lokets fönster
    { nr: 12, namn: 'Båt', fil: 'bat', keiws: { x: 730, y: 488, s: 0.25, ytor: [[730, 445]] } }, // i styrhyttens fönster
    { nr: 13, namn: 'Båt 2', fil: 'bat2', keiws: { x: 605, y: 446, s: 0.2, ytor: [[605, 420]] } }, // i styrhyttens fönster
    { nr: 14, namn: 'Stort flygplan', fil: 'flygplan-stort', keiws: { x: 880, y: 420, s: 0.25, ytor: [[880, 390]] } }, // i cockpit
    { nr: 15, namn: 'Stort flygplan 2', fil: 'flygplan-stort2', keiws: { x: 300, y: 383, s: 0.22, ytor: [[300, 352]] } }, // i cockpit
    { nr: 16, namn: 'Raket', fil: 'raket', keiws: { x: 670, y: 330, s: 0.25, ytor: [[660, 310]] } }, // i övre fönstret
    { nr: 17, namn: 'Segelbåt', fil: 'segelbat', keiws: { x: 517, y: 662, s: 0.2, ytor: [[505, 652]] } }, // i runda fönstret
    { nr: 18, namn: 'Segelbåt 2', fil: 'segelbat2', keiws: { x: 537, y: 682, s: 0.18, ytor: [[527, 672]] } }, // i runda fönstret
    { nr: 19, namn: 'Polisbil', fil: 'polisbil', keiws: { x: 490, y: 570, s: 0.28, ytor: [[490, 520]] } }, // i bakre fönstret
    { nr: 20, namn: 'Polisbil 2', fil: 'polisbil2', keiws: { x: 400, y: 515, s: 0.28, ytor: [[400, 450]] } }, // i bakre fönstret
    { nr: 21, namn: 'Polisbil 3', fil: 'polisbil3', keiws: { x: 425, y: 495, s: 0.3, ytor: [[425, 420]] } }, // i bakre fönstret
    { nr: 22, namn: 'Ambulans', fil: 'ambulans', keiws: { x: 705, y: 495, s: 0.28, ytor: [[705, 400]] } }, // i dörrfönstret
    { nr: 23, namn: 'Ambulans 2', fil: 'ambulans2', keiws: { x: 525, y: 510, s: 0.25, ytor: [[525, 440]] } }, // i sidofönstret
    { nr: 24, namn: 'Betongbil', fil: 'betongbil', keiws: { x: 630, y: 485, s: 0.26, ytor: [[630, 400]] } }, // i hyttfönstret
    { nr: 25, namn: 'Betongbil 2', fil: 'betongbil2', keiws: { x: 505, y: 505, s: 0.3, ytor: [[505, 420]] } }, // i hyttfönstret
    { nr: 26, namn: 'Kranbil', fil: 'kranbil', keiws: { x: 650, y: 495, s: 0.25, ytor: [[650, 420]] } }, // i hyttfönstret
    { nr: 27, namn: 'Kranbil 2', fil: 'kranbil2', keiws: { x: 750, y: 515, s: 0.28, ytor: [[750, 440]] } }, // i hyttfönstret
    { nr: 28, namn: 'Buss', fil: 'buss', keiws: { x: 765, y: 560, s: 0.28, ytor: [[765, 470]] } }, // i ett sidofönster
    { nr: 29, namn: 'Buss 2', fil: 'buss2', keiws: { x: 360, y: 500, s: 0.26, ytor: [[360, 420], [360, 490]] } }, // i främre sidofönstret
    { nr: 30, namn: 'Brandbil', fil: 'brandbil', keiws: { x: 445, y: 620, s: 0.28, ytor: [[440, 550]] } }, // i hyttfönstret
    { nr: 31, namn: 'Brandbil 2', fil: 'brandbil2', keiws: { x: 725, y: 472, s: 0.24, ytor: [[720, 430]] } }, // i hyttfönstret
    { nr: 32, namn: 'Dumper', fil: 'dumper', keiws: { x: 720, y: 505, s: 0.3, ytor: [[720, 420]] } }, // i hyttfönstret
    { nr: 33, namn: 'Dumper 2', fil: 'dumper2', keiws: { x: 780, y: 450, s: 0.25, ytor: [[780, 390]] } }, // i hyttfönstret
    { nr: 34, namn: 'Stort flygplan 3', fil: 'flygplan-stort3', keiws: { x: 995, y: 445, s: 0.25, ytor: [[995, 380]] } }, // i terminalfönstret
    { nr: 35, namn: 'Stort flygplan 4', fil: 'flygplan-stort4', keiws: { x: 1075, y: 200, s: 0.25, ytor: [[1075, 160]] } }, // i tornet
    { nr: 36, namn: 'Sopbil 3', fil: 'sopbil3', keiws: { x: 480, y: 495, s: 0.3, ytor: [[480, 400]] } }, // i sidorutan
    { nr: 37, namn: 'Sopbil 4', fil: 'sopbil4', keiws: { x: 505, y: 565, s: 0.3, ytor: [[505, 480]] } }, // i sidorutan
    { nr: 38, namn: 'Flygplan 3', fil: 'flygplan3', keiws: { x: 560, y: 445, s: 0.35, ytor: [[560, 330]] } }, // i cockpit
    { nr: 39, namn: 'Flygplan 4', fil: 'flygplan4', keiws: { x: 500, y: 460, s: 0.35, ytor: [[500, 330]] } }, // i cockpit
    { nr: 40, namn: 'Flygplan 5', fil: 'flygplan5', keiws: { x: 600, y: 465, s: 0.3, ytor: [[600, 390]] } }, // i cockpit
    { nr: 41, namn: 'Grävare 2', fil: 'gravare2', keiws: { x: 825, y: 520, s: 0.32, ytor: [[825, 430]] } }, // i hyttfönstret
    { nr: 42, namn: 'Grävare 3', fil: 'gravare3', keiws: { x: 850, y: 470, s: 0.3, ytor: [[850, 400]] } }, // i hyttfönstret
    { nr: 43, namn: 'Traktor 3', fil: 'traktor3', keiws: { x: 490, y: 415, s: 0.35, ytor: [[490, 300]] } }, // i mittrutan
    { nr: 44, namn: 'Traktor 4', fil: 'traktor4', keiws: { x: 520, y: 400, s: 0.32, ytor: [[520, 300]] } }, // i dörrutan
    { nr: 45, namn: 'Grävare 4', fil: 'gravare4', keiws: { x: 535, y: 450, s: 0.3, ytor: [[540, 300]] } }, // i hyttfönstret
    { nr: 46, namn: 'Raket 2', fil: 'raket2', keiws: { x: 705, y: 380, s: 0.25, ytor: [[705, 330]] } }, // i stora fönstret
    { nr: 47, namn: 'Raket 3', fil: 'raket3', keiws: { x: 650, y: 330, s: 0.2, ytor: [[650, 300]] } }, // i övre fönstret
];

const AKTIVA = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33
];
