document.addEventListener('DOMContentLoaded', () => {
    const viewCanvas = document.getElementById('viewCanvas');
    const vCtx = viewCanvas.getContext('2d');
    const canvasContainer = document.getElementById('canvas-container');

    // Element-referenser — deklarerade först så att funktionerna nedan
    // aldrig kan råka använda dem före deklarationen.
    const startOverlay = document.getElementById('start-overlay');
    const restartBtn = document.getElementById('restart-btn');
    const saveBtn = document.getElementById('save-btn');
    const fillBtn = document.getElementById('fill-btn');
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
    // alla bilder; saveState 1 = SPARA väntar på andra hållningen.
    let clearState = 0;
    let saveState = 0;
    let clearTimer = null;
    let viewRect = { left: 0, top: 0 };
    // --- Håll-in-logik för BÖRJA OM, SPARA och FÄRGLÄGG ---
    // Man måste hålla fingret intryckt i HOLD_MS (ca 1 s). BÖRJA OM: en
    // hållning tömmer bilden, och sedan visar knappen en stund (ALLA_MS) att
    // en lång hållning (ALLA_HOLD_MS) nollställer alla bilder. SPARA: första
    // hållningen visar "HÅLL INNE IGEN FÖR ATT SPARA", andra sparar bilden.
    // FÄRGLÄGG: en hållning trollar fram hela färgbilden (BÖRJA OM ångrar).
    // En kort tryckning gör inget — så att ett barn inte råkar sudda allt
    // (eller fylla plattan med bilder) av misstag — utom att knappen en
    // stund (TIPS_MS) visar att man ska hålla inne.
    const HOLD_MS = 1000;
    const ALLA_MS = 4000;
    const ALLA_HOLD_MS = 4000;
    const SAVE_MS = 5000;   // så länge SPARA väntar på andra hållningen
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
        const ms = btn === restartBtn && clearState ? ALLA_HOLD_MS : HOLD_MS;
        btn.style.setProperty('--hold-ms', ms + 'ms');
        // Väntar knappen på andra hållningen får tiden inte ta slut mitt i den
        if (vantar(btn) && clearTimer) { clearTimeout(clearTimer); clearTimer = null; }
        holdTimer = setTimeout(() => {
            holdTimer = null;
            btn.classList.remove('holding');
            if (btn === saveBtn) handleSave();
            else if (btn === fillBtn) fargaHela();
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
                clearTimer = setTimeout(aterstallKnappar, holdBtn === saveBtn ? SAVE_MS : ALLA_MS);
            }
        }
    }

    function vantar(btn) {
        return (btn === saveBtn && saveState) || (btn === restartBtn && clearState);
    }

    function knappText(btn) {
        if (btn === saveBtn) return saveState ? 'HÅLL INNE IGEN FÖR ATT SPARA' : 'SPARA';
        if (btn === fillBtn) return 'FÄRGLÄGG';
        return clearState ? 'HÅLL INNE LÄNGE FÖR ATT NOLLSTÄLLA ALLA BILDER' : 'BÖRJA OM';
    }

    function visaHallTips(btn) {
        slackTips();
        // Väntar knappen redan på en andra hållning står det där vad man ska göra
        if (vantar(btn)) return;
        btn.textContent = 'HÅLL INNE FÖR ATT ' +
            (btn === saveBtn ? 'SPARA' : btn === fillBtn ? 'FÄRGLÄGGA' : 'BÖRJA OM');
        btn.classList.add('tips');
        tipsTimer = setTimeout(slackTips, TIPS_MS);
    }

    function slackTips() {
        if (tipsTimer) { clearTimeout(tipsTimer); tipsTimer = null; }
        [restartBtn, saveBtn, fillBtn].forEach(btn => {
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
    const PICTURES = ALLA_BILDER.filter(b => AKTIVA.includes(b.nr));

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
    const KEIWS_UPP_MS = 600;   // upp bakom kanten med en liten studs …
    const KEIWS_VINKA = 700;    // … vinkar sedan (KEIWS.vinka) …
    const KEIWS_VINKA_MS = KEIWS.vinka.reduce((t, b) => t + b.tid, 0);
    const KEIWS_BLINK = KEIWS_VINKA + KEIWS_VINKA_MS + 300;   // … och blinkar en gång
    const KEIWS_MS = KEIWS_BLINK + 400;
    const FEST_PAUS_MS = 300;   // från sista kompisens blink till festvinkningen
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

    // Varje bild minns det man målat medan appen är öppen, så man kan
    // bläddra fram och tillbaka utan att förlora något.
    const pictureState = [];
    let pictureLoaded = false;

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
        if (pictureLoaded) {
            pictureState[currentPicture] = { fill: fillPx.slice(), hittade: kompisar.map(k => k.hittad) };
        }
        pictureLoaded = true;
        currentPicture = index;
        setPaperSize(Math.round(PAPER_H * pic.fimg.naturalWidth / pic.fimg.naturalHeight));
        lCtx.setTransform(1, 0, 0, 1, 0, 0);
        lCtx.clearRect(0, 0, PAPER_W, PAPER_H);
        lCtx.drawImage(pic.img, 0, 0, PAPER_W, PAPER_H);
        cCtx.setTransform(1, 0, 0, 1, 0, 0);
        cCtx.clearRect(0, 0, PAPER_W, PAPER_H);
        cCtx.drawImage(pic.fimg, 0, 0, PAPER_W, PAPER_H);
        labelRegions();
        franFargbild();
        const saved = pictureState[index];
        prepKeiws(PICTURES[index], saved && saved.hittade);
        if (saved) {
            fillPx.set(saved.fill);
        } else {
            fillPx.fill(PAPER);
        }
        fCtx.putImageData(fillImage, 0, 0);
        dirty = null;
        aterstallKnappar();
        requestRender();
    }

    function changePicture(step) {
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
    const FARGA_MS = 1200;
    let fargaAnim = null;

    function fargaHela() {
        stoppaFarga();
        if (clearState || saveState) aterstallKnappar();
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
        kollaKompisar();
        if (clearState || saveState) aterstallKnappar();
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

    // --- SPARA ---
    // Sparar bilden som den ser ut nu (det målade, keIWs om han är hittad,
    // och konturerna) som en PNG i bildens storlek (oftast 1200x900). Laddas ner till plattans
    // Hämtade filer (Downloads), där den syns i Galleri/Filer.
    let sparaTimer = null;
    function sparaBild() {
        if (dirty) { fCtx.putImageData(fillImage, 0, 0); dirty = null; }
        const c = document.createElement('canvas');
        c.width = PAPER_W;
        c.height = PAPER_H;
        const ctx = c.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, PAPER_W, PAPER_H);
        ctx.drawImage(fillCanvas, 0, 0);
        kompisar.forEach(k => { if (k.hittad) ritaKeiwsMaskad(ctx, k, 1, KEIWS.stilla); });
        ctx.drawImage(lineCanvas, 0, 0);
        const d = new Date(), tv = n => String(n).padStart(2, '0');
        const namn = 'pensla-' + PICTURES[currentPicture].namn.toLowerCase()
            .replace(/[åä]/g, 'a').replace(/ö/g, 'o').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') +
            '-' + d.getFullYear() + tv(d.getMonth() + 1) + tv(d.getDate()) + '-' +
            tv(d.getHours()) + tv(d.getMinutes()) + tv(d.getSeconds()) + '.png';
        c.toBlob(blob => {
            if (!blob) return;
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = namn;
            document.body.appendChild(a);
            a.click();
            a.remove();
            setTimeout(() => URL.revokeObjectURL(url), 10000);
        }, 'image/png');
        // Kvittens på knappen en stund
        saveBtn.textContent = 'SPARAD ✓';
        saveBtn.classList.add('sparad');
        if (sparaTimer) clearTimeout(sparaTimer);
        sparaTimer = setTimeout(() => {
            saveBtn.textContent = 'SPARA';
            saveBtn.classList.remove('sparad');
        }, 2000);
    }

    // SPARA — tvåstegs med hållning: första hållningen (1 s) visar "HÅLL
    // INNE IGEN FÖR ATT SPARA" (SAVE_MS timeout / nollställs om man målar),
    // andra hållningen (1 s) sparar.
    function handleSave() {
        if (saveState === 0) {
            aterstallKnappar();
            saveState = 1;
            saveBtn.textContent = knappText(saveBtn);
            saveBtn.classList.add('confirm', 'lang');
            clearTimer = setTimeout(aterstallKnappar, SAVE_MS);
        } else {
            aterstallKnappar();
            sparaBild();
        }
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
            pictureState.length = 0;
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
        requestRender();
    }

    function aterstallKnappar() {
        clearState = 0;
        saveState = 0;
        if (clearTimer) {
            clearTimeout(clearTimer);
            clearTimer = null;
        }
        if (restartBtn) {
            restartBtn.textContent = 'BÖRJA OM';
            restartBtn.classList.remove('confirm', 'tips', 'lang');
        }
        if (saveBtn && saveBtn.classList.contains('confirm')) {
            saveBtn.textContent = 'SPARA';
            saveBtn.classList.remove('confirm', 'lang');
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
        aterstallKnappar();
    }

    // --- Händelsebindningar (tidigare inline i HTML) ---
    document.getElementById('start-btn').addEventListener('click', startApp);

    // Bläddra mellan bilder: touchstart (med stopPropagation) agerar direkt
    // för touch, click för mus.
    [['prev-btn', -1], ['next-btn', 1]].forEach(([id, step]) => {
        const btn = document.getElementById(id);
        btn.addEventListener('click', () => changePicture(step));
        btn.addEventListener('touchstart', function(e) {
            e.preventDefault();
            e.stopPropagation();
            changePicture(step);
        }, { passive: false });
    });

    // BÖRJA OM, SPARA (två hållningar) och FÄRGLÄGG (en hållning) — håll in
    // HOLD_MS (1 s, ALLA_HOLD_MS för att nollställa alla bilder). Touchstart stopPropagates så den inte målar; mousedown
    // för test på dator.
    function holdEnd(slappt) {
        endHold(slappt);
        restartBtn.classList.remove('holding');
        saveBtn.classList.remove('holding');
        fillBtn.classList.remove('holding');
    }

    [restartBtn, saveBtn, fillBtn].forEach(btn => {
        const holdStart = () => {
            slackTips();
            startHold(btn);
            btn.classList.add('holding');
        };
        btn.addEventListener('touchstart', function(e) {
            e.stopPropagation();
            holdStart();
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
    window.addEventListener('touchend', () => holdEnd(true), { passive: true });
    window.addEventListener('touchcancel', () => holdEnd(false), { passive: true });
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
        if (document.hidden) aterstallKnappar();
    });
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', debouncedLayout);
        window.visualViewport.addEventListener('scroll', debouncedLayout);
    }

    loadPicture(0);
    applyLayout();
    setTimeout(applyLayout, 50);

    // Registrera service worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js').then(reg => {
            reg.addEventListener('updatefound', () => {
                const nw = reg.installing;
                if (!nw) return;
                nw.addEventListener('statechange', () => {
                    if (nw.state === 'installed' && navigator.serviceWorker.controller) {
                        window.location.reload();
                    }
                });
            });
        }).catch(() => {});
    }
});
