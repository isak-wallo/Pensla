document.addEventListener('DOMContentLoaded', () => {
    const viewCanvas = document.getElementById('viewCanvas');
    const vCtx = viewCanvas.getContext('2d');
    const canvasContainer = document.getElementById('canvas-container');

    // Element-referenser — deklarerade först så att funktionerna nedan
    // aldrig kan råka använda dem före deklarationen.
    const startOverlay = document.getElementById('start-overlay');
    const restartBtn = document.getElementById('restart-btn');
    const fillBtn = document.getElementById('fill-btn');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const app = document.getElementById('app');

    // Bilden är 900 px hög och oftast 1200 bred (4:3), men andra format går
    // också: bredden tas från färgbilden när bilden laddas (setPaperSize).
    // Lager:
    //  - lineCanvas: bara konturerna (genomskinlig bakgrund)
    //  - colorCanvas: facit — själva färgbilden (syns aldrig, penseln
    //    hämtar färgen ur den pixel för pixel)
    //  - fillCanvas: det barnet målat fram (vitt där inget är målat)
    //  - viewCanvas: det som syns — fillCanvas med lineCanvas ovanpå
    // Områdena (ytor omringade av linjer) numreras en gång när bilden
    // laddas (`labels`), så att keIWs bara syns i sina ytor.
    let PAPER_W = 1200;
    const PAPER_H = 900;
    const lineCanvas = document.createElement('canvas');
    lineCanvas.width = PAPER_W;
    lineCanvas.height = PAPER_H;
    const lCtx = lineCanvas.getContext('2d', { willReadFrequently: true });
    const colorCanvas = document.createElement('canvas');
    colorCanvas.width = PAPER_W;
    colorCanvas.height = PAPER_H;
    const cCtx = colorCanvas.getContext('2d', { willReadFrequently: true });
    const fillCanvas = document.createElement('canvas');
    fillCanvas.width = PAPER_W;
    fillCanvas.height = PAPER_H;
    const fCtx = fillCanvas.getContext('2d');
    let fillImage = fCtx.createImageData(PAPER_W, PAPER_H);
    let fillPx = new Uint32Array(fillImage.data.buffer);

    // Byter bildbredd: alla lager och buffertar får den nya storleken.
    function setPaperSize(w) {
        if (w === PAPER_W) return;
        PAPER_W = w;
        lineCanvas.width = colorCanvas.width = fillCanvas.width = w;
        fillImage = fCtx.createImageData(w, PAPER_H);
        fillPx = new Uint32Array(fillImage.data.buffer);
        labels = new Int32Array(w * PAPER_H);
    }

    // Omålat papper. Canvas-pixlar lagras som ABGR (little-endian) i en
    // Uint32Array; vitt är samma åt båda hållen.
    const PAPER = 0xFFFFFFFF;
    const BAKGRUND = '#dcecf8';   // runt bilden (samma ljusblå som Poppas himmel)

    // clearState 1 = bilden är nyss tömd och BÖRJA OM erbjuder att nollställa
    // alla bilder. (SPARA togs bort i v105: det målade sparas ändå i plattan.)
    let clearState = 0;
    let clearTimer = null;
    let viewRect = { left: 0, top: 0 };
    // --- Håll-in-logik för BÖRJA OM och FÄRGLÄGG ---
    // Man måste hålla fingret intryckt i HOLD_MS (ca 1 s). BÖRJA OM: en
    // hållning tömmer bilden, och sedan visar knappen en stund (ALLA_MS) att
    // en lång hållning (ALLA_HOLD_MS) nollställer alla bilder.
    // FÄRGLÄGG: en hållning trollar fram hela färgbilden (BÖRJA OM ångrar).
    // En kort tryckning gör inget — så att ett barn inte råkar sudda allt
    // av misstag — utom att knappen en
    // stund (TIPS_MS) visar att man ska hålla inne.
    const HOLD_MS = 1000;
    const FARGA_HOLD_MS = 1500;   // FÄRGLÄGG vill ha en lite längre hållning
    const ALLA_MS = 4000;
    const ALLA_HOLD_MS = 4000;
    // Synka håll-animationens längd i CSS med HOLD_MS (--hold-ms används
    // av .sys-btn.holding i style.css).
    document.documentElement.style.setProperty('--hold-ms', HOLD_MS + 'ms');
    let holdTimer = null;
    let holdBtn = null;
    const TIPS_MS = 5000;
    let tipsTimer = null;

    function startHold(btn) {
        if (holdTimer) clearTimeout(holdTimer);
        holdBtn = btn;
        // Att nollställa alla bilder kräver en längre hållning
        const ms = btn === restartBtn && clearState ? ALLA_HOLD_MS : btn === fillBtn ? FARGA_HOLD_MS : HOLD_MS;
        btn.style.setProperty('--hold-ms', ms + 'ms');
        // Väntar knappen på andra hållningen får tiden inte ta slut mitt i den
        if (vantar(btn) && clearTimer) { clearTimeout(clearTimer); clearTimer = null; }
        holdTimer = setTimeout(() => {
            holdTimer = null;
            btn.classList.remove('holding');
            if (btn === fillBtn) fargaHela();
            else handleClear();
        }, ms);
    }

    // slappt = fingret (musknappen) släpptes på knappen; släpps den innan
    // HOLD_MS gått visas tipset. Glider fingret av knappen visas inget.
    function endHold(slappt) {
        if (holdTimer) {
            clearTimeout(holdTimer);
            holdTimer = null;
            if (slappt) visaHallTips(holdBtn);
            // Avbruten andra hållning: knappen väntar en stund till
            if (vantar(holdBtn) && !clearTimer) {
                clearTimer = setTimeout(aterstallKnappar, ALLA_MS);
            }
        }
    }

    function vantar(btn) {
        return btn === restartBtn && clearState;
    }

    function knappText(btn) {
        if (btn === fillBtn) return 'FÄRGLÄGG';
        return clearState ? 'HÅLL INNE LÄNGE FÖR ATT NOLLSTÄLLA ALLA BILDER' : 'BÖRJA OM';
    }

    function visaHallTips(btn) {
        slackTips();
        // Väntar knappen redan på en andra hållning står det där vad man ska göra
        if (vantar(btn)) return;
        btn.textContent = 'HÅLL INNE FÖR ATT ' +
            (btn === fillBtn ? 'FÄRGLÄGGA' : 'BÖRJA OM');
        btn.classList.add('tips');
        tipsTimer = setTimeout(slackTips, TIPS_MS);
    }

    function slackTips() {
        if (tipsTimer) { clearTimeout(tipsTimer); tipsTimer = null; }
        [restartBtn, fillBtn].forEach(btn => {
            if (btn.classList.contains('tips')) {
                btn.classList.remove('tips');
                btn.textContent = knappText(btn);
            }
        });
    }

    function resizeCanvas() {
        if (!canvasContainer) return;
        const w = canvasContainer.clientWidth;
        const h = canvasContainer.clientHeight;
        // Att sätta width/height nollställer HELA canvas-bufferten även om
        // storleken är oförändrad — gör det bara vid faktisk ändring, så
        // slipper varje applyLayout kosta en omallokering.
        if (viewCanvas.width !== w || viewCanvas.height !== h) {
            viewCanvas.width = w;
            viewCanvas.height = h;
        }
        viewRect = viewCanvas.getBoundingClientRect();
        requestRender();
        markLayout();
    }

    // Layoutlås
    let lockedW = 0, lockedH = 0;
    let lockLandscape = null;
    let shrinkTimer = null;

    // Hur länge (ms) en MINDRE layout-viewport måste bestå innan låset
    // släpper och appen krymper till den. Transienta systemfält i immersive
    // fullscreen ändrar aldrig innerWidth/innerHeight och triggar inte detta.
    // En bestående mindre viewport är ett äkta lägesbyte — t.ex. skärmlåsning
    // (pinning) som tvingar fram status-/navigeringsfält och förskjuter hela
    // fönstret nedåt så knapparna annars klipps vid skärmens nederkant.
    const SHRINK_ADOPT_MS = 400;

    // Statisk dö-yta: en permanent svart remsa som alltid finns där.
    // Garanterar att Androids systemknappar (bakåt/hem/översikt) hamnar
    // framför svart dö-yta istället för framför knapparna eller ritytan.
    // safe-area-inset fungerar inte i installerad standalone-app (inset = 0),
    // därför en fast remsa. 48 px ≈ en systemknappshöjd.
    // Sidan beror på enhet: telefon i landskap har systemknapparna på en
    // långsida (höger), tablet i botten. Vi skiljer på skärmhöjd: låst
    // höjd < 550 px räknas som telefon (dö-yta till höger), annars tablet
    // (dö-yta i botten).
    // Den statiska remsan sätts bara på Android — på iPad/dator finns inga
    // systemknappar över appen, så där skulle den bara ta plats.
    const DEAD_ZONE = 48;
    const PHONE_LANDSCAPE_MAX_H = 550;
    const IS_ANDROID = /Android/i.test(navigator.userAgent);

    function applyLayout() {
        const isLandscape = window.innerWidth > window.innerHeight;
        const w = window.innerWidth;
        const h = window.innerHeight;

        if (lockLandscape === null || isLandscape !== lockLandscape) {
            lockLandscape = isLandscape;
            lockedW = w;
            lockedH = h;
            if (shrinkTimer) { clearTimeout(shrinkTimer); shrinkTimer = null; }
        } else {
            if (w > lockedW) lockedW = w;
            if (h > lockedH) lockedH = h;
        }

        // Mindre viewport än låset? Anta den nya storleken om den består.
        if (w < lockedW || h < lockedH) {
            if (shrinkTimer) clearTimeout(shrinkTimer);
            shrinkTimer = setTimeout(() => {
                shrinkTimer = null;
                const w2 = window.innerWidth;
                const h2 = window.innerHeight;
                if ((w2 > h2) === lockLandscape && (w2 < lockedW || h2 < lockedH)) {
                    lockedW = w2;
                    lockedH = h2;
                    applyLayout();
                }
            }, SHRINK_ADOPT_MS);
        }

        if (app) {
            app.style.width = lockedW + 'px';
            app.style.height = lockedH + 'px';
            // Dö-yta: telefon (låst höjd < 550 px) -> svart remsa till höger,
            // tablet -> svart remsa i botten. + extra dynamisk padding om
            // visualViewport indikerar synliga systemfält (t.ex. vid
            // skärmlåsning/pinning där hela fönstret förskjuts). I immersive
            // fullscreen är den dynamiska delen 0.
            const isPhone = lockedH < PHONE_LANDSCAPE_MAX_H;
            let staticPad = IS_ANDROID ? DEAD_ZONE : 0;
            let dynPad = 0;
            if (window.visualViewport) {
                const dyn = isPhone
                    ? lockedW - window.visualViewport.width - window.visualViewport.offsetLeft
                    : lockedH - window.visualViewport.height - window.visualViewport.offsetTop;
                if (dyn > 0) dynPad = dyn;
            }
            if (isPhone) {
                app.style.paddingRight = (staticPad + dynPad) + 'px';
                app.style.paddingBottom = '';
            } else {
                app.style.paddingBottom = (staticPad + dynPad) + 'px';
                app.style.paddingRight = '';
            }
        }
        resizeCanvas();
    }

    // --- Bilder ---
    // Varje bild är en tecknad färgbild (från Gemini) och dess konturer,
    // framtagna med verktyg/fargbild.py: bilder/farg/NAMN.svg (konturerna,
    // 900 px höga) och bilder/farg/NAMN.jpg (färgbilden som penseln trollar
    // fram). Konturerna ritas på lineCanvas och färgbilden på colorCanvas.

    // Bilderna står i bilder.js; bara de aktiva visas.
    // Ordningen blandas varje gång appen startar men ligger fast medan den
    // är igång, så att ◀ och ▶ går fram och tillbaka i samma ordning.
    const PICTURES = ALLA_BILDER.filter(b => AKTIVA.includes(b.nr));
    for (let i = PICTURES.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [PICTURES[i], PICTURES[j]] = [PICTURES[j], PICTURES[i]];
    }

    // Bildfilerna laddas i förväg så att bläddring går direkt.
    PICTURES.forEach(pic => {
        pic.img = new Image();
        pic.img.src = 'bilder/farg/' + pic.fil + '.svg';
        pic.fimg = new Image();
        pic.fimg.src = 'bilder/farg/' + pic.fil + '.jpg';
    });
    let vantarPaBild = -1;
    let currentPicture = 0;

    // --- Områden (numrerade ytor) ---
    // labels[i]: 0 = linje (går inte att måla), >0 = områdets nummer.
    // Pixlar med alpha >= LINE_ALPHA räknas som linje; kantpixlarna under
    // den gränsen hör till ytan så att färgen går hela vägen in under
    // linjens anti-aliasade kant (ingen vit hinna). Ytorna behövs bara för
    // keIWs (han syns bara i sina ytor).
    const LINE_ALPHA = 200;
    let labels = new Int32Array(PAPER_W * PAPER_H);
    let antalYtor = 1;
    let facitPx = new Uint32Array(PAPER_W * PAPER_H);   // färgbilden pixel för pixel

    function labelRegions() {
        const W = PAPER_W, H = PAPER_H;
        const alpha = lCtx.getImageData(0, 0, W, H).data;
        labels.fill(0);
        for (let i = 0, n = W * H; i < n; i++) {
            if (alpha[i * 4 + 3] < LINE_ALPHA) labels[i] = -1;   // yta, ej besökt
        }
        let id = 0;
        for (let seed = 0, n = W * H; seed < n; seed++) {
            if (labels[seed] !== -1) continue;
            id++;
            floodLabel(seed, id);
        }
        antalYtor = id + 1;
    }

    // Scanline-fyllning som numrerar ett sammanhängande område (4-grannar).
    function floodLabel(seed, id) {
        const W = PAPER_W, H = PAPER_H;
        const stack = [seed];
        while (stack.length) {
            const p = stack.pop();
            if (labels[p] !== -1) continue;
            const y = (p / W) | 0;
            const rowStart = y * W;
            let l = p, r = p;
            while (l > rowStart && labels[l - 1] === -1) l--;
            while (r < rowStart + W - 1 && labels[r + 1] === -1) r++;
            for (let i = l; i <= r; i++) labels[i] = id;
            for (let dy = -1; dy <= 1; dy += 2) {
                const yy = y + dy;
                if (yy < 0 || yy >= H) continue;
                const base = yy * W;
                let inSpan = false;
                for (let x = l - rowStart; x <= r - rowStart; x++) {
                    if (labels[base + x] === -1) {
                        if (!inSpan) { stack.push(base + x); inSpan = true; }
                    } else {
                        inSpan = false;
                    }
                }
            }
        }
    }

    // Penseln trollar fram själva färgbilden pixel för pixel (facitPx).
    // Helt vita pixlar flyttas ett snäpp från PAPER, som betyder omålad.
    function franFargbild() {
        facitPx = new Uint32Array(cCtx.getImageData(0, 0, PAPER_W, PAPER_H).data.buffer);
        for (let i = 0, len = facitPx.length; i < len; i++) {
            if (facitPx[i] === PAPER) facitPx[i] = 0xFFFEFEFE;
        }
    }

    // --- keIWs och hans kompisar ---
    // Den lilla blå kompisen gömmer sig i varje bild, som krypet i Richard
    // Scarrys böcker, och med sig har han två kompisar: en grön och en röd
    // (exakta kopior i andra färger). De syns inte från början; när man
    // målar där en av dem är poppar han upp, vinkar och blir kvar. När alla
    // tre är hittade (genom att måla) vinkar de en gång till tillsammans.
    // De ritas av sina klossar (KEIWS i keiws.js, origo i kroppens övre
    // vänstra hörn), så de blir skarpa i alla storlekar.
    const KEIWS_TRAFF = 40;     // så många målade pixlar på honom innan han poppar
    const KEIWS_UPP_MS = 720;   // upp bakom kanten med en liten studs …
    const KEIWS_VINKA = 820;    // … vinkar sedan (KEIWS.vinka) …
    const KEIWS_VINKA_MS = KEIWS.vinka.reduce((t, b) => t + b.tid, 0);
    const KEIWS_BLINK = KEIWS_VINKA + KEIWS_VINKA_MS + 300;   // … och blinkar en gång
    const KEIWS_MS = KEIWS_BLINK + 400;
    const FEST_PAUS_MS = 300;   // från sista kompisens blink till festvinkningen
    const VALKOMMEN_MS = 400;   // bläddrar man till en bild där alla är hittade vinkar de efter så här länge
    // Nyckeln i bilder.js och färgerna (samma nycklar som KEIWS.farger)
    const KOMPISAR = [
        ['keiws', KEIWS.farger],
        ['gron', { bla: '#50c499', ljus: '#64d2aa', oga: '#101628' }],   // mintgrön
        ['rod', { bla: '#d66d61', ljus: '#e38277', oga: '#101628' }],    // korallröd
    ];
    // Kompisarna i bilden: { farger, x, y, s, box, yta, mask, tmp, hittad, start, traff }
    let kompisar = [];
    let festTid = null;         // när alla tre ska vinka tillsammans

    // (x, y) = mitt under fötterna, s = skala.
    function ritaKeiws(ctx, x, y, s, rekt, farger) {
        const X = v => Math.round(x + (v - 80) * s), Y = v => Math.round(y + (v - 204) * s);
        rekt.forEach(([x0, y0, x1, y1, f]) => {
            ctx.fillStyle = farger[f];
            ctx.fillRect(X(x0), Y(y0), X(x1) - X(x0), Y(y1) - Y(y0));
        });
    }

    // Förbereder kompisarna för bilden: ruta, mask (de ytor han syns i) och
    // en arbetscanvas var. Anropas efter labelRegions.
    function prepKeiws(pic, hittade) {
        festTid = null;
        kompisar = [];
        KOMPISAR.forEach(([nyckel, farger], i) => {
            const c = pic[nyckel];
            if (!c) return;
            const yta = new Uint8Array(antalYtor);
            c.ytor.forEach(([px, py]) => {
                const l = labels[Math.round(py) * PAPER_W + Math.round(px)];
                if (l > 0) yta[l] = 1;
            });
            // Rutan rymmer honom med armarna ute och lite luft ovanför (han
            // studsar lite förbi och vinkar med armen över huvudet)
            const x0 = Math.max(0, Math.floor(c.x - 126 * c.s));
            const x1 = Math.min(PAPER_W - 1, Math.ceil(c.x + 138 * c.s));
            const y0 = Math.max(0, Math.floor(c.y - 252 * c.s * 1.2));
            const y1 = Math.min(PAPER_H - 1, Math.ceil(c.y));
            const w = x1 - x0 + 1, h = y1 - y0 + 1;
            const mask = document.createElement('canvas');
            mask.width = w;
            mask.height = h;
            const mctx = mask.getContext('2d');
            const img = mctx.createImageData(w, h);
            const px = new Uint32Array(img.data.buffer);
            for (let y = 0; y < h; y++) {
                for (let x = 0; x < w; x++) {
                    if (yta[labels[(y0 + y) * PAPER_W + x0 + x]]) px[y * w + x] = 0xFF000000;
                }
            }
            mctx.putImageData(img, 0, 0);
            const tmp = document.createElement('canvas');
            tmp.width = w;
            tmp.height = h;
            kompisar.push({ farger, x: c.x, y: c.y, s: c.s, box: { x0, y0, x1, y1, w, h },
                            yta, mask, tmp, hittad: !!(hittade && hittade[i]), start: -Infinity, traff: 0 });
        });
    }

    function poppaKeiws(k) {
        if (k.hittad) return;
        k.hittad = true;
        k.start = performance.now();
        sparaSnart();
        requestRender();
    }

    // Efter penseldrag: poppar de som målats fram. Blev det den sista
    // vinkar alla tillsammans när han vinkat klart.
    function kollaKompisar() {
        let ny = null;
        kompisar.forEach(k => {
            if (!k.hittad && k.traff >= KEIWS_TRAFF) { poppaKeiws(k); ny = k; }
        });
        if (ny && kompisar.length > 1 && kompisar.every(k => k.hittad)) {
            festTid = ny.start + KEIWS_MS + FEST_PAUS_MS;
        }
    }

    // Vilka klossar som visas vid tiden t (ms sedan han hittades).
    function keiwsLage(t) {
        if (t >= KEIWS_VINKA && t < KEIWS_VINKA + KEIWS_VINKA_MS) {
            let v = t - KEIWS_VINKA;
            for (const b of KEIWS.vinka) {
                if (v < b.tid) return b.rekt;
                v -= b.tid;
            }
        }
        if (t >= KEIWS_BLINK && t < KEIWS_BLINK + 160) return KEIWS.blink;
        return KEIWS.stilla;
    }

    // Ritar kompisen k maskad till sina ytor på ctx (i bildkoordinater).
    function ritaKeiwsMaskad(ctx, k, upp, rekt) {
        const b = k.box, tctx = k.tmp.getContext('2d');
        tctx.globalCompositeOperation = 'source-over';
        tctx.clearRect(0, 0, b.w, b.h);
        ritaKeiws(tctx, k.x - b.x0, k.y - b.y0 + (1 - upp) * 204 * k.s, k.s, rekt, k.farger);
        tctx.globalCompositeOperation = 'destination-in';
        tctx.drawImage(k.mask, 0, 0);
        tctx.globalCompositeOperation = 'source-over';
        ctx.drawImage(k.tmp, b.x0, b.y0);
    }

    // Ritar de hittade kompisarna på vCtx, som redan har bildens transform.
    // Returnerar true medan någon animation pågår (eller festen väntar).
    function renderKeiws(now) {
        if (festTid !== null && now >= festTid) {
            // Festen: alla vinkar och blinkar en gång till (redan uppe)
            kompisar.forEach(k => { k.start = now - KEIWS_VINKA; });
            festTid = null;
        }
        let ror = festTid !== null;
        kompisar.forEach(k => {
            if (!k.hittad) return;
            const t = now - k.start;
            let upp = 1;
            if (t < KEIWS_UPP_MS) {
                const p = t / KEIWS_UPP_MS, kk = 1.5;
                upp = 1 + (kk + 1) * Math.pow(p - 1, 3) + kk * Math.pow(p - 1, 2);
            }
            ritaKeiwsMaskad(vCtx, k, upp, keiwsLage(t));
            if (t < KEIWS_MS) ror = true;
        });
        return ror;
    }

    // --- Det målade sparas i plattan ---
    // Varje bild minns det man målat, även när appen stängs eller en ny
    // version laddas (som teckningen i Kludda). Det målade är alltid
    // färgbildens egna pixlar, så det räcker att minnas VILKA pixlar som är
    // målade: en bit per pixel (`mask`, 135 kB för 1200 × 900) och vilka
    // kompisar som är hittade. `sparade` har alla bilders minne (nyckel =
    // bildens fasta nr) och skrivs till IndexedDB en stund efter en ändring
    // (SPARA_EFTER_MS, men inte mitt i ett penseldrag) och direkt när appen
    // döljs eller man byter bild. BÖRJA OM tömmer bildens minne.
    const DB_NAMN = 'pensla';
    const DB_LAGER = 'bilder';
    const DB_VANTA_MS = 2000;                // längre än så väntar starten inte på det sparade
    const SENAST_NYCKEL = 'pensla-senast';   // nr på bilden som visades sist (localStorage)
    const SPARA_EFTER_MS = 1500;
    const sparade = new Map();   // nr -> { nr, w, mask, hittade }
    let db = null;
    let andrad = false;          // bilden som visas är ändrad sedan den sparades
    let minnsTimer = null;
    let uppskjutet = 0;          // så många gånger sparandet väntat på att fingret ska lyftas
    let skrivs = Promise.resolve();   // den senaste skrivningen till plattan
    let startad = false;         // det sparade är inläst och första bilden visas
    let pictureLoaded = false;

    // Läser in allt sparat. Svarar alltid (även utan IndexedDB, och senast
    // efter DB_VANTA_MS), så att appen startar ändå.
    function lasSparat() {
        return new Promise(resolve => {
            const vanta = setTimeout(resolve, DB_VANTA_MS);
            const svara = () => { clearTimeout(vanta); resolve(); };
            try {
                const q = indexedDB.open(DB_NAMN, 1);
                q.onupgradeneeded = () => q.result.createObjectStore(DB_LAGER, { keyPath: 'nr' });
                q.onerror = q.onblocked = svara;
                q.onsuccess = () => {
                    db = q.result;
                    const alla = db.transaction(DB_LAGER).objectStore(DB_LAGER).getAll();
                    alla.onsuccess = () => {
                        alla.result.forEach(p => { if (!sparade.has(p.nr)) sparade.set(p.nr, p); });
                        svara();
                    };
                    alla.onerror = svara;
                };
            } catch (e) { svara(); }
        });
    }

    // För över bilden som visas till `sparade` (en omålad bild utan hittade
    // kompisar tas bort därifrån). Returnerar bildens nr.
    function minns() {
        const nr = PICTURES[currentPicture].nr;
        const n = PAPER_W * PAPER_H;
        const mask = new Uint8Array((n + 7) >> 3);
        let malat = false;
        for (let i = 0; i < n; i++) {
            if (fillPx[i] !== PAPER) { mask[i >> 3] |= 1 << (i & 7); malat = true; }
        }
        const hittade = kompisar.map(k => k.hittad);
        if (malat || hittade.some(h => h)) sparade.set(nr, { nr, w: PAPER_W, mask, hittade });
        else sparade.delete(nr);
        return nr;
    }

    // Skriver bildens minne till plattan (eller tar bort det).
    function skriv(nr) {
        return new Promise(resolve => {
            if (!db) { resolve(); return; }
            try {
                const tx = db.transaction(DB_LAGER, 'readwrite');
                const p = sparade.get(nr);
                if (p) tx.objectStore(DB_LAGER).put(p);
                else tx.objectStore(DB_LAGER).delete(nr);
                tx.oncomplete = tx.onerror = tx.onabort = () => resolve();
            } catch (e) { resolve(); }
        });
    }

    // Direkt (när appen döljs, man byter bild eller en ny version ska
    // laddas). Löftet är klart när det som sparats sist är skrivet.
    function sparaNu() {
        if (minnsTimer) { clearTimeout(minnsTimer); minnsTimer = null; }
        uppskjutet = 0;
        if (andrad && pictureLoaded) {
            andrad = false;
            skrivs = skriv(minns());
        }
        return skrivs;
    }

    // En stund efter en ändring. Mitt i ett penseldrag (eller FÄRGLÄGG)
    // väntar det lite till, så att det inte hackar på en gammal platta —
    // men inte hur länge som helst.
    function sparaSnart() {
        andrad = true;
        if (minnsTimer) return;
        minnsTimer = setTimeout(() => {
            minnsTimer = null;
            if ((fingers.size || mouseLast || fargaAnim) && ++uppskjutet < 6) sparaSnart();
            else sparaNu();
        }, SPARA_EFTER_MS);
    }

    // NOLLSTÄLL ALLA: allt sparat tas bort.
    function glomAllt() {
        sparade.clear();
        andrad = false;
        if (!db) return;
        try { db.transaction(DB_LAGER, 'readwrite').objectStore(DB_LAGER).clear(); } catch (e) { /* utan lagring */ }
    }

    // En ny version (service workern längst ner) laddas inte mitt i
    // målandet utan när appen döljs eller startskärmen visas, och det
    // målade sparas först (som i Kludda).
    let nyVersion = false;

    function laddaOmOmNy() {
        if (!nyVersion) return;
        nyVersion = false;
        sparaNu().then(() => window.location.reload());
    }

    function loadPicture(index) {
        const pic = PICTURES[index];
        const ejKlar = [pic.img, pic.fimg].find(im => im && !(im.complete && im.naturalWidth));
        if (ejKlar) {
            // Bildfilen är inte laddad än: byt när den är klar
            vantarPaBild = index;
            ejKlar.onload = () => { if (vantarPaBild === index) loadPicture(index); };
            return;
        }
        vantarPaBild = -1;
        stoppaFarga();
        if (pictureLoaded) sparaNu();
        pictureLoaded = true;
        currentPicture = index;
        try { localStorage.setItem(SENAST_NYCKEL, pic.nr); } catch (e) { /* utan lagring */ }
        setPaperSize(Math.round(PAPER_H * pic.fimg.naturalWidth / pic.fimg.naturalHeight));
        lCtx.setTransform(1, 0, 0, 1, 0, 0);
        lCtx.clearRect(0, 0, PAPER_W, PAPER_H);
        lCtx.drawImage(pic.img, 0, 0, PAPER_W, PAPER_H);
        cCtx.setTransform(1, 0, 0, 1, 0, 0);
        cCtx.clearRect(0, 0, PAPER_W, PAPER_H);
        cCtx.drawImage(pic.fimg, 0, 0, PAPER_W, PAPER_H);
        labelRegions();
        franFargbild();
        // Det sparade gäller bara om bilden har samma bredd som då
        let saved = sparade.get(pic.nr);
        if (saved && saved.w !== PAPER_W) saved = null;
        prepKeiws(pic, saved && saved.hittade);
        if (saved) {
            const mask = saved.mask;
            for (let i = 0, n = PAPER_W * PAPER_H; i < n; i++) {
                fillPx[i] = (mask[i >> 3] >> (i & 7)) & 1 ? facitPx[i] : PAPER;
            }
        } else {
            fillPx.fill(PAPER);
        }
        fCtx.putImageData(fillImage, 0, 0);
        dirty = null;
        aterstallKnappar();
        // Alla redan hittade (bilden är färdigmålad): de vinkar en gång
        if (kompisar.length && kompisar.every(k => k.hittad)) {
            festTid = performance.now() + VALKOMMEN_MS;
        }
        requestRender();
    }

    function changePicture(step) {
        if (!startad) return;
        const bas = vantarPaBild >= 0 ? vantarPaBild : currentPicture;
        loadPicture((bas + step + PICTURES.length) % PICTURES.length);
    }

    // --- Rendering ---
    // Bilden passas in i ytan (utan beskärning). Är ytan stående (iPad i
    // porträtt) roteras bilden 90° medurs så den fortfarande blir stor.
    let xf = { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 };

    function updateTransform() {
        const W = viewCanvas.width, H = viewCanvas.height;
        if (W >= H) {
            const s = Math.min(W / PAPER_W, H / PAPER_H);
            xf = { a: s, b: 0, c: 0, d: s,
                   e: (W - PAPER_W * s) / 2, f: (H - PAPER_H * s) / 2 };
        } else {
            const s = Math.min(H / PAPER_W, W / PAPER_H);
            xf = { a: 0, b: s, c: -s, d: 0,
                   e: W / 2 + (PAPER_H / 2) * s, f: H / 2 - (PAPER_W / 2) * s };
        }
    }

    // Ritning sker högst en gång per frame (requestRender). Målade pixlar
    // skrivs till fillPx direkt; `dirty` samlar vilken rektangel som
    // behöver föras över till fillCanvas innan nästa ritning.
    let dirty = null;
    let renderPending = false;

    function markDirty(x0, y0, x1, y1) {
        if (!dirty) dirty = { x0, y0, x1, y1 };
        else {
            if (x0 < dirty.x0) dirty.x0 = x0;
            if (y0 < dirty.y0) dirty.y0 = y0;
            if (x1 > dirty.x1) dirty.x1 = x1;
            if (y1 > dirty.y1) dirty.y1 = y1;
        }
    }

    function requestRender() {
        if (renderPending) return;
        renderPending = true;
        requestAnimationFrame(() => {
            renderPending = false;
            render();
        });
    }

    function render() {
        if (dirty) {
            fCtx.putImageData(fillImage, 0, 0, dirty.x0, dirty.y0,
                dirty.x1 - dirty.x0 + 1, dirty.y1 - dirty.y0 + 1);
            dirty = null;
        }
        const W = viewCanvas.width, H = viewCanvas.height;
        if (W === 0 || H === 0) return;
        updateTransform();
        vCtx.setTransform(1, 0, 0, 1, 0, 0);
        vCtx.fillStyle = BAKGRUND;
        vCtx.fillRect(0, 0, W, H);
        vCtx.setTransform(xf.a, xf.b, xf.c, xf.d, xf.e, xf.f);
        vCtx.drawImage(fillCanvas, 0, 0);
        const now = performance.now();
        const keiwsRor = renderKeiws(now);
        vCtx.drawImage(lineCanvas, 0, 0);
        vCtx.setTransform(1, 0, 0, 1, 0, 0);
        if (keiwsRor) requestRender();
    }

    // Skärmkoordinat -> bildkoordinat (inversen av xf)
    function getPaperCoords(clientX, clientY) {
        const vx = clientX - viewRect.left - xf.e;
        const vy = clientY - viewRect.top - xf.f;
        const det = xf.a * xf.d - xf.b * xf.c;
        return {
            x: (xf.d * vx - xf.c * vy) / det,
            y: (-xf.b * vx + xf.a * vy) / det
        };
    }

    // --- Måla ---
    // Fingret är en pensel som trollar fram färgbilden där den målar (den
    // kan inte välja färg). Bara det som målas blir målat, inget fylls i av
    // sig självt.
    const PENSEL = 28;         // penselns radie i bildpixlar

    // Målar en rund klick med penseln kring (cx, cy) i bildkoordinater.
    function stamp(cx, cy) {
        const W = PAPER_W, H = PAPER_H, r = PENSEL;
        const y0 = Math.max(0, Math.ceil(cy - r)), y1 = Math.min(H - 1, Math.floor(cy + r));
        if (y0 > y1) return;
        let minX = W, maxX = -1;
        for (let y = y0; y <= y1; y++) {
            const dy = y - cy;
            const half = Math.sqrt(r * r - dy * dy);
            const xa = Math.max(0, Math.ceil(cx - half)), xb = Math.min(W - 1, Math.floor(cx + half));
            if (xa > xb) continue;
            if (xa < minX) minX = xa;
            if (xb > maxX) maxX = xb;
            for (const k of kompisar) {
                if (k.hittad || y < k.box.y0 || y > k.box.y1) continue;
                const ka = Math.max(xa, k.box.x0), kb = Math.min(xb, k.box.x1);
                for (let i = y * W + ka, end = y * W + kb; i <= end; i++) {
                    if (k.yta[labels[i]]) k.traff++;
                }
            }
            for (let i = y * W + xa, end = y * W + xb; i <= end; i++) {
                if (labels[i] > 0) fillPx[i] = facitPx[i];
            }
        }
        if (maxX >= minX) markDirty(minX, y0, maxX, y1);
    }

    // FÄRGLÄGG — hela färgbilden trollas fram, svepande från vänster till
    // höger under FARGA_MS, och sedan poppar keIWs och kompisarna fram
    // (utan festvinkning: den får man när man målat fram dem själv).
    const FARGA_MS = 1800;
    let fargaAnim = null;

    function fargaHela() {
        stoppaFarga();
        if (clearState) aterstallKnappar();
        sparaSnart();
        const start = performance.now();
        let x = 0;
        const steg = now => {
            const nx = Math.min(PAPER_W, Math.round((now - start) / FARGA_MS * PAPER_W));
            if (nx > x) {
                for (let y = 0; y < PAPER_H; y++) {
                    for (let i = y * PAPER_W + x, end = y * PAPER_W + nx; i < end; i++) {
                        if (labels[i] > 0) fillPx[i] = facitPx[i];
                    }
                }
                markDirty(x, 0, nx - 1, PAPER_H - 1);
                x = nx;
                requestRender();
            }
            if (x < PAPER_W) fargaAnim = requestAnimationFrame(steg);
            else { fargaAnim = null; kompisar.forEach(poppaKeiws); }
        };
        fargaAnim = requestAnimationFrame(steg);
    }

    function stoppaFarga() {
        if (fargaAnim) { cancelAnimationFrame(fargaAnim); fargaAnim = null; }
    }

    // Penseldrag från a till b: klickar tätt längs sträckan.
    function stroke(ax, ay, bx, by) {
        const d = Math.hypot(bx - ax, by - ay);
        const steg = Math.max(1, Math.ceil(d / (PENSEL * 0.35)));
        for (let k = 1; k <= steg; k++) {
            stamp(ax + (bx - ax) * k / steg, ay + (by - ay) * k / steg);
        }
    }

    // Efter varje penseldrag: har han målats fram?
    function checkTouched() {
        sparaSnart();
        kollaKompisar();
        if (clearState) aterstallKnappar();
        requestRender();
    }

    // Alla fingrar målar. Varje finger minns sin senaste punkt.
    const fingers = new Map();

    function onTouchStart(e) {
        if (e.cancelable) e.preventDefault();
        for (let i = 0; i < e.changedTouches.length; i++) {
            const t = e.changedTouches[i];
            const p = getPaperCoords(t.clientX, t.clientY);
            fingers.set(t.identifier, p);
            stamp(p.x, p.y);
        }
        checkTouched();
    }

    function onTouchMove(e) {
        if (e.cancelable) e.preventDefault();
        for (let i = 0; i < e.changedTouches.length; i++) {
            const t = e.changedTouches[i];
            const last = fingers.get(t.identifier);
            if (!last) continue;
            const p = getPaperCoords(t.clientX, t.clientY);
            stroke(last.x, last.y, p.x, p.y);
            fingers.set(t.identifier, p);
        }
        checkTouched();
    }

    function onTouchEnd(e) {
        for (let i = 0; i < e.changedTouches.length; i++) fingers.delete(e.changedTouches[i].identifier);
    }

    // BÖRJA OM — en hållning (1 s) tömmer bilden. Sedan står det en stund
    // (ALLA_MS, eller tills man målar) att en lång hållning (ALLA_HOLD_MS)
    // nollställer alla bilder till svartvitt.
    function handleClear() {
        if (clearState === 0) {
            tomBild();
            aterstallKnappar();
            clearState = 1;
            restartBtn.textContent = knappText(restartBtn);
            restartBtn.classList.add('confirm', 'lang');
            clearTimer = setTimeout(aterstallKnappar, ALLA_MS);
        } else {
            glomAllt();
            tomBild();
            aterstallKnappar();
            restartBtn.textContent = 'ALLA NOLLSTÄLLDA ✓';
            restartBtn.classList.add('lang');
            clearTimer = setTimeout(aterstallKnappar, 2000);
        }
    }

    function tomBild() {
        stoppaFarga();
        kompisar.forEach(k => { k.hittad = false; k.traff = 0; });
        festTid = null;
        fillPx.fill(PAPER);
        fCtx.putImageData(fillImage, 0, 0);
        dirty = null;
        sparaSnart();
        requestRender();
    }

    function aterstallKnappar() {
        clearState = 0;
        if (clearTimer) {
            clearTimeout(clearTimer);
            clearTimer = null;
        }
        if (restartBtn) {
            restartBtn.textContent = 'BÖRJA OM';
            restartBtn.classList.remove('confirm', 'tips', 'lang');
        }
    }

    function isInstalledApp() {
        return window.matchMedia('(display-mode: standalone)').matches
            || window.navigator.standalone === true;
    }

    function startApp() {
        // Begär alltid fullscreen — även om fullscreenElement ser satt ut.
        // Android kan tvinga fram systemfälten (t.ex. vid skärmlåsning) utan
        // att HTML-fullscreen formellt släpps; en ny begäran med gest rättar
        // till läget, och är den redan i fullscreen händer inget.
        if (document.documentElement.requestFullscreen) {
            document.documentElement.requestFullscreen().catch(err => {
                console.log(`Helskärm misslyckades: ${err.message}`);
            });
        } else if (document.documentElement.webkitRequestFullscreen) {
            // Äldre iPads (före iPadOS 16.4) har bara webkit-prefixet.
            document.documentElement.webkitRequestFullscreen();
        }
        document.getElementById('start-overlay').style.display = 'none';
        setTimeout(applyLayout, 100);
    }

    // Startskärmen fungerar som återhämtningsläge: den visas vid bakåt-tryck
    // och när fullscreen tappats, och BÖRJA PENSLA-knappen (en äkta gest) tar
    // tillbaka in i fullscreen. Det målade påverkas inte.
    function showStartOverlay() {
        startOverlay.style.display = 'flex';
        stangMarkering();
        aterstallKnappar();
        laddaOmOmNy();
    }

    // --- Hemlig markering (vuxengest) ---
    // Ägaren kan märka ut bilder som ska kontrolleras noggrannare: håll
    // båda pilarna och FÄRGLÄGG samtidigt i GEST_MS (5 s), utan att BÖRJA OM
    // hålls. Då kommer texten "Markera områden som ska ses över" högst upp
    // och knapparna KLAR och AVBRYT i panelen, och man målar grovt med
    // fingret runt det som ska kollas (flera drag går; inga drag alls =
    // hela bilden). Dragen ritas i ett eget lager ovanpå appen, så det
    // målade rörs inte och inget målas under tiden. KLAR sparar markeringen
    // i en kö i plattan (localStorage) och skickar den till mottagaren på
    // samma adress (worker/mottagare.js); går det inte fram ligger den kvar
    // i kön och skickas när appen startas nästa gång. AVBRYT kastar den.
    // Båda går tillbaka till den vanliga appen. Inget ljud.
    //
    // En markering: { id, nr, namn, drag: [[x0, y0, x1, y1, ...] ...],
    // bredd, tid, version, plattform }. Punkterna är normerade 0–1 relativt
    // bilden (x mot bredden, y mot höjden) och `bredd` är penselns bredd
    // som andel av bildens höjd. Dragen förenklas innan de sparas. Samma
    // rad skrivs av Pensla N, och läses med verktyg/markeringar.py.
    const GEST_MS = 5000;
    const PIL_KLICK_MS = 1000;      // ett klick så här snart efter ett tryck med fingret på en pil är samma tryck
    const GEST_SLACK = 12;          // så många px får ett finger glida utanför sin knapp
    const MARK_BREDD = 0.05;        // penselns bredd (andel av bildens höjd)
    const MARK_FARG = '#e6007e';    // syns mot alla bilderna; lagret är halvgenomskinligt (style.css)
    const MARK_STEG = 0.006;        // tätare punkter än så tas inte med (andel av höjden)
    const MARK_SLAT = 0.004;        // förenklingen får flytta draget högst så här mycket
    const MARK_MAX_DRAG = 20;       // taken kontrolleras också av mottagaren
    const MARK_MAX_PUNKTER = 100;   // per drag
    const MARK_MAX_ALLA = 600;      // punkter sammanlagt
    const MARK_VILA_MS = 90000;     // läget stängs av sig självt om inget händer
    const MARK_KO = 'pensla-markeringar';
    const MARK_KO_MAX = 50;
    const MARK_URL = 'api/markering';
    const MARK_VANTA_MS = 8000;
    const MARK_SVALJ_MS = 350;      // så länge ligger lagret kvar (osynligt) efter AVBRYT
    const MARK_TEXT = 'Markera områden som ska ses över';
    const markLage = document.getElementById('mark-lage');
    const markCanvas = document.getElementById('markCanvas');
    const markPanel = document.getElementById('mark-panel');
    const markText = document.getElementById('mark-text');
    const mCtx = markCanvas.getContext('2d');
    const gestNere = new Map();     // finger (touch.identifier) -> knappen det sattes ner på
    let gestTimer = null;
    let foreBild = -1;              // bilden som visades innan den första pilen trycktes
    let markerar = false;
    let markDrag = [];              // färdiga drag: [x0, y0, x1, y1, ...] normerat
    const markPagar = new Map();    // finger -> draget som ritas just nu
    let markVila = null;
    let markStang = null;

    function nereKnappar() {
        return new Set(gestNere.values());
    }

    function gestNer(e, btn) {
        for (let i = 0; i < e.changedTouches.length; i++) gestNere.set(e.changedTouches[i].identifier, btn);
    }

    function gestUpp(e) {
        for (let i = 0; i < e.changedTouches.length; i++) gestNere.delete(e.changedTouches[i].identifier);
        gestKoll();
    }

    // Ett finger som glider av sin knapp räknas inte längre.
    function gestFlytt(e) {
        if (!gestNere.size) return;
        let andrat = false;
        for (let i = 0; i < e.changedTouches.length; i++) {
            const t = e.changedTouches[i];
            const btn = gestNere.get(t.identifier);
            if (!btn) continue;
            const r = btn.getBoundingClientRect();
            if (t.clientX < r.left - GEST_SLACK || t.clientX > r.right + GEST_SLACK ||
                t.clientY < r.top - GEST_SLACK || t.clientY > r.bottom + GEST_SLACK) {
                gestNere.delete(t.identifier);
                andrat = true;
            }
        }
        if (andrat) gestKoll();
    }

    // Gesten räknas bara medan ◀, ▶ och FÄRGLÄGG alla hålls och BÖRJA OM
    // inte gör det (en hand som vilar över hela panelen ger alltså inget).
    function gestKoll() {
        const n = nereKnappar();
        const alla = n.has(prevBtn) && n.has(nextBtn) && n.has(fillBtn) && !n.has(restartBtn);
        if (alla && !markerar) {
            if (gestTimer) return;
            holdEnd(false);         // FÄRGLÄGG ska inte färglägga
            slackTips();
            gestTimer = setTimeout(() => { gestTimer = null; oppnaMarkering(); }, GEST_MS);
        } else if (gestTimer) {
            clearTimeout(gestTimer);
            gestTimer = null;
        }
    }

    // Lägger lagret precis över bilden, texten högst upp i den och
    // knapparna precis över knapp-panelen.
    function markLayout() {
        if (!markerar) return;
        const c = viewCanvas.getBoundingClientRect();
        markCanvas.style.left = c.left + 'px';
        markCanvas.style.top = c.top + 'px';
        markCanvas.style.width = c.width + 'px';
        markCanvas.style.height = c.height + 'px';
        if (markCanvas.width !== viewCanvas.width || markCanvas.height !== viewCanvas.height) {
            markCanvas.width = viewCanvas.width;
            markCanvas.height = viewCanvas.height;
        }
        markText.style.left = (c.left + c.width / 2) + 'px';
        markText.style.top = (c.top + 8) + 'px';
        markText.style.maxWidth = (c.width - 16) + 'px';
        const p = document.getElementById('button-container').getBoundingClientRect();
        markPanel.style.left = p.left + 'px';
        markPanel.style.top = p.top + 'px';
        markPanel.style.width = p.width + 'px';
        markPanel.style.height = p.height + 'px';
        ritaMarkering();
    }

    // Dragen ritas i bildens koordinater med samma transform som bilden,
    // heltäckande (lagret är halvgenomskinligt, så överlapp blir inte mörkare).
    function ritaMarkering() {
        mCtx.setTransform(1, 0, 0, 1, 0, 0);
        mCtx.clearRect(0, 0, markCanvas.width, markCanvas.height);
        updateTransform();
        mCtx.setTransform(xf.a, xf.b, xf.c, xf.d, xf.e, xf.f);
        mCtx.lineJoin = mCtx.lineCap = 'round';
        mCtx.lineWidth = MARK_BREDD * PAPER_H;
        mCtx.strokeStyle = mCtx.fillStyle = MARK_FARG;
        markDrag.concat(Array.from(markPagar.values())).forEach(d => {
            mCtx.beginPath();
            if (d.length === 2) {
                mCtx.arc(d[0] * PAPER_W, d[1] * PAPER_H, MARK_BREDD * PAPER_H / 2, 0, 2 * Math.PI);
                mCtx.fill();
                return;
            }
            mCtx.moveTo(d[0] * PAPER_W, d[1] * PAPER_H);
            for (let i = 2; i < d.length; i += 2) mCtx.lineTo(d[i] * PAPER_W, d[i + 1] * PAPER_H);
            mCtx.stroke();
        });
        mCtx.setTransform(1, 0, 0, 1, 0, 0);
    }

    // Skärmpunkt -> normerad bildpunkt (0–1), hållen inom bilden.
    function markPunkt(clientX, clientY) {
        const p = getPaperCoords(clientX, clientY);
        return [Math.min(1, Math.max(0, p.x / PAPER_W)), Math.min(1, Math.max(0, p.y / PAPER_H))];
    }

    // Avståndet mellan två normerade punkter, i andelar av bildens höjd.
    function markAvstand(ax, ay, bx, by) {
        return Math.hypot((bx - ax) * PAPER_W / PAPER_H, by - ay);
    }

    // Förenklar ett drag (Ramer–Douglas–Peucker): punkter som ligger närmare
    // än `slat` från linjen mellan sina grannar tas bort. Grövre tills
    // draget ryms i MARK_MAX_PUNKTER.
    function markForenkla(d) {
        const k = PAPER_W / PAPER_H;
        const n = d.length / 2;
        const X = i => d[2 * i] * k, Y = i => d[2 * i + 1];
        for (let slat = MARK_SLAT; ; slat *= 2) {
            const kvar = new Uint8Array(n);
            kvar[0] = kvar[n - 1] = 1;
            const stack = [[0, n - 1]];
            while (stack.length) {
                const [a, b] = stack.pop();
                const dx = X(b) - X(a), dy = Y(b) - Y(a), l2 = dx * dx + dy * dy;
                let bast = -1, langst = slat;
                for (let i = a + 1; i < b; i++) {
                    const t = l2 ? Math.min(1, Math.max(0, ((X(i) - X(a)) * dx + (Y(i) - Y(a)) * dy) / l2)) : 0;
                    const av = Math.hypot(X(i) - X(a) - t * dx, Y(i) - Y(a) - t * dy);
                    if (av > langst) { langst = av; bast = i; }
                }
                if (bast >= 0) { kvar[bast] = 1; stack.push([a, bast], [bast, b]); }
            }
            const ut = [];
            for (let i = 0; i < n; i++) if (kvar[i]) ut.push(d[2 * i], d[2 * i + 1]);
            if (ut.length / 2 <= MARK_MAX_PUNKTER) return ut;
        }
    }

    function markVilaOm() {
        if (!markerar) return;
        if (markVila) clearTimeout(markVila);
        markVila = setTimeout(stangMarkering, MARK_VILA_MS);
    }

    function oppnaMarkering() {
        if (markerar || !startad || !pictureLoaded || vantarPaBild >= 0) return;
        holdEnd(false);
        slackTips();
        markerar = true;
        markDrag = [];
        markPagar.clear();
        markText.textContent = MARK_TEXT;
        markLage.classList.remove('kvitto', 'stanger');
        markLage.hidden = false;
        markLayout();
        markVilaOm();
    }

    // Tillbaka till den vanliga appen (AVBRYT, efter kvittot, eller när appen döljs).
    function stangMarkering() {
        if (markVila) { clearTimeout(markVila); markVila = null; }
        if (markStang) { clearTimeout(markStang); markStang = null; }
        markerar = false;
        markDrag = [];
        markPagar.clear();
        markLage.hidden = true;
        markLage.classList.remove('kvitto', 'stanger');
    }

    function markBorja(id, clientX, clientY) {
        if (markLage.classList.contains('kvitto') || markPagar.has(id)) return;
        if (markDrag.length + markPagar.size >= MARK_MAX_DRAG) return;
        markPagar.set(id, markPunkt(clientX, clientY));
        ritaMarkering();
    }

    function markDra(id, clientX, clientY) {
        const d = markPagar.get(id);
        if (!d) return;
        const p = markPunkt(clientX, clientY);
        if (markAvstand(d[d.length - 2], d[d.length - 1], p[0], p[1]) < MARK_STEG) return;
        d.push(p[0], p[1]);
        ritaMarkering();
    }

    function markSlut(id) {
        const d = markPagar.get(id);
        if (!d) return;
        markPagar.delete(id);
        const f = markForenkla(d);
        const redan = markDrag.reduce((n, x) => n + x.length / 2, 0);
        // Ryms inte draget inom taken tas det inte med (det försvinner från bilden).
        if (markDrag.length < MARK_MAX_DRAG && redan + f.length / 2 <= MARK_MAX_ALLA) markDrag.push(f);
        ritaMarkering();
    }

    let markTryck = 0;      // senaste fingret i lagret (musen som webbläsaren härmar efteråt räknas inte)
    markCanvas.addEventListener('touchstart', e => {
        e.preventDefault();
        markTryck = Date.now();
        for (let i = 0; i < e.changedTouches.length; i++) {
            const t = e.changedTouches[i];
            markBorja(t.identifier, t.clientX, t.clientY);
        }
    }, { passive: false });
    markCanvas.addEventListener('touchmove', e => {
        e.preventDefault();
        for (let i = 0; i < e.changedTouches.length; i++) {
            const t = e.changedTouches[i];
            markDra(t.identifier, t.clientX, t.clientY);
        }
    }, { passive: false });
    ['touchend', 'touchcancel'].forEach(typ => {
        markCanvas.addEventListener(typ, e => {
            markTryck = Date.now();
            for (let i = 0; i < e.changedTouches.length; i++) markSlut(e.changedTouches[i].identifier);
        });
    });
    // Mus (test på dator)
    markCanvas.addEventListener('mousedown', e => {
        if (e.button === 0 && Date.now() - markTryck > PIL_KLICK_MS) markBorja('mus', e.clientX, e.clientY);
    });
    window.addEventListener('mousemove', e => markDra('mus', e.clientX, e.clientY));
    window.addEventListener('mouseup', () => markSlut('mus'));
    // Inget i läget går vidare till appen under (penseln, knapparna).
    ['touchstart', 'mousedown'].forEach(typ => {
        markLage.addEventListener(typ, e => { e.stopPropagation(); markVilaOm(); });
    });

    // Kön i plattan: markeringar som inte kommit fram än.
    function lasKo() {
        try {
            const ko = JSON.parse(localStorage.getItem(MARK_KO));
            return Array.isArray(ko) ? ko : [];
        } catch (e) { return []; }
    }

    function skrivKo(ko) {
        try {
            if (ko.length) localStorage.setItem(MARK_KO, JSON.stringify(ko.slice(-MARK_KO_MAX)));
            else localStorage.removeItem(MARK_KO);
            return true;
        } catch (e) { return false; }
    }

    // Skickar kön, en markering i taget. En markering tas ur kön först när
    // mottagaren själv har svarat (huvudet X-Pensla-Markering): "sparad",
    // eller "ogiltig" (den kommer aldrig att tas emot). Allt annat (inget
    // nät, ingen mottagare, fullt för i dag) låter den ligga kvar till nästa
    // gång. Löftet är klart när försöket är gjort.
    let koGar = null;

    function skickaKo() {
        if (koGar) return koGar;
        koGar = (async () => {
            for (const m of lasKo()) {
                let svar = null;
                const stopp = new AbortController();
                const tid = setTimeout(() => stopp.abort(), MARK_VANTA_MS);
                try {
                    const res = await fetch(MARK_URL, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(m),
                        cache: 'no-store',
                        credentials: 'omit',
                        signal: stopp.signal
                    });
                    svar = res.headers.get('X-Pensla-Markering');
                } catch (e) { /* inget nät: ligger kvar */ }
                clearTimeout(tid);
                if (svar !== 'sparad' && svar !== 'ogiltig') break;
                skrivKo(lasKo().filter(x => x.id !== m.id));
            }
        })().then(() => { koGar = null; }, () => { koGar = null; });
        return koGar;
    }

    // Versionen står i sw.js (VERSION), som appen inte läser; cachens namn
    // är 'pensla-' + VERSION. Utan service worker blir den tom.
    function appVersion() {
        if (!window.caches) return Promise.resolve('');
        return caches.keys().then(namn => {
            const v = namn.map(n => /^pensla-(v\d+(?:-test)?)$/.exec(n)).filter(m => m).map(m => m[1]);
            v.sort((a, b) => parseInt(a.slice(1), 10) - parseInt(b.slice(1), 10));
            return v.length ? v[v.length - 1] : '';
        }).catch(() => '');
    }

    function markId() {
        const b = new Uint8Array(8);
        crypto.getRandomValues(b);
        return Array.from(b, x => x.toString(16).padStart(2, '0')).join('');
    }

    function markKvitto(text) {
        markText.textContent = text;
        if (markStang) clearTimeout(markStang);
        markStang = setTimeout(stangMarkering, 2000);
    }

    // KLAR: markeringen läggs i kön och skickas. Ett kort kvitto, sedan
    // tillbaka till den vanliga appen.
    async function markKlar() {
        if (!markerar || markLage.classList.contains('kvitto')) return;
        if (markVila) { clearTimeout(markVila); markVila = null; }
        markLage.classList.add('kvitto');
        Array.from(markPagar.keys()).forEach(markSlut);
        const pic = PICTURES[currentPicture];
        const m = {
            id: markId(),
            nr: pic.nr,
            namn: pic.namn,
            drag: markDrag.map(d => d.map(v => Math.round(v * 1000) / 1000)),
            bredd: MARK_BREDD,
            tid: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
            version: '',
            plattform: 'webb'
        };
        m.version = await appVersion();
        const ko = lasKo();
        ko.push(m);
        if (!skrivKo(ko)) { markKvitto('Gick inte att spara'); return; }
        markText.textContent = 'Skickar …';
        await skickaKo();
        if (!markerar) return;
        markKvitto(lasKo().some(x => x.id === m.id) ? 'Sparat ✓ Skickas senare' : 'Skickat ✓');
    }

    // AVBRYT: markeringen kastas. Lagret ligger kvar osynligt en kort stund
    // och sväljer det klick som webbläsaren kan skicka efter fingret, så att
    // det inte hamnar på en pil under.
    function markAvbryt() {
        if (!markerar || markLage.classList.contains('kvitto')) return;
        if (markVila) { clearTimeout(markVila); markVila = null; }
        markLage.classList.add('kvitto', 'stanger');
        markStang = setTimeout(stangMarkering, MARK_SVALJ_MS);
    }

    // KLAR och AVBRYT agerar när fingret släpps på knappen (som i Pensla N),
    // och glider fingret av knappen händer inget. De väntar inte på
    // webbläsarens klick, som kan utebli efter ett snabbt drag; klicket är
    // kvar för mus och gör inget en andra gång.
    [['mark-klar', markKlar], ['mark-avbryt', markAvbryt]].forEach(([id, gor]) => {
        const btn = document.getElementById(id);
        btn.addEventListener('click', gor);
        btn.addEventListener('touchend', e => {
            if (e.cancelable) e.preventDefault();
            const t = e.changedTouches[0];
            const r = btn.getBoundingClientRect();
            if (t.clientX >= r.left && t.clientX <= r.right && t.clientY >= r.top && t.clientY <= r.bottom) gor();
        });
    });
    window.addEventListener('online', () => { skickaKo(); });

    // --- Händelsebindningar (tidigare inline i HTML) ---
    document.getElementById('start-btn').addEventListener('click', startApp);

    // Bläddra mellan bilder: touchstart (med stopPropagation) agerar direkt
    // för touch, click för mus. Sätts en pil ner medan den andra hålls
    // (början på vuxengesten, se "Hemlig markering") går appen i stället
    // tillbaka till bilden som visades innan den första pilen trycktes, så
    // att gesten inte byter bild.
    // Klicket som webbläsaren kan skicka efter ett tryck med fingret (när
    // touchstart inte gick att avbryta) räknas inte, annars byttes två bilder.
    let pilTryck = 0;
    [[prevBtn, -1, nextBtn], [nextBtn, 1, prevBtn]].forEach(([btn, step, andra]) => {
        btn.addEventListener('click', () => {
            if (Date.now() - pilTryck < PIL_KLICK_MS) return;
            changePicture(step);
        });
        btn.addEventListener('touchstart', function(e) {
            e.preventDefault();
            e.stopPropagation();
            pilTryck = Date.now();
            const nere = nereKnappar();
            const bas = vantarPaBild >= 0 ? vantarPaBild : currentPicture;
            gestNer(e, btn);
            // En pil medan FÄRGLÄGG hålls: hållningen avbryts (annars
            // färglades den nya bilden).
            if (holdTimer && holdBtn === fillBtn) holdEnd(false);
            if (nere.has(andra)) {
                if (startad && foreBild >= 0 && foreBild !== bas) loadPicture(foreBild);
            } else {
                if (!nere.has(btn)) foreBild = bas;
                changePicture(step);
            }
            gestKoll();
        }, { passive: false });
    });

    // BÖRJA OM och FÄRGLÄGG — håll in
    // HOLD_MS (1 s, ALLA_HOLD_MS för att nollställa alla bilder). Touchstart stopPropagates så den inte målar; mousedown
    // för test på dator.
    function holdEnd(slappt) {
        endHold(slappt);
        restartBtn.classList.remove('holding');
        fillBtn.classList.remove('holding');
    }

    [restartBtn, fillBtn].forEach(btn => {
        const holdStart = () => {
            slackTips();
            startHold(btn);
            btn.classList.add('holding');
        };
        btn.addEventListener('touchstart', function(e) {
            e.stopPropagation();
            gestNer(e, btn);
            holdStart();
            gestKoll();     // alla tre nere: hållningen avbryts och gesten börjar
            e.preventDefault();
        }, { passive: false });

        // Touch-hållning avbryts om fingret glider utanför knappen (samma som
        // mouseleave för mus). Touch-event riktas alltid till elementet där
        // touchen startade, så touchmove på knappen räcker för en bounds-check.
        btn.addEventListener('touchmove', function(e) {
            const t = e.changedTouches[0];
            const r = this.getBoundingClientRect();
            if (t.clientX < r.left || t.clientX > r.right ||
                t.clientY < r.top || t.clientY > r.bottom) {
                holdEnd(false);
            }
        }, { passive: true });

        // Mus: mousedown startar hållningen (bara vänster knapp), mouseup/mouseleave avslutar
        btn.addEventListener('mousedown', function(e) {
            if (e.button !== 0) return;
            e.stopPropagation();
            holdStart();
        });
        btn.addEventListener('mouseleave', () => holdEnd(false));
    });

    // touchend/cancel på hela fönstret stänger hållningen (fingret lyfts)
    window.addEventListener('touchend', e => { gestUpp(e); holdEnd(true); }, { passive: true });
    window.addEventListener('touchcancel', e => { gestUpp(e); holdEnd(false); }, { passive: true });
    window.addEventListener('touchmove', gestFlytt, { passive: true });
    window.addEventListener('mouseup', () => holdEnd(true));

    // --- Back-knapp: håll användaren kvar i appen ---
    // Bakåt får aldrig lämna sidan — i pinnat läge strandar den installerade
    // appen annars på WebAPK:ns svarta splash-skärm, som bara går att lämna
    // genom att avpinna. Skydd i två lager:
    //
    // 1) Navigation API: avbryter traverseringen helt tyst. Androids
    //    system-bakåt undantas dock av Chrome (den ska alltid "fungera"),
    //    så i praktiken skyddar detta mest vid test i desktop-Chrome.
    // 2) Gest-armerad pushState-buffert: vid touch fylls historiken på med
    //    poster (samma URL, märkta med penslaDepth) upp till MAX_TRAP_DEPTH.
    //    Poster skapade MED gest respekteras av Chromes "history
    //    manipulation intervention", så varje bakåt-tryck kliver bara ner
    //    ett steg i bufferten — osynligt för användaren, ritytan lämnas
    //    inte. Nästa touch fyller på bufferten igen. Först på botten
    //    (poster utan penslaDepth) visas startskärmen och en sista
    //    fångstpost pushas. OBS: pushState inne i popstate (= utan gest)
    //    flaggas av interventionen så att NÄSTA bakåt lämnar sidan — därför
    //    görs det enbart som sista utväg på botten, aldrig i bufferten.
    const MAX_TRAP_DEPTH = 8;
    let backTrapNeedsArm = true;

    if (window.navigation) {
        navigation.addEventListener('navigate', (e) => {
            if (e.navigationType === 'traverse' && e.cancelable) {
                e.preventDefault();
            }
        });
    }

    history.pushState(null, '', location.href); // grundfälla (utan gest)

    window.addEventListener('popstate', (e) => {
        backTrapNeedsArm = true;
        if (e.state && typeof e.state.penslaDepth === 'number') {
            return; // landade i bufferten — tyst, barnet ritar vidare
        }
        history.pushState(null, '', location.href);
        showStartOverlay();
    });

    document.addEventListener('pointerdown', () => {
        if (!backTrapNeedsArm) return;
        backTrapNeedsArm = false;
        let depth = (history.state && typeof history.state.penslaDepth === 'number')
            ? history.state.penslaDepth + 1 : 0;
        while (depth < MAX_TRAP_DEPTH) {
            history.pushState({ penslaDepth: depth }, '', location.href);
            depth++;
        }
    }, { capture: true, passive: true });

    // Lås orientering till landskap. Låset biter bara i helskärm eller
    // installerad app — i vanligt webbläsarläge utan helskärm nekas det
    // tyst, därför görs ett nytt försök varje gång helskärm tas (se
    // fullscreenchange nedan).
    function lockOrientation() {
        if (screen.orientation && screen.orientation.lock) {
            screen.orientation.lock('landscape').catch(() => {});
        }
    }
    lockOrientation();

    document.addEventListener('fullscreenchange', () => {
        if (document.fullscreenElement) {
            startOverlay.style.display = 'none';
            lockOrientation();  // nu kan låset bita (kräver helskärm)
        } else if (!isInstalledApp()) {
            // Webbläsarläge: startskärmen är enda vägen tillbaka till
            // fullscreen. Installerad app visar INGEN startskärm här utan
            // återtar fullscreen tyst vid nästa touch — så bakåt-knappen
            // (som kastar ut ur helskärm) inte lämnar ritytan.
            showStartOverlay();
        }
        setTimeout(applyLayout, 100);
    });

    // Installerad app: återta immersive fullscreen (dolda systemfält) tyst
    // vid touch om det tappats — efter bakåt-tryck (som kastar ut ur helskärm
    // utan att kunna blockeras) eller skärmlåsningens väg via appväxlaren.
    // Barnet ritar bara vidare; fälten döljs igen vid nästa tryck. Kräver
    // användargest, därför på touchend. Nekar Android (t.ex. immersive
    // förbjudet i pinnat läge på vissa versioner) händer inget — layouten
    // klarar sig ändå.
    window.addEventListener('touchend', () => {
        if (isInstalledApp() && !document.fullscreenElement && document.fullscreenEnabled) {
            document.documentElement.requestFullscreen().catch(() => {});
        }
    }, { passive: true });

    // Mus (test på dator): dra med vänster knapp nedtryckt för att måla.
    // På touch-enheter ger preventDefault i touchstart inga mus-event.
    let mouseLast = null;
    viewCanvas.addEventListener('mousedown', e => {
        if (e.button !== 0) return;
        mouseLast = getPaperCoords(e.clientX, e.clientY);
        stamp(mouseLast.x, mouseLast.y);
        checkTouched();
    });
    window.addEventListener('mousemove', e => {
        if (!mouseLast) return;
        const p = getPaperCoords(e.clientX, e.clientY);
        stroke(mouseLast.x, mouseLast.y, p.x, p.y);
        mouseLast = p;
        checkTouched();
    });
    window.addEventListener('mouseup', () => { mouseLast = null; });

    viewCanvas.addEventListener('touchstart', onTouchStart, { passive: false });
    viewCanvas.addEventListener('touchmove', onTouchMove, { passive: false });
    window.addEventListener('touchend', onTouchEnd, { passive: true });
    window.addEventListener('touchcancel', onTouchEnd, { passive: true });

    // Blockera pinch-zoom på iOS — Safari har ignorerat user-scalable=no
    // ända sedan iOS 10. gesturestart är iOS-specifik och finns inte på
    // Android (där meta-taggen redan räcker), så detta är en no-op där.
    document.addEventListener('gesturestart', e => e.preventDefault());

    // Debounca layout-events så snabba resize/rotation-serier
    // bara triggar en enda omräkning per frame.
    let layoutPending = false;
    function debouncedLayout() {
        if (!layoutPending) {
            layoutPending = true;
            requestAnimationFrame(() => {
                applyLayout();
                layoutPending = false;
            });
        }
    }
    window.addEventListener('resize', debouncedLayout);
    window.addEventListener('orientationchange', debouncedLayout);
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) return;
        stangMarkering();
        aterstallKnappar();
        sparaNu();
        laddaOmOmNy();
    });
    window.addEventListener('pagehide', sparaNu);
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', debouncedLayout);
        window.visualViewport.addEventListener('scroll', debouncedLayout);
    }

    applyLayout();
    setTimeout(applyLayout, 50);

    // Första bilden visas när det sparade är inläst. Var bilden som visades
    // sist målad börjar appen på den (resten ligger kvar i blandad ordning).
    lasSparat().then(() => {
        let senast = 0;
        try { senast = +localStorage.getItem(SENAST_NYCKEL); } catch (e) { /* utan lagring */ }
        const i = PICTURES.findIndex(p => p.nr === senast);
        if (i > 0 && sparade.has(senast)) PICTURES.unshift(PICTURES.splice(i, 1)[0]);
        startad = true;
        loadPicture(0);
        skickaKo();     // markeringar som inte kom fram förra gången
    });

    // Service worker. Webbläsaren letar själv efter en ny version bara när
    // appen startas, så den letar också när man kommer tillbaka till appen
    // och var UPPDATERA_VAR medan den är öppen (ny version: laddaOmOmNy).
    const UPPDATERA_VAR = 10 * 60 * 1000;
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js').then(reg => {
            const leta = () => reg.update().catch(() => {});
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'visible') leta();
            });
            setInterval(leta, UPPDATERA_VAR);
            reg.addEventListener('updatefound', () => {
                const nw = reg.installing;
                if (!nw) return;
                nw.addEventListener('statechange', () => {
                    if (nw.state === 'installed' && navigator.serviceWorker.controller) {
                        nyVersion = true;
                        if (document.hidden || startOverlay.style.display !== 'none') laddaOmOmNy();
                    }
                });
            });
        }).catch(() => {});
    }
});
