-- Pensla: de hemliga markeringarna (worker/mottagare.js skriver,
-- verktyg/markeringar.py --server läser). Körs en gång när databasen skapas:
--   npx wrangler@4 d1 execute pensla-markeringar --remote --file worker/schema.sql
-- drag = JSON, [[x0, y0, x1, y1, ...] ...]: frihandsdrag med punkter normerade 0–1
-- relativt bilden (tom lista = hela bilden). bredd = penselns bredd (andel av bildens höjd).
-- mottagen = serverns klocka (ms sedan 1970), tid = appens klocka (UTC).
-- miljo = 'skarp' eller 'test'. hanterad sätts till 1 när markeringen är åtgärdad.
CREATE TABLE IF NOT EXISTS markering (
    id        TEXT PRIMARY KEY,
    mottagen  INTEGER NOT NULL,
    miljo     TEXT NOT NULL,
    nr        INTEGER NOT NULL,
    namn      TEXT NOT NULL,
    drag      TEXT NOT NULL,
    bredd     REAL NOT NULL,
    tid       TEXT NOT NULL,
    version   TEXT NOT NULL,
    plattform TEXT NOT NULL,
    hanterad  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS markering_mottagen ON markering (mottagen);
