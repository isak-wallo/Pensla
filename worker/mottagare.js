// Pensla: mottagare för de hemliga markeringarna (app.js, "Hemlig markering").
//
// Workern ligger framför de statiska filerna men körs bara för /api/* och
// för adresser som inte är en fil (wrangler.jsonc: run_worker_first). Allt
// annat serveras av Cloudflare precis som utan worker, och det som ändå
// hamnar här skickas vidare till filerna (env.ASSETS), så att 404 och
// testmiljöns single-page-application-svar blir som förut.
//
// POST /api/markering tar emot en markering från appen och sparar den i D1
// (bindningen DB, tabellen i worker/schema.sql). Det finns ingen adress att
// LÄSA markeringar på: de läses bara med wrangler mot databasen
// (verktyg/markeringar.py --server), som kräver inloggning på kontot.
//
// Mottagaren är öppen mot internet, så:
//  - bara POST med JSON från sidans egen adress (Origin), högst MAX_KROPP byte,
//  - bara kända fält, bildnummer som finns i bilder.js, högst MAX_DRAG drag
//    med högst MAX_PUNKTER punkter var (MAX_ALLA sammanlagt) och tal i 0–1,
//    penselbredd, tid och version i fasta format (samma tak som i app.js),
//  - ingen fri text sparas: bildens namn slås upp här ur bilder.js (det som
//    appen skickar används inte), och inget om avsändaren sparas (ingen
//    IP-adress, ingen webbläsare),
//  - högst MAX_PER_DYGN nya per dygn och MAX_TOTALT sammanlagt (sedan svarar
//    den "full" tills någon har läst och rensat).
//
// Svaret har alltid huvudet X-Pensla-Markering: sparad, ogiltig, full eller
// stangd. Appen tar bara en markering ur sin kö på "sparad" eller "ogiltig".

const MAX_KROPP = 10240;
const MAX_DRAG = 20;
const MAX_PUNKTER = 100;       // per drag
const MAX_ALLA = 600;          // punkter sammanlagt
const MAX_PER_DYGN = 60;
const MAX_TOTALT = 500;
const DYGN_MS = 24 * 60 * 60 * 1000;
const BILDER_MS = 5 * 60 * 1000;      // så länge minns workern listan ur bilder.js
const TIDIGAST = Date.UTC(2026, 0, 1);
const FALT = ['id', 'nr', 'namn', 'drag', 'bredd', 'tid', 'version', 'plattform'];

let bilder = null;        // Map nr -> namn
let bilderLasta = 0;

function svar(status, lage) {
    return new Response(null, {
        status,
        headers: { 'X-Pensla-Markering': lage, 'Cache-Control': 'no-store' }
    });
}

// Bildernas nummer och namn ur den publicerade bilder.js (samma fil som appen läser).
async function kandaBilder(request, env) {
    const nu = Date.now();
    if (bilder && nu - bilderLasta < BILDER_MS) return bilder;
    const res = await env.ASSETS.fetch(new Request(new URL('/bilder.js', request.url)));
    if (!res.ok) return bilder;
    const text = await res.text();
    const nya = new Map();
    for (const m of text.matchAll(/\{ nr: (\d+), namn: '([^'\\]{1,60})'/g)) nya.set(Number(m[1]), m[2]);
    if (nya.size) { bilder = nya; bilderLasta = nu; }
    return bilder;
}

// Den kontrollerade markeringen (bara det som sparas), eller null.
function kontrollera(m, kanda) {
    if (!m || typeof m !== 'object' || Array.isArray(m)) return null;
    if (Object.keys(m).some(k => !FALT.includes(k))) return null;
    if (typeof m.id !== 'string' || !/^[0-9a-f]{16}$/.test(m.id)) return null;
    if (!Number.isInteger(m.nr) || !kanda.has(m.nr)) return null;
    if (m.namn !== undefined && (typeof m.namn !== 'string' || m.namn.length > 60)) return null;
    // Dragen: [[x0, y0, x1, y1, ...] ...], normerade punkter (ett drag kan vara en enda punkt)
    if (!Array.isArray(m.drag) || m.drag.length > MAX_DRAG) return null;
    const drag = [];
    let alla = 0;
    for (const d of m.drag) {
        if (!Array.isArray(d) || d.length < 2 || d.length % 2 || d.length > 2 * MAX_PUNKTER) return null;
        if (d.some(v => typeof v !== 'number' || !Number.isFinite(v) || v < 0 || v > 1)) return null;
        alla += d.length / 2;
        if (alla > MAX_ALLA) return null;
        drag.push(d.map(v => Math.round(v * 1000) / 1000));
    }
    if (typeof m.bredd !== 'number' || !Number.isFinite(m.bredd) || m.bredd < 0.005 || m.bredd > 0.2) return null;
    if (typeof m.tid !== 'string' || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(m.tid)) return null;
    const t = Date.parse(m.tid);
    if (!Number.isFinite(t) || t < TIDIGAST || t > Date.now() + DYGN_MS) return null;
    if (typeof m.version !== 'string' || !/^(v\d{1,5}(-test)?|native-v\d{1,5})?$/.test(m.version)) return null;
    if (m.plattform !== 'webb' && m.plattform !== 'native') return null;
    return { id: m.id, nr: m.nr, namn: kanda.get(m.nr), drag: JSON.stringify(drag),
             bredd: Math.round(m.bredd * 1000) / 1000, tid: m.tid, version: m.version, plattform: m.plattform };
}

async function taEmot(request, env, url) {
    if (request.method !== 'POST') return svar(405, 'ogiltig');
    if (request.headers.get('Origin') !== url.origin) return svar(403, 'ogiltig');
    if (!/^application\/json\b/i.test(request.headers.get('Content-Type') || '')) return svar(415, 'ogiltig');
    if (Number(request.headers.get('Content-Length') || 0) > MAX_KROPP) return svar(413, 'ogiltig');
    if (!env.DB) return svar(503, 'stangd');      // databasen är inte kopplad än

    // Kroppen läses med tak, även om Content-Length saknas eller ljuger.
    const delar = [];
    let langd = 0;
    if (request.body) {
        const lasare = request.body.getReader();
        for (;;) {
            const { done, value } = await lasare.read();
            if (done) break;
            langd += value.byteLength;
            if (langd > MAX_KROPP) { await lasare.cancel(); return svar(413, 'ogiltig'); }
            delar.push(value);
        }
    }
    const kropp = new Uint8Array(langd);
    let pos = 0;
    for (const d of delar) { kropp.set(d, pos); pos += d.byteLength; }
    let m = null;
    try {
        m = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(kropp));
    } catch (e) { return svar(400, 'ogiltig'); }

    const kanda = await kandaBilder(request, env);
    if (!kanda) return svar(503, 'stangd');
    const ok = kontrollera(m, kanda);
    if (!ok) return svar(400, 'ogiltig');

    const nu = Date.now();
    const miljo = url.hostname.startsWith('test.') ? 'test' : 'skarp';
    // Taken hålls i samma sats som skrivningen. En markering som redan
    // finns (appen fick aldrig svaret förra gången) räknas som sparad.
    const res = await env.DB.prepare(
        'INSERT OR IGNORE INTO markering (id, mottagen, miljo, nr, namn, drag, bredd, tid, version, plattform) ' +
        'SELECT ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10 ' +
        'WHERE (SELECT COUNT(*) FROM markering) < ?11 ' +
        'AND (SELECT COUNT(*) FROM markering WHERE mottagen > ?12) < ?13'
    ).bind(ok.id, nu, miljo, ok.nr, ok.namn, ok.drag, ok.bredd, ok.tid, ok.version, ok.plattform,
           MAX_TOTALT, nu - DYGN_MS, MAX_PER_DYGN).run();
    if (res.meta && res.meta.changes > 0) return svar(204, 'sparad');
    const finns = await env.DB.prepare('SELECT 1 FROM markering WHERE id = ?1').bind(ok.id).first();
    return finns ? svar(204, 'sparad') : svar(429, 'full');
}

export default {
    async fetch(request, env) {
        const url = new URL(request.url);
        if (url.pathname === '/api/markering') {
            try {
                return await taEmot(request, env, url);
            } catch (e) {
                return svar(503, 'stangd');
            }
        }
        if (url.pathname.startsWith('/api/')) return svar(404, 'ogiltig');
        return env.ASSETS.fetch(request);
    }
};
