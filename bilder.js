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
    { nr: 4, namn: 'Sopbil snett', fil: 'sopbil-snett', keiws: { x: 765, y: 505, s: 0.32, ytor: [[765, 440]] }, gron: { x: 633, y: 326, s: 0.5, ytor: [[633, 264]] }, rod: { x: 1106, y: 392, s: 0.5, ytor: [[1106, 330]] } }, // i vindrutan
    { nr: 5, namn: 'Traktor 2', fil: 'traktor2', keiws: { x: 781, y: 410, s: 0.32, ytor: [[781, 340]] } }, // i bakre rutan
    { nr: 6, namn: 'Flygplan', fil: 'flygplan', keiws: { x: 479, y: 491, s: 0.5, ytor: [[479, 429]] }, gron: { x: 314, y: 469, s: 0.5, ytor: [[314, 407]] }, rod: { x: 835, y: 468, s: 0.42, ytor: [[835, 415]] } },
    { nr: 7, namn: 'Flygplan 2', fil: 'flygplan2', keiws: { x: 732, y: 469, s: 0.5, ytor: [[732, 407]] }, gron: { x: 688, y: 315, s: 0.5, ytor: [[688, 253]] }, rod: { x: 226, y: 348, s: 0.5, ytor: [[226, 286]] } },
    { nr: 8, namn: 'Helikopter', fil: 'helikopter', keiws: { x: 424, y: 557, s: 0.5, ytor: [[424, 495]] }, gron: { x: 446, y: 227, s: 0.5, ytor: [[446, 165]] }, rod: { x: 666, y: 513, s: 0.5, ytor: [[666, 451]] } },
    { nr: 9, namn: 'Helikopter 2', fil: 'helikopter2', keiws: { x: 705, y: 468, s: 0.38, ytor: [[705, 410]] }, gron: { x: 798, y: 238, s: 0.5, ytor: [[798, 176]] }, rod: { x: 864, y: 557, s: 0.5, ytor: [[864, 495]] } }, // i fönstret, bredvid stolen
    { nr: 10, namn: 'Tåg', fil: 'tag', keiws: { x: 520, y: 505, s: 0.28, ytor: [[520, 450]] }, gron: { x: 1051, y: 304, s: 0.5, ytor: [[1051, 242]] }, rod: { x: 798, y: 447, s: 0.5, ytor: [[798, 385]] } }, // i lokets fönster
    { nr: 11, namn: 'Tåg 2', fil: 'tag2', keiws: { x: 712, y: 498, s: 0.28, ytor: [[712, 450]] }, gron: { x: 699, y: 348, s: 0.5, ytor: [[699, 286]] }, rod: { x: 178, y: 396, s: 0.42, ytor: [[178, 343]] } }, // i lokets fönster
    { nr: 12, namn: 'Båt', fil: 'bat', keiws: { x: 730, y: 488, s: 0.25, ytor: [[730, 445]] }, gron: { x: 655, y: 359, s: 0.5, ytor: [[655, 297]] }, rod: { x: 292, y: 403, s: 0.5, ytor: [[292, 341]] } }, // i styrhyttens fönster
    { nr: 13, namn: 'Båt 2', fil: 'bat2', keiws: { x: 718, y: 477, s: 0.42, ytor: [[718, 424]] }, gron: { x: 600, y: 326, s: 0.5, ytor: [[600, 264]] }, rod: { x: 358, y: 535, s: 0.5, ytor: [[358, 473]] } },
    { nr: 14, namn: 'Stort flygplan', fil: 'flygplan-stort', keiws: { x: 853, y: 458, s: 0.5, ytor: [[853, 396]] }, gron: { x: 666, y: 282, s: 0.5, ytor: [[666, 220]] }, rod: { x: 325, y: 194, s: 0.5, ytor: [[325, 132]] } },
    { nr: 15, namn: 'Stort flygplan 2', fil: 'flygplan-stort2', keiws: { x: 534, y: 260, s: 0.5, ytor: [[534, 198]] }, gron: { x: 930, y: 227, s: 0.5, ytor: [[930, 165]] }, rod: { x: 300, y: 305, s: 0.45, ytor: [[300, 249]] } },
    { nr: 16, namn: 'Raket', fil: 'raket', keiws: { x: 997, y: 531, s: 0.42, ytor: [[997, 478]] }, gron: { x: 567, y: 128, s: 0.5, ytor: [[567, 66]] }, rod: { x: 997, y: 531, s: 0.42, ytor: [[997, 478]] } },
    { nr: 17, namn: 'Segelbåt', fil: 'segelbat', keiws: { x: 1150, y: 360, s: 0.42, ytor: [[1150, 307]] }, gron: { x: 391, y: 541, s: 0.36, ytor: [[391, 497]] }, rod: { x: 567, y: 205, s: 0.5, ytor: [[567, 143]] } },
    { nr: 18, namn: 'Segelbåt 2', fil: 'segelbat2', keiws: { x: 853, y: 594, s: 0.42, ytor: [[853, 541]] }, gron: { x: 611, y: 227, s: 0.5, ytor: [[611, 165]] }, rod: { x: 765, y: 502, s: 0.5, ytor: [[765, 440]] } },
    { nr: 19, namn: 'Polisbil', fil: 'polisbil', keiws: { x: 622, y: 579, s: 0.5, ytor: [[622, 517]] }, gron: { x: 292, y: 315, s: 0.5, ytor: [[292, 253]] }, rod: { x: 930, y: 293, s: 0.5, ytor: [[930, 231]] } },
    { nr: 20, namn: 'Polisbil 2', fil: 'polisbil2', keiws: { x: 402, y: 535, s: 0.5, ytor: [[402, 473]] }, gron: { x: 457, y: 337, s: 0.5, ytor: [[457, 275]] }, rod: { x: 1007, y: 315, s: 0.5, ytor: [[1007, 253]] } },
    { nr: 21, namn: 'Polisbil 3', fil: 'polisbil3', keiws: { x: 402, y: 491, s: 0.5, ytor: [[402, 429]] }, gron: { x: 1071, y: 261, s: 0.36, ytor: [[1071, 217]] }, rod: { x: 622, y: 502, s: 0.5, ytor: [[622, 440]] } },
    { nr: 22, namn: 'Ambulans', fil: 'ambulans', keiws: { x: 655, y: 468, s: 0.42, ytor: [[655, 415]] }, gron: { x: 484, y: 207, s: 0.42, ytor: [[484, 154]] }, rod: { x: 435, y: 502, s: 0.5, ytor: [[435, 440]] } },
    { nr: 23, namn: 'Ambulans 2', fil: 'ambulans2', keiws: { x: 820, y: 513, s: 0.5, ytor: [[820, 451]] }, gron: { x: 369, y: 326, s: 0.5, ytor: [[369, 264]] }, rod: { x: 853, y: 271, s: 0.5, ytor: [[853, 209]] } },
    { nr: 24, namn: 'Betongbil', fil: 'betongbil', keiws: { x: 630, y: 485, s: 0.26, ytor: [[630, 400]] } }, // i hyttfönstret
    { nr: 25, namn: 'Betongbil 2', fil: 'betongbil2', keiws: { x: 523, y: 513, s: 0.5, ytor: [[523, 451]] }, gron: { x: 413, y: 315, s: 0.5, ytor: [[413, 253]] }, rod: { x: 963, y: 271, s: 0.5, ytor: [[963, 209]] } },
    { nr: 26, namn: 'Kranbil', fil: 'kranbil', keiws: { x: 842, y: 491, s: 0.5, ytor: [[842, 429]] }, gron: { x: 556, y: 216, s: 0.5, ytor: [[556, 154]] }, rod: { x: 347, y: 337, s: 0.5, ytor: [[347, 275]] } },
    { nr: 27, namn: 'Kranbil 2', fil: 'kranbil2', keiws: { x: 743, y: 524, s: 0.5, ytor: [[743, 462]] }, gron: { x: 567, y: 216, s: 0.5, ytor: [[567, 154]] }, rod: { x: 886, y: 359, s: 0.5, ytor: [[886, 297]] } },
    { nr: 28, namn: 'Buss', fil: 'buss', keiws: { x: 765, y: 568, s: 0.5, ytor: [[765, 506]] }, gron: { x: 776, y: 315, s: 0.5, ytor: [[776, 253]] }, rod: { x: 1073, y: 183, s: 0.5, ytor: [[1073, 121]] } },
    { nr: 29, namn: 'Buss 2', fil: 'buss2', keiws: { x: 523, y: 315, s: 0.5, ytor: [[523, 253]] }, gron: { x: 43, y: 387, s: 0.42, ytor: [[43, 334]] }, rod: { x: 1062, y: 436, s: 0.5, ytor: [[1062, 374]] } },
    { nr: 30, namn: 'Brandbil', fil: 'brandbil', keiws: { x: 600, y: 634, s: 0.5, ytor: [[600, 572]] }, gron: { x: 457, y: 337, s: 0.5, ytor: [[457, 275]] }, rod: { x: 908, y: 249, s: 0.5, ytor: [[908, 187]] } },
    { nr: 31, namn: 'Brandbil 2', fil: 'brandbil2', keiws: { x: 908, y: 491, s: 0.5, ytor: [[908, 429]] }, gron: { x: 644, y: 249, s: 0.5, ytor: [[644, 187]] }, rod: { x: 424, y: 128, s: 0.5, ytor: [[424, 66]] } },
    { nr: 32, namn: 'Dumper', fil: 'dumper', keiws: { x: 710, y: 513, s: 0.5, ytor: [[710, 451]] }, gron: { x: 787, y: 260, s: 0.5, ytor: [[787, 198]] }, rod: { x: 490, y: 117, s: 0.5, ytor: [[490, 55]] } },
    { nr: 33, namn: 'Dumper 2', fil: 'dumper2', keiws: { x: 776, y: 458, s: 0.5, ytor: [[776, 396]] }, gron: { x: 655, y: 249, s: 0.5, ytor: [[655, 187]] }, rod: { x: 853, y: 315, s: 0.5, ytor: [[853, 253]] } },
    { nr: 34, namn: 'Stort flygplan 3', fil: 'flygplan-stort3', keiws: { x: 996, y: 447, s: 0.5, ytor: [[996, 385]] }, gron: { x: 853, y: 293, s: 0.5, ytor: [[853, 231]] }, rod: { x: 754, y: 150, s: 0.5, ytor: [[754, 88]] } },
    { nr: 35, namn: 'Stort flygplan 4', fil: 'flygplan-stort4', keiws: { x: 1051, y: 128, s: 0.5, ytor: [[1051, 66]] }, gron: { x: 205, y: 270, s: 0.42, ytor: [[205, 217]] }, rod: { x: 952, y: 359, s: 0.5, ytor: [[952, 297]] } },
    { nr: 36, namn: 'Sopbil 3', fil: 'sopbil3', keiws: { x: 479, y: 491, s: 0.5, ytor: [[479, 429]] }, gron: { x: 501, y: 227, s: 0.5, ytor: [[501, 165]] }, rod: { x: 1073, y: 260, s: 0.5, ytor: [[1073, 198]] } },
    { nr: 37, namn: 'Sopbil 4', fil: 'sopbil4', keiws: { x: 523, y: 579, s: 0.5, ytor: [[523, 517]] }, gron: { x: 567, y: 370, s: 0.5, ytor: [[567, 308]] }, rod: { x: 1128, y: 359, s: 0.5, ytor: [[1128, 297]] } },
    { nr: 38, namn: 'Flygplan 3', fil: 'flygplan3', keiws: { x: 545, y: 447, s: 0.5, ytor: [[545, 385]] }, gron: { x: 534, y: 260, s: 0.5, ytor: [[534, 198]] }, rod: { x: 369, y: 359, s: 0.5, ytor: [[369, 297]] } },
    { nr: 39, namn: 'Flygplan 4', fil: 'flygplan4', keiws: { x: 534, y: 469, s: 0.5, ytor: [[534, 407]] }, gron: { x: 446, y: 271, s: 0.5, ytor: [[446, 209]] }, rod: { x: 1084, y: 304, s: 0.5, ytor: [[1084, 242]] } },
    { nr: 40, namn: 'Flygplan 5', fil: 'flygplan5', keiws: { x: 600, y: 458, s: 0.5, ytor: [[600, 396]] }, gron: { x: 688, y: 337, s: 0.5, ytor: [[688, 275]] }, rod: { x: 897, y: 381, s: 0.5, ytor: [[897, 319]] } },
    { nr: 41, namn: 'Grävare 2', fil: 'gravare2', keiws: { x: 677, y: 535, s: 0.5, ytor: [[677, 473]] }, gron: { x: 545, y: 315, s: 0.5, ytor: [[545, 253]] }, rod: { x: 864, y: 315, s: 0.5, ytor: [[864, 253]] } },
    { nr: 42, namn: 'Grävare 3', fil: 'gravare3', keiws: { x: 699, y: 502, s: 0.5, ytor: [[699, 440]] }, gron: { x: 732, y: 293, s: 0.5, ytor: [[732, 231]] }, rod: { x: 567, y: 260, s: 0.5, ytor: [[567, 198]] } },
    { nr: 43, namn: 'Traktor 3', fil: 'traktor3', keiws: { x: 512, y: 414, s: 0.5, ytor: [[512, 352]] }, gron: { x: 468, y: 150, s: 0.5, ytor: [[468, 88]] }, rod: { x: 930, y: 304, s: 0.5, ytor: [[930, 242]] } },
    { nr: 44, namn: 'Traktor 4', fil: 'traktor4', keiws: { x: 520, y: 400, s: 0.32, ytor: [[520, 300]] } }, // i dörrutan
    { nr: 45, namn: 'Grävare 4', fil: 'gravare4', keiws: { x: 535, y: 450, s: 0.3, ytor: [[540, 300]] } }, // i hyttfönstret
    { nr: 46, namn: 'Raket 2', fil: 'raket2', keiws: { x: 699, y: 414, s: 0.5, ytor: [[699, 352]] }, gron: { x: 710, y: 106, s: 0.5, ytor: [[710, 44]] }, rod: { x: 127, y: 436, s: 0.5, ytor: [[127, 374]] } },
    { nr: 47, namn: 'Raket 3', fil: 'raket3', keiws: { x: 140, y: 455, s: 0.5, ytor: [[140, 393]] }, gron: { x: 622, y: 139, s: 0.5, ytor: [[622, 77]] }, rod: { x: 1040, y: 370, s: 0.36, ytor: [[1040, 325]] } },
    { nr: 48, namn: 'Grävare 5', fil: 'gravare5', keiws: { x: 830, y: 475, s: 0.3, ytor: [[840, 330], [830, 445], [830, 410]] } }, // i hyttfönstret
    { nr: 49, namn: 'Traktor 5', fil: 'traktor5', keiws: { x: 420, y: 330, s: 0.28, ytor: [[420, 260], [420, 310]] } }, // i hyttfönstret
    { nr: 50, namn: 'Flygplan 6', fil: 'flygplan6', keiws: { x: 732, y: 458, s: 0.5, ytor: [[732, 396]] }, gron: { x: 292, y: 205, s: 0.5, ytor: [[292, 143]] }, rod: { x: 622, y: 293, s: 0.5, ytor: [[622, 231]] } }, // i cockpit
    { nr: 51, namn: 'Sopbil 5', fil: 'sopbil5', keiws: { x: 375, y: 480, s: 0.28, ytor: [[375, 400]] } }, // i sidorutan
    { nr: 52, namn: 'Stort flygplan 5', fil: 'flygplan-stort5', keiws: { x: 809, y: 106, s: 0.5, ytor: [[809, 44]] }, gron: { x: 124, y: 477, s: 0.42, ytor: [[124, 424]] }, rod: { x: 963, y: 403, s: 0.5, ytor: [[963, 341]] } },
    { nr: 53, namn: 'Kranbil 3', fil: 'kranbil3', keiws: { x: 770, y: 380, s: 0.3, ytor: [[770, 310]] } }, // i kranhytten
    { nr: 54, namn: 'Traktor 6', fil: 'traktor6', keiws: { x: 736, y: 144, s: 0.42, ytor: [[736, 91]] }, gron: { x: 589, y: 128, s: 0.5, ytor: [[589, 66]] }, rod: { x: 880, y: 405, s: 0.42, ytor: [[880, 352]] } },
    { nr: 55, namn: 'Betongbil 3', fil: 'betongbil3', keiws: { x: 365, y: 380, s: 0.28, ytor: [[365, 320]] } }, // i sidorutan
    { nr: 56, namn: 'Brandbil 3', fil: 'brandbil3', keiws: { x: 445, y: 460, s: 0.25, ytor: [[445, 400]] } }, // i sidorutan
    { nr: 57, namn: 'Ambulans 3', fil: 'ambulans3', keiws: { x: 370, y: 450, s: 0.3, ytor: [[370, 360]] } }, // i sidofönstret
    { nr: 58, namn: 'Polisbil 4', fil: 'polisbil4', keiws: { x: 280, y: 400, s: 0.28, ytor: [[280, 330]] } }, // i bakre rutan
    { nr: 59, namn: 'Brandbil 4', fil: 'brandbil4', keiws: { x: 530, y: 470, s: 0.22, ytor: [[530, 410]] } }, // i sidorutan
    { nr: 60, namn: 'Räddningsbåt', fil: 'raddningsbat', keiws: { x: 515, y: 430, s: 0.3, ytor: [[515, 370]] } }, // i styrhytten
    { nr: 61, namn: 'Sopbil 6', fil: 'sopbil6', keiws: { x: 425, y: 480, s: 0.28, ytor: [[425, 380]] } }, // i sidorutan
    { nr: 62, namn: 'Helikopter 3', fil: 'helikopter3', keiws: { x: 680, y: 480, s: 0.3, ytor: [[680, 420]] } }, // i kabinfönstret
    { nr: 63, namn: 'Dumper 3', fil: 'dumper3', keiws: { x: 240, y: 400, s: 0.3, ytor: [[240, 320]] } }, // i vindrutan
    { nr: 64, namn: 'Skördetröska', fil: 'skordetroska', keiws: { x: 941, y: 216, s: 0.5, ytor: [[941, 154]] }, gron: { x: 677, y: 106, s: 0.5, ytor: [[677, 44]] }, rod: { x: 314, y: 216, s: 0.5, ytor: [[314, 154]] } },
    { nr: 65, namn: 'Dumper 4', fil: 'dumper4', keiws: { x: 1000, y: 400, s: 0.3, ytor: [[1000, 320]] } }, // i vindrutan
    { nr: 66, namn: 'Plogbil', fil: 'plogbil', keiws: { x: 680, y: 380, s: 0.3, ytor: [[680, 300]] } }, // i vindrutan
    { nr: 67, namn: 'Bärgningsbil', fil: 'bargningsbil', keiws: { x: 180, y: 430, s: 0.3, ytor: [[130, 400], [195, 400], [260, 400]] } }, // i vindrutan
    { nr: 68, namn: 'Postbil', fil: 'postbil', keiws: { x: 800, y: 420, s: 0.3, ytor: [[800, 320]] } }, // i vindrutan
    { nr: 69, namn: 'Traktor 7', fil: 'traktor7', keiws: { x: 50, y: 381, s: 0.5, ytor: [[50, 319]] }, gron: { x: 270, y: 249, s: 0.5, ytor: [[270, 187]] }, rod: { x: 864, y: 216, s: 0.5, ytor: [[864, 154]] } },
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
    { nr: 106, namn: 'Traktor 8', fil: 'traktor8', keiws: { x: 650, y: 355, s: 0.45, ytor: [[650, 280], [700, 230]] }, gron: { x: 204, y: 304, s: 0.5, ytor: [[204, 242]] }, rod: { x: 622, y: 117, s: 0.5, ytor: [[622, 55]] } }, // i framrutan
    { nr: 107, namn: 'Traktor 9', fil: 'traktor9', keiws: { x: 520, y: 440, s: 0.45, ytor: [[540, 260], [520, 360]] }, gron: { x: 83, y: 249, s: 0.5, ytor: [[83, 187]] }, rod: { x: 523, y: 150, s: 0.5, ytor: [[523, 88]] } }, // i hytten
    { nr: 108, namn: 'Traktor 10', fil: 'traktor10', keiws: { x: 440, y: 410, s: 0.4, ytor: [[400, 260], [460, 330]] }, gron: { x: 457, y: 183, s: 0.5, ytor: [[457, 121]] }, rod: { x: 875, y: 315, s: 0.5, ytor: [[875, 253]] } }, // i hytten
    // Betongbilar och ambulanser i mellanstil (2026-10-21).
    { nr: 109, namn: 'Betongbil 4', fil: 'betongbil4', keiws: { x: 941, y: 403, s: 0.5, ytor: [[941, 341]] }, gron: { x: 402, y: 304, s: 0.5, ytor: [[402, 242]] }, rod: { x: 72, y: 458, s: 0.5, ytor: [[72, 396]] } },
    { nr: 110, namn: 'Betongbil 5', fil: 'betongbil5', keiws: { x: 420, y: 500, s: 0.4, ytor: [[400, 400], [440, 470], [380, 470]] } }, // i sidofönstret
    { nr: 111, namn: 'Ambulans 4', fil: 'ambulans4', keiws: { x: 690, y: 450, s: 0.4, ytor: [[690, 360], [660, 420]] }, gron: { x: 600, y: 238, s: 0.5, ytor: [[600, 176]] }, rod: { x: 50, y: 315, s: 0.5, ytor: [[50, 253]] } }, // i framrutan
    { nr: 112, namn: 'Ambulans 5', fil: 'ambulans5', keiws: { x: 600, y: 500, s: 0.4, ytor: [[560, 420], [640, 400], [620, 470]] } }, // i sidofönstret
    { nr: 113, namn: 'Stort flygplan 6', fil: 'flygplan-stort6', keiws: { x: 1018, y: 315, s: 0.5, ytor: [[1018, 253]] }, gron: { x: 732, y: 293, s: 0.5, ytor: [[732, 231]] }, rod: { x: 895, y: 405, s: 0.36, ytor: [[895, 361]] } },
    { nr: 114, namn: 'Plogbil 2', fil: 'plogbil2', keiws: { x: 835, y: 336, s: 0.42, ytor: [[812, 312]] }, gron: { x: 864, y: 238, s: 0.5, ytor: [[864, 176]] }, rod: { x: 997, y: 297, s: 0.42, ytor: [[997, 244]] } }, // i framrutan
    { nr: 115, namn: 'Plogbil 3', fil: 'plogbil3', keiws: { x: 562, y: 364, s: 0.42, ytor: [[525, 325]] }, gron: { x: 589, y: 227, s: 0.5, ytor: [[589, 165]] }, rod: { x: 996, y: 271, s: 0.5, ytor: [[996, 209]] } }, // i framrutan
    { nr: 116, namn: 'Bärgningsbil 2', fil: 'bargningsbil2', keiws: { x: 277, y: 413, s: 0.42, ytor: [[225, 350]] }, gron: { x: 490, y: 139, s: 0.5, ytor: [[490, 77]] }, rod: { x: 930, y: 381, s: 0.5, ytor: [[930, 319]] } }, // i framrutan
    { nr: 117, namn: 'Bärgningsbil 3', fil: 'bargningsbil3', keiws: { x: 1093, y: 406, s: 0.42, ytor: [[1112, 375]] }, gron: { x: 391, y: 238, s: 0.5, ytor: [[391, 176]] }, rod: { x: 699, y: 414, s: 0.5, ytor: [[699, 352]] } }, // i framrutan
    { nr: 118, namn: 'Traktor 11', fil: 'traktor11', keiws: { x: 939, y: 416, s: 0.5, ytor: [[939, 356]] }, gron: { x: 808, y: 261, s: 0.42, ytor: [[808, 208]] }, rod: { x: 281, y: 513, s: 0.5, ytor: [[281, 451]] } }, // i framrutan
    { nr: 119, namn: 'Traktor 12', fil: 'traktor12', keiws: { x: 1097, y: 419, s: 0.5, ytor: [[1097, 359]] }, gron: { x: 545, y: 260, s: 0.5, ytor: [[545, 198]] }, rod: { x: 886, y: 282, s: 0.5, ytor: [[886, 220]] } }, // i framrutan
    { nr: 120, namn: 'Traktor 13', fil: 'traktor13', keiws: { x: 564, y: 371, s: 0.45, ytor: [[564, 317]] }, gron: { x: 699, y: 238, s: 0.5, ytor: [[699, 176]] }, rod: { x: 519, y: 269, s: 0.36, ytor: [[519, 225]] } }, // i framrutan
    { nr: 121, namn: 'Hjullastare', fil: 'hjullastare', keiws: { x: 728, y: 410, s: 0.5, ytor: [[728, 350]] }, gron: { x: 512, y: 227, s: 0.5, ytor: [[512, 165]] }, rod: { x: 963, y: 282, s: 0.5, ytor: [[963, 220]] } }, // i framrutan
    { nr: 122, namn: 'Hjullastare 2', fil: 'hjullastare2', keiws: { x: 608, y: 421, s: 0.5, ytor: [[608, 361]] }, gron: { x: 600, y: 282, s: 0.5, ytor: [[600, 220]] }, rod: { x: 809, y: 381, s: 0.5, ytor: [[809, 319]] } }, // i framrutan
    { nr: 123, namn: 'Hjullastare 3', fil: 'hjullastare3', keiws: { x: 551, y: 384, s: 0.4, ytor: [[551, 336]] }, gron: { x: 391, y: 271, s: 0.5, ytor: [[391, 209]] }, rod: { x: 765, y: 370, s: 0.5, ytor: [[765, 308]] } }, // i framrutan
    { nr: 124, namn: 'Hjullastare 4', fil: 'hjullastare4', keiws: { x: 763, y: 402, s: 0.5, ytor: [[763, 342]] }, gron: { x: 754, y: 279, s: 0.42, ytor: [[754, 226]] }, rod: { x: 534, y: 337, s: 0.5, ytor: [[534, 275]] } }, // i framrutan
    { nr: 125, namn: 'Brandbil 6', fil: 'brandbil6', keiws: { x: 435, y: 524, s: 0.5, ytor: [[435, 462]] }, gron: { x: 765, y: 315, s: 0.5, ytor: [[765, 253]] }, rod: { x: 204, y: 271, s: 0.5, ytor: [[204, 209]] } }, // i framrutan
    { nr: 126, namn: 'Tankbil', fil: 'tankbil', keiws: { x: 490, y: 535, s: 0.5, ytor: [[490, 473]] }, gron: { x: 545, y: 271, s: 0.5, ytor: [[545, 209]] }, rod: { x: 336, y: 348, s: 0.5, ytor: [[336, 286]] } }, // i framrutan
    { nr: 127, namn: 'Tankbil 2', fil: 'tankbil2', keiws: { x: 400, y: 525, s: 0.4, ytor: [[400, 420]] }, gron: { x: 688, y: 359, s: 0.5, ytor: [[688, 297]] }, rod: { x: 1172, y: 315, s: 0.5, ytor: [[1172, 253]] } }, // i framrutan
    { nr: 128, namn: 'Tankbil 3', fil: 'tankbil3', keiws: { x: 960, y: 538, s: 0.45, ytor: [[960, 440]] }, gron: { x: 435, y: 370, s: 0.5, ytor: [[435, 308]] }, rod: { x: 1172, y: 524, s: 0.5, ytor: [[1172, 462]] } }, // i framrutan
    { nr: 129, namn: 'Tankbil 4', fil: 'tankbil4', keiws: { x: 970, y: 555, s: 0.45, ytor: [[970, 499]] }, gron: { x: 787, y: 326, s: 0.5, ytor: [[787, 264]] }, rod: { x: 1161, y: 315, s: 0.5, ytor: [[1161, 253]] } }, // i framrutan
    { nr: 130, namn: 'Brandbil 7', fil: 'brandbil7', keiws: { x: 1007, y: 491, s: 0.5, ytor: [[1007, 429]] }, gron: { x: 754, y: 260, s: 0.5, ytor: [[754, 198]] }, rod: { x: 1260, y: 359, s: 0.5, ytor: [[1260, 297]] } }, // i framrutan
    { nr: 131, namn: 'Brandbil 8', fil: 'brandbil8', keiws: { x: 1040, y: 545, s: 0.45, ytor: [[1040, 489]] }, gron: { x: 996, y: 348, s: 0.5, ytor: [[996, 286]] }, rod: { x: 358, y: 194, s: 0.5, ytor: [[358, 132]] } }, // i framrutan
    { nr: 132, namn: 'Glassbil', fil: 'glassbil', keiws: { x: 790, y: 488, s: 0.45, ytor: [[790, 410]] }, gron: { x: 600, y: 271, s: 0.5, ytor: [[600, 209]] }, rod: { x: 413, y: 260, s: 0.5, ytor: [[413, 198]] } }, // i luckan eller hytten
    { nr: 133, namn: 'Glassbil 2', fil: 'glassbil2', keiws: { x: 830, y: 470, s: 0.45, ytor: [[830, 414]] }, gron: { x: 589, y: 260, s: 0.5, ytor: [[589, 198]] }, rod: { x: 875, y: 282, s: 0.5, ytor: [[875, 220]] } }, // i luckan eller hytten
    { nr: 134, namn: 'Glassbil 3', fil: 'glassbil3', keiws: { x: 875, y: 491, s: 0.5, ytor: [[875, 429]] }, gron: { x: 677, y: 282, s: 0.5, ytor: [[677, 220]] }, rod: { x: 490, y: 304, s: 0.5, ytor: [[490, 242]] } }, // i luckan eller hytten
    { nr: 135, namn: 'Glassbil 4', fil: 'glassbil4', keiws: { x: 1128, y: 557, s: 0.5, ytor: [[1128, 495]] }, gron: { x: 1447, y: 315, s: 0.5, ytor: [[1447, 253]] }, rod: { x: 259, y: 480, s: 0.5, ytor: [[259, 418]] } }, // i luckan eller hytten
    { nr: 136, namn: 'Glassbil 5', fil: 'glassbil5', keiws: { x: 974, y: 557, s: 0.5, ytor: [[974, 495]] }, gron: { x: 699, y: 293, s: 0.5, ytor: [[699, 231]] }, rod: { x: 446, y: 359, s: 0.5, ytor: [[446, 297]] } }, // i luckan eller hytten
    { nr: 137, namn: 'Skördetröska 2', fil: 'skordetroska2', keiws: { x: 677, y: 491, s: 0.5, ytor: [[677, 429]] }, gron: { x: 817, y: 234, s: 0.42, ytor: [[817, 181]] }, rod: { x: 1304, y: 370, s: 0.5, ytor: [[1304, 308]] } }, // i luckan eller hytten
    { nr: 138, namn: 'Skördetröska 3', fil: 'skordetroska3', keiws: { x: 1030, y: 402, s: 0.45, ytor: [[1030, 300]] }, gron: { x: 1073, y: 205, s: 0.5, ytor: [[1073, 143]] }, rod: { x: 83, y: 425, s: 0.5, ytor: [[83, 363]] } }, // i luckan eller hytten
    { nr: 139, namn: 'Skördetröska 4', fil: 'skordetroska4', keiws: { x: 589, y: 447, s: 0.5, ytor: [[589, 385]] }, gron: { x: 501, y: 227, s: 0.5, ytor: [[501, 165]] }, rod: { x: 105, y: 392, s: 0.5, ytor: [[105, 330]] } }, // i luckan eller hytten
    { nr: 140, namn: 'Skördetröska 5', fil: 'skordetroska5', keiws: { x: 480, y: 428, s: 0.42, ytor: [[480, 300]] }, gron: { x: 457, y: 238, s: 0.5, ytor: [[457, 176]] }, rod: { x: 182, y: 403, s: 0.5, ytor: [[182, 341]] } }, // i luckan eller hytten
];

const BORTTAGNA = [1, 2, 3, 5, 24, 44, 45, 48, 49, 51, 53, 55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 66, 67, 68, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 110, 112];

const AKTIVA = [4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 46, 47, 50, 52, 54, 64, 69, 106, 107, 108, 109, 111, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124];
