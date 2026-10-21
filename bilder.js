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
    { nr: 48, namn: 'Grävare 5', fil: 'gravare5', keiws: { x: 830, y: 475, s: 0.3, ytor: [[840, 330]] } }, // i hyttfönstret
    { nr: 49, namn: 'Traktor 5', fil: 'traktor5', keiws: { x: 420, y: 330, s: 0.28, ytor: [[420, 260]] } }, // i hyttfönstret
    { nr: 50, namn: 'Flygplan 6', fil: 'flygplan6', keiws: { x: 610, y: 440, s: 0.2, ytor: [[610, 410]] } }, // i ett runt fönster
    { nr: 51, namn: 'Sopbil 5', fil: 'sopbil5', keiws: { x: 375, y: 480, s: 0.28, ytor: [[375, 400]] } }, // i sidorutan
    { nr: 52, namn: 'Stort flygplan 5', fil: 'flygplan-stort5', keiws: { x: 860, y: 172, s: 0.25, ytor: [[860, 140]] } }, // i tornet
    { nr: 53, namn: 'Kranbil 3', fil: 'kranbil3', keiws: { x: 770, y: 380, s: 0.3, ytor: [[770, 310]] } }, // i kranhytten
    { nr: 54, namn: 'Traktor 6', fil: 'traktor6', keiws: { x: 380, y: 320, s: 0.3, ytor: [[380, 250]] } }, // i hyttfönstret
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
    { nr: 72, namn: 'Buss 3', fil: 'buss3', keiws: { x: 515, y: 500, s: 0.3, ytor: [[515, 400]] } }, // i ett sidofönster
    { nr: 73, namn: 'Brandbil 5', fil: 'brandbil5', keiws: { x: 950, y: 490, s: 0.3, ytor: [[950, 380]] } }, // i vindrutan
    { nr: 74, namn: 'Polisbil 5', fil: 'polisbil5', keiws: { x: 245, y: 400, s: 0.25, ytor: [[220, 360], [260, 370], [280, 320]] } }, // i bakre rutan
];

const AKTIVA = [2, 4, 5, 6, 8, 10, 11, 12, 13, 14, 16, 17, 18, 20, 22, 25, 27, 28, 31, 32, 33, 35, 37, 38, 41, 46, 48, 49, 50, 52, 53, 55, 57, 60, 61, 62, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74];
