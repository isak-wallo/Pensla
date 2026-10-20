document.addEventListener('DOMContentLoaded', () => {
    const viewCanvas = document.getElementById('viewCanvas');
    const vCtx = viewCanvas.getContext('2d');
    const canvasContainer = document.getElementById('canvas-container');

    // Element-referenser — deklarerade först så att funktionerna nedan
    // aldrig kan råka använda dem före deklarationen.
    const startOverlay = document.getElementById('start-overlay');
    const restartBtn = document.getElementById('restart-btn');
    const saveBtn = document.getElementById('save-btn');
    const app = document.getElementById('app');

    // Bilden är 1200x900 (landskap). Lager:
    //  - lineCanvas: bara konturerna (genomskinlig bakgrund)
    //  - colorCanvas: facit — själva färgbilden (syns aldrig, penseln
    //    hämtar färgen ur den pixel för pixel)
    //  - fillCanvas: det barnet målat fram (vitt där inget är målat)
    //  - viewCanvas: det som syns — fillCanvas med lineCanvas ovanpå
    // Områdena (ytor omringade av linjer) numreras en gång när bilden
    // laddas (`labels`), så att en yta kan fyllas i av sig själv.
    const PAPER_W = 1200;
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
    const fillImage = fCtx.createImageData(PAPER_W, PAPER_H);
    const fillPx = new Uint32Array(fillImage.data.buffer);

    // Omålat papper. Canvas-pixlar lagras som ABGR (little-endian) i en
    // Uint32Array; vitt är samma åt båda hållen.
    const PAPER = 0xFFFFFFFF;
    const BAKGRUND = '#dcecf8';   // runt bilden (samma ljusblå som Poppas himmel)

    let clearState = 0;
    let clearTimer = null;
    let viewRect = { left: 0, top: 0 };
    // --- Håll-in-logik för BÖRJA OM och SPARA ---
    // Man måste hålla fingret intryckt i HOLD_MS (ca 1 s). BÖRJA OM: första
    // hållningen visar SÄKER?, andra hållningen tömmer bilden. SPARA: en
    // hållning sparar bilden. En kort tryckning gör inget — så att ett barn
    // inte råkar sudda allt (eller fylla plattan med bilder) av misstag.
    const HOLD_MS = 1000;
    // Synka håll-animationens längd i CSS med HOLD_MS (--hold-ms används
    // av .sys-btn.holding i style.css).
    document.documentElement.style.setProperty('--hold-ms', HOLD_MS + 'ms');
    let holdTimer = null;

    function startHold(btn) {
        if (holdTimer) clearTimeout(holdTimer);
        holdTimer = setTimeout(() => {
            holdTimer = null;
            btn.classList.remove('holding');
            if (btn === saveBtn) sparaBild();
            else handleClear();
        }, HOLD_MS);
    }

    function endHold() {
        if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
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
    // 1200x900) och bilder/farg/NAMN.jpg (färgbilden som penseln trollar
    // fram). Konturerna ritas på lineCanvas och färgbilden på colorCanvas.

    // Bilderna. `fil` = NAMN i bilder/farg/. `keiws` = var den lilla kompisen
    // keIWs gömmer sig: (x, y) = mitt under fötterna, s = skala, `ytor` =
    // punkter i de ytor han syns i (han ritas bara där, så det som ligger
    // framför skymmer honom).
    const PICTURES = [
        { namn: 'Traktor', fil: 'traktor', keiws: { x: 420, y: 455, s: 0.32, ytor: [[420, 380]] } },          // i bakre rutan
        { namn: 'Grävare', fil: 'gravare', keiws: { x: 720, y: 462, s: 0.4, ytor: [[720, 400]] } },            // i hyttens fönster
        { namn: 'Sopbil', fil: 'sopbil', keiws: { x: 855, y: 512, s: 0.32, ytor: [[855, 420]] } },             // i hytten, bakom ratten
        { namn: 'Sopbil snett', fil: 'sopbil-snett', keiws: { x: 765, y: 505, s: 0.32, ytor: [[765, 440]] } }, // i vindrutan
        { namn: 'Traktor 2', fil: 'traktor2', keiws: { x: 781, y: 410, s: 0.32, ytor: [[781, 340]] } },        // i bakre rutan
        { namn: 'Flygplan', fil: 'flygplan', keiws: { x: 455, y: 476, s: 0.4, ytor: [[455, 420]] } },         // i cockpitrutan
        { namn: 'Flygplan 2', fil: 'flygplan2', keiws: { x: 760, y: 450, s: 0.4, ytor: [[760, 400]] } },       // i cockpitrutan
        { namn: 'Helikopter', fil: 'helikopter', keiws: { x: 440, y: 530, s: 0.45, ytor: [[440, 450]] } },     // i glaskupan
        { namn: 'Helikopter 2', fil: 'helikopter2', keiws: { x: 705, y: 468, s: 0.38, ytor: [[705, 410]] } }  // i fönstret, bredvid stolen
    ];

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
    // linjens anti-aliasade kant (ingen vit hinna).
    const LINE_ALPHA = 200;
    // Områden mindre än så här (pixlar) är bara små celler mellan
    // detaljstreck. De fylls i direkt när penseln nuddar dem.
    const MIN_REGION = 150;
    let labels = new Int32Array(PAPER_W * PAPER_H);
    let regionSize = [0];
    let regionTop = [0];      // omslutande rektangel för varje område, så att
    let regionBottom = [0];   // ifyllnad bara behöver gå igenom den
    let regionLeft = [0];
    let regionRight = [0];
    let facitPx = new Uint32Array(PAPER_W * PAPER_H);   // färgbilden pixel för pixel
    let regionPainted = new Int32Array(1);  // antal målade pixlar
    let regionDone = new Uint8Array(1);     // 1 = helt ifyllt (eller på väg)

    function labelRegions() {
        const W = PAPER_W, H = PAPER_H;
        const alpha = lCtx.getImageData(0, 0, W, H).data;
        labels.fill(0);
        for (let i = 0, n = W * H; i < n; i++) {
            if (alpha[i * 4 + 3] < LINE_ALPHA) labels[i] = -1;   // yta, ej besökt
        }
        regionSize = [0];
        regionTop = [0];
        regionBottom = [0];
        regionLeft = [0];
        regionRight = [0];
        let id = 0;
        for (let seed = 0, n = W * H; seed < n; seed++) {
            if (labels[seed] !== -1) continue;
            id++;
            floodLabel(seed, id);
        }
        regionPainted = new Int32Array(id + 1);
        regionDone = new Uint8Array(id + 1);
    }

    // Scanline-fyllning som numrerar ett sammanhängande område (4-grannar).
    function floodLabel(seed, id) {
        const W = PAPER_W, H = PAPER_H;
        const stack = [seed];
        let count = 0, top = H, bottom = 0, left = W, right = 0;
        while (stack.length) {
            const p = stack.pop();
            if (labels[p] !== -1) continue;
            const y = (p / W) | 0;
            const rowStart = y * W;
            let l = p, r = p;
            while (l > rowStart && labels[l - 1] === -1) l--;
            while (r < rowStart + W - 1 && labels[r + 1] === -1) r++;
            for (let i = l; i <= r; i++) labels[i] = id;
            count += r - l + 1;
            if (y < top) top = y;
            if (y > bottom) bottom = y;
            if (l - rowStart < left) left = l - rowStart;
            if (r - rowStart > right) right = r - rowStart;
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
        regionSize[id] = count;
        regionTop[id] = top;
        regionBottom[id] = bottom;
        regionLeft[id] = left;
        regionRight[id] = right;
    }

    // Penseln trollar fram själva färgbilden pixel för pixel (facitPx).
    // Helt vita pixlar flyttas ett snäpp från PAPER, som betyder omålad.
    function franFargbild() {
        facitPx = new Uint32Array(cCtx.getImageData(0, 0, PAPER_W, PAPER_H).data.buffer);
        for (let i = 0, len = facitPx.length; i < len; i++) {
            if (facitPx[i] === PAPER) facitPx[i] = 0xFFFEFEFE;
        }
    }

    // --- keIWs ---
    // Den lilla blå kompisen gömmer sig i varje bild, som krypet i Richard
    // Scarrys böcker. Han syns inte från början; när man målar där han är
    // poppar han upp, vinkar och blir kvar. Han ritas av sina klossar
    // (KEIWS i keiws.js, origo i kroppens övre vänstra hörn), så han blir
    // skarp i alla storlekar.
    const KEIWS_TRAFF = 40;     // så många målade pixlar på honom innan han poppar
    const KEIWS_UPP_MS = 600;   // upp bakom kanten med en liten studs …
    const KEIWS_VINKA = 700;    // … vinkar sedan (KEIWS.vinka) …
    const KEIWS_VINKA_MS = KEIWS.vinka.reduce((t, b) => t + b.tid, 0);
    const KEIWS_BLINK = KEIWS_VINKA + KEIWS_VINKA_MS + 300;   // … och blinkar en gång
    const KEIWS_MS = KEIWS_BLINK + 400;
    let keiws = null;           // { x, y, s, box, mask, tmp, hittad, start, traff }
    let keiwsYta = new Uint8Array(1);   // 1 för ytor han syns i

    // (x, y) = mitt under fötterna, s = skala.
    function ritaKeiws(ctx, x, y, s, rekt) {
        const X = v => Math.round(x + (v - 80) * s), Y = v => Math.round(y + (v - 204) * s);
        rekt.forEach(([x0, y0, x1, y1, f]) => {
            ctx.fillStyle = KEIWS.farger[f];
            ctx.fillRect(X(x0), Y(y0), X(x1) - X(x0), Y(y1) - Y(y0));
        });
    }

    // Förbereder keIWs för bilden: ruta, mask (de ytor han syns i) och
    // en arbetscanvas. Anropas efter labelRegions.
    function prepKeiws(c, hittad) {
        keiwsYta = new Uint8Array(regionSize.length);
        c.ytor.forEach(([px, py]) => {
            const l = labels[Math.round(py) * PAPER_W + Math.round(px)];
            if (l > 0) keiwsYta[l] = 1;
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
                if (keiwsYta[labels[(y0 + y) * PAPER_W + x0 + x]]) px[y * w + x] = 0xFF000000;
            }
        }
        mctx.putImageData(img, 0, 0);
        const tmp = document.createElement('canvas');
        tmp.width = w;
        tmp.height = h;
        keiws = { x: c.x, y: c.y, s: c.s, box: { x0, y0, x1, y1, w, h },
                  mask, tmp, hittad, start: -Infinity, traff: 0 };
    }

    function poppaKeiws() {
        if (!keiws || keiws.hittad) return;
        keiws.hittad = true;
        keiws.start = performance.now();
        requestRender();
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

    // Ritar keIWs maskad till sina ytor på ctx (i bildkoordinater).
    function ritaKeiwsMaskad(ctx, upp, rekt) {
        const b = keiws.box, tctx = keiws.tmp.getContext('2d');
        tctx.globalCompositeOperation = 'source-over';
        tctx.clearRect(0, 0, b.w, b.h);
        ritaKeiws(tctx, keiws.x - b.x0, keiws.y - b.y0 + (1 - upp) * 204 * keiws.s, keiws.s, rekt);
        tctx.globalCompositeOperation = 'destination-in';
        tctx.drawImage(keiws.mask, 0, 0);
        tctx.globalCompositeOperation = 'source-over';
        ctx.drawImage(keiws.tmp, b.x0, b.y0);
    }

    // Ritar keIWs (om han är hittad) på vCtx, som redan har bildens transform.
    // Returnerar true medan animationen pågår.
    function renderKeiws(now) {
        if (!keiws || !keiws.hittad) return false;
        const t = now - keiws.start;
        let upp = 1;
        if (t < KEIWS_UPP_MS) {
            const p = t / KEIWS_UPP_MS, k = 1.5;
            upp = 1 + (k + 1) * Math.pow(p - 1, 3) + k * Math.pow(p - 1, 2);
        }
        ritaKeiwsMaskad(vCtx, upp, keiwsLage(t));
        return t < KEIWS_MS;
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
        if (pictureLoaded) {
            finishFades();
            pictureState[currentPicture] = { fill: fillPx.slice(), keiws: !!(keiws && keiws.hittad) };
        }
        pictureLoaded = true;
        currentPicture = index;
        lCtx.setTransform(1, 0, 0, 1, 0, 0);
        lCtx.clearRect(0, 0, PAPER_W, PAPER_H);
        lCtx.drawImage(pic.img, 0, 0);
        cCtx.setTransform(1, 0, 0, 1, 0, 0);
        cCtx.clearRect(0, 0, PAPER_W, PAPER_H);
        cCtx.drawImage(pic.fimg, 0, 0, PAPER_W, PAPER_H);
        labelRegions();
        franFargbild();
        fades.length = 0;
        const saved = pictureState[index];
        prepKeiws(PICTURES[index].keiws, !!(saved && saved.keiws));
        if (saved) {
            fillPx.set(saved.fill);
            for (let i = 0, n = labels.length; i < n; i++) {
                const l = labels[i];
                if (l > 0 && fillPx[i] !== PAPER) regionPainted[l]++;
            }
            for (let l = 1; l < regionSize.length; l++) {
                if (regionPainted[l] === regionSize[l]) regionDone[l] = 1;
            }
        } else {
            fillPx.fill(PAPER);
        }
        fCtx.putImageData(fillImage, 0, 0);
        dirty = null;
        resetClearButton();
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
        // Ytor som håller på att fyllas i tonas fram ovanpå
        const now = performance.now();
        for (let k = fades.length - 1; k >= 0; k--) {
            const f = fades[k];
            if (ritaFade(f, now)) {
                commitRegion(f.id);
                fades.splice(k, 1);
                continue;
            }
            vCtx.drawImage(f.canvas, f.x, f.y);
        }
        if (dirty) {    // commitRegion ovan kan ha målat klart en yta
            fCtx.putImageData(fillImage, 0, 0, dirty.x0, dirty.y0,
                dirty.x1 - dirty.x0 + 1, dirty.y1 - dirty.y0 + 1);
            dirty = null;
            vCtx.drawImage(fillCanvas, 0, 0);
        }
        const keiwsRor = renderKeiws(now);
        vCtx.drawImage(lineCanvas, 0, 0);
        vCtx.setTransform(1, 0, 0, 1, 0, 0);
        if (fades.length || keiwsRor) requestRender();
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
    // Fingret är en pensel som målar fram ytornas givna färger (den kan inte
    // välja färg). När FYLL_ANDEL av en yta är målad fylls resten i av sig
    // själv: färgen rinner mjukt ut från det målade (startFade/ritaFade).
    const PENSEL = 28;         // penselns radie i bildpixlar
    const FYLL_ANDEL = 0.95;
    const FADE_MS = 600;        // kortaste ifyllnadstid …
    const FADE_MAX_MS = 1600;   // … och längsta
    const FADE_PER_PX = 12;     // ms per pixel som färgen ska rinna
    const FADE_BAND = 14;       // bredd på den mjuka kanten (px)
    const fades = [];          // { id, canvas, x, y, start }
    const touched = new Set(); // ytor som penseln nuddat i den här rörelsen

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
            const kollaKeiws = keiws && !keiws.hittad && y >= keiws.box.y0 && y <= keiws.box.y1;
            for (let i = y * W + xa, end = y * W + xb; i <= end; i++) {
                const l = labels[i];
                if (kollaKeiws && keiwsYta[l]) {
                    const x = i - y * W;
                    if (x >= keiws.box.x0 && x <= keiws.box.x1) keiws.traff++;
                }
                if (l <= 0 || regionDone[l] || fillPx[i] !== PAPER) continue;
                fillPx[i] = facitPx[i];
                regionPainted[l]++;
                touched.add(l);
            }
        }
        if (maxX >= minX) markDirty(minX, y0, maxX, y1);
    }

    // Penseldrag från a till b: klickar tätt längs sträckan.
    function stroke(ax, ay, bx, by) {
        const d = Math.hypot(bx - ax, by - ay);
        const steg = Math.max(1, Math.ceil(d / (PENSEL * 0.35)));
        for (let k = 1; k <= steg; k++) {
            stamp(ax + (bx - ax) * k / steg, ay + (by - ay) * k / steg);
        }
    }

    // Kollar om någon av de nyss målade ytorna nått gränsen.
    function checkTouched() {
        touched.forEach(l => {
            if (regionDone[l]) return;
            if (regionSize[l] < MIN_REGION) {
                regionDone[l] = 1;
                commitRegion(l);
            } else if (regionPainted[l] >= regionSize[l] * FYLL_ANDEL) {
                startFade(l);
            }
        });
        touched.clear();
        if (keiws && !keiws.hittad && keiws.traff >= KEIWS_TRAFF) poppaKeiws();
        if (clearState) resetClearButton();
        requestRender();
    }

    // Lägger det som är kvar av ytan på en egen liten canvas som tonas fram
    // ovanpå; när toningen är klar skrivs den in i fillPx (commitRegion).
    function startFade(id) {
        regionDone[id] = 1;
        if (keiwsYta[id]) poppaKeiws();
        const W = PAPER_W;
        const x0 = regionLeft[id], y0 = regionTop[id];
        const w = regionRight[id] - x0 + 1, h = regionBottom[id] - y0 + 1;
        const c = document.createElement('canvas');
        c.width = w;
        c.height = h;
        const ctx = c.getContext('2d');
        const img = ctx.createImageData(w, h);
        const px = new Uint32Array(img.data.buffer);
        // Färgen rinner ut från det som redan är målat: bredden-först genom
        // de omålade pixlarna, i avståndsordning (ordning + avstånd sparas).
        const dist = new Int32Array(w * h).fill(-1);
        const ordning = [];
        for (let y = 0; y < h; y++) {
            const row = (y0 + y) * W + x0;
            for (let x = 0; x < w; x++) {
                const i = row + x;
                if (labels[i] === id && fillPx[i] !== PAPER) dist[y * w + x] = 0;
            }
        }
        for (let k = 0; k < w * h; k++) {
            if (dist[k] !== 0) continue;
            const x = k % w;
            if ((x > 0 && dist[k - 1] < 0) || (x < w - 1 && dist[k + 1] < 0) ||
                (k >= w && dist[k - w] < 0) || (k < w * h - w && dist[k + w] < 0)) ordning.push(k);
        }
        const fargAv = (k) => {
            const i = (y0 + ((k / w) | 0)) * W + x0 + (k % w);
            return facitPx[i];
        };
        // Avstånd med 8 grannar (5 rakt, 7 snett) i en hink-kö, så att
        // kanten blir rund i stället för spetsig. Avståndet räknas i femtedels px.
        const hinkar = [ordning.slice()];
        ordning.length = 0;
        for (let d = 0; d < hinkar.length; d++) {
            const hink = hinkar[d];
            if (!hink) continue;
            for (let n = 0; n < hink.length; n++) {
                const k = hink[n];
                if (dist[k] !== d) continue;           // redan nådd kortare väg
                ordning.push(k);
                const x = k % w;
                for (let dy = -1; dy <= 1; dy++) {
                    for (let dx = -1; dx <= 1; dx++) {
                        if (!dx && !dy) continue;
                        const xx = x + dx;
                        if (xx < 0 || xx >= w) continue;
                        const q = k + dy * w + dx;
                        if (q < 0 || q >= w * h) continue;
                        const nd = d + (dx && dy ? 7 : 5);
                        if (dist[q] !== -1 && dist[q] <= nd) continue;
                        const i = (y0 + ((q / w) | 0)) * W + x0 + xx;
                        if (labels[i] !== id || (dist[q] === 0)) continue;
                        dist[q] = nd;
                        (hinkar[nd] || (hinkar[nd] = [])).push(q);
                    }
                }
            }
            hinkar[d] = null;
        }
        for (let k = 0; k < w * h; k++) if (dist[k] > 0) dist[k] = (dist[k] / 5) | 0;
        // Bara de omålade pixlarna ska tonas fram (ordning börjar med kanten av det målade)
        const kvar = ordning.filter(k => dist[k] > 0);
        // Omålade pixlar som inte nås (ingen målad granne) läggs sist
        for (let y = 0; y < h; y++) {
            const row = (y0 + y) * W + x0;
            for (let x = 0; x < w; x++) {
                const k = y * w + x;
                if (dist[k] === -1 && labels[row + x] === id && fillPx[row + x] === PAPER) kvar.push(k);
            }
        }
        const maxD = kvar.length ? Math.max(1, dist[kvar[kvar.length - 1]]) : 1;
        const tid = Math.min(FADE_MAX_MS, Math.max(FADE_MS, 300 + maxD * FADE_PER_PX));
        fades.push({ id, canvas: c, ctx, img, px, x: x0, y: y0, w, kvar, dist, maxD, fargAv,
            klara: 0, start: performance.now(), tid });
    }

    // Flyttar fram färgens kant: pixlar bakom kanten blir helt täckta, de i
    // kantbandet (FADE_BAND px) halvgenomskinliga, så kanten blir mjuk.
    function ritaFade(f, now) {
        const t = Math.min(1, (now - f.start) / f.tid);
        const p = 1 - (1 - t) * (1 - t);                // snabb start, mjukt slut
        const front = p * (f.maxD + FADE_BAND);
        let x0 = f.w, y0 = 1e9, x1 = -1, y1 = -1;
        let k = f.klara;
        for (; k < f.kvar.length; k++) {
            const q = f.kvar[k], d = f.dist[q] < 0 ? f.maxD : f.dist[q];
            if (d > front) break;
            const a = Math.min(1, (front - d) / FADE_BAND);
            const c = f.fargAv(q);
            f.px[q] = ((Math.round(a * 255) << 24) | (c & 0xFFFFFF)) >>> 0;
            const x = q % f.w, y = (q / f.w) | 0;
            if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
        }
        // pixlarna längst bak i bandet är nu helt täckta och behöver inte röras igen
        while (f.klara < k) {
            const q = f.kvar[f.klara], d = f.dist[q] < 0 ? f.maxD : f.dist[q];
            if (front - d < FADE_BAND) break;
            f.klara++;
        }
        if (x1 >= 0) f.ctx.putImageData(f.img, 0, 0, x0, y0, x1 - x0 + 1, y1 - y0 + 1);
        return t >= 1;
    }

    // Fyller hela ytan i fillPx (direkt, utan toning).
    function commitRegion(id) {
        const W = PAPER_W;
        const x0 = regionLeft[id], x1 = regionRight[id];
        const y0 = regionTop[id], y1 = regionBottom[id];
        for (let y = y0; y <= y1; y++) {
            for (let i = y * W + x0, end = y * W + x1; i <= end; i++) {
                if (labels[i] === id) fillPx[i] = facitPx[i];
            }
        }
        regionPainted[id] = regionSize[id];
        markDirty(x0, y0, x1, y1);
    }

    // Gör klart alla pågående toningar direkt (inför bildbyte).
    function finishFades() {
        fades.forEach(f => commitRegion(f.id));
        fades.length = 0;
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
    // och konturerna) som en PNG i 1200x900. Laddas ner till plattans
    // Hämtade filer (Downloads), där den syns i Galleri/Filer.
    let sparaTimer = null;
    function sparaBild() {
        finishFades();
        if (dirty) { fCtx.putImageData(fillImage, 0, 0); dirty = null; }
        const c = document.createElement('canvas');
        c.width = PAPER_W;
        c.height = PAPER_H;
        const ctx = c.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, PAPER_W, PAPER_H);
        ctx.drawImage(fillCanvas, 0, 0);
        if (keiws && keiws.hittad) ritaKeiwsMaskad(ctx, 1, KEIWS.stilla);
        ctx.drawImage(lineCanvas, 0, 0);
        const d = new Date(), tv = n => String(n).padStart(2, '0');
        const namn = 'farga-' + PICTURES[currentPicture].namn.toLowerCase()
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

    // BÖRJA OM — tvåstegs med hållning: första hållningen (1 s) visar
    // "SÄKER?" (5 s timeout / nollställs om man målar), andra hållningen
    // (1 s) tömmer bilden.
    function handleClear() {
        if (clearState === 0) {
            clearState = 1;
            restartBtn.textContent = 'SÄKER?';
            restartBtn.classList.add('confirm');
            clearTimer = setTimeout(resetClearButton, 5000);
        } else {
            fades.length = 0;
            if (keiws) { keiws.hittad = false; keiws.traff = 0; }
            fillPx.fill(PAPER);
            regionPainted.fill(0);
            regionDone.fill(0);
            fCtx.putImageData(fillImage, 0, 0);
            dirty = null;
            requestRender();
            resetClearButton();
        }
    }

    function resetClearButton() {
        clearState = 0;
        if (clearTimer) {
            clearTimeout(clearTimer);
            clearTimer = null;
        }
        if (restartBtn) {
            restartBtn.textContent = 'BÖRJA OM';
            restartBtn.classList.remove('confirm');
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
    // och när fullscreen tappats, och BÖRJA MÅLA-knappen (en äkta gest) tar
    // tillbaka in i fullscreen. Det målade påverkas inte.
    function showStartOverlay() {
        startOverlay.style.display = 'flex';
        resetClearButton();
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

    // BÖRJA OM (två hållningar, SÄKER?) och SPARA (en hållning) — håll in
    // HOLD_MS (1 s). Touchstart stopPropagates så den inte målar; mousedown
    // för test på dator.
    function holdEnd() {
        endHold();
        restartBtn.classList.remove('holding');
        saveBtn.classList.remove('holding');
    }

    [restartBtn, saveBtn].forEach(btn => {
        const holdStart = () => {
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
                holdEnd();
            }
        }, { passive: true });

        // Mus: mousedown startar hållningen (bara vänster knapp), mouseup/mouseleave avslutar
        btn.addEventListener('mousedown', function(e) {
            if (e.button !== 0) return;
            e.stopPropagation();
            holdStart();
        });
        btn.addEventListener('mouseleave', holdEnd);
    });

    // touchend/cancel på hela fönstret stänger hållningen (fingret lyfts)
    window.addEventListener('touchend', holdEnd, { passive: true });
    window.addEventListener('touchcancel', holdEnd, { passive: true });
    window.addEventListener('mouseup', holdEnd);

    // --- Back-knapp: håll användaren kvar i appen ---
    // Bakåt får aldrig lämna sidan — i pinnat läge strandar den installerade
    // appen annars på WebAPK:ns svarta splash-skärm, som bara går att lämna
    // genom att avpinna. Skydd i två lager:
    //
    // 1) Navigation API: avbryter traverseringen helt tyst. Androids
    //    system-bakåt undantas dock av Chrome (den ska alltid "fungera"),
    //    så i praktiken skyddar detta mest vid test i desktop-Chrome.
    // 2) Gest-armerad pushState-buffert: vid touch fylls historiken på med
    //    poster (samma URL, märkta med fargaDepth) upp till MAX_TRAP_DEPTH.
    //    Poster skapade MED gest respekteras av Chromes "history
    //    manipulation intervention", så varje bakåt-tryck kliver bara ner
    //    ett steg i bufferten — osynligt för användaren, ritytan lämnas
    //    inte. Nästa touch fyller på bufferten igen. Först på botten
    //    (poster utan fargaDepth) visas startskärmen och en sista
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
        if (e.state && typeof e.state.fargaDepth === 'number') {
            return; // landade i bufferten — tyst, barnet ritar vidare
        }
        history.pushState(null, '', location.href);
        showStartOverlay();
    });

    document.addEventListener('pointerdown', () => {
        if (!backTrapNeedsArm) return;
        backTrapNeedsArm = false;
        let depth = (history.state && typeof history.state.fargaDepth === 'number')
            ? history.state.fargaDepth + 1 : 0;
        while (depth < MAX_TRAP_DEPTH) {
            history.pushState({ fargaDepth: depth }, '', location.href);
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
        if (document.hidden) resetClearButton();
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
