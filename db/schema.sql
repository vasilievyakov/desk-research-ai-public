-- Desk Research: five tables.
-- sources     -> where we collect from
-- materials   -> what the collector brought (one row per link)
-- findings    -> what the worker extracted with the model
-- runs        -> every run of every block, with status
-- subscribers -> who pressed Start in the Telegram bot

CREATE TABLE IF NOT EXISTS sources (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    kind        TEXT NOT NULL,            -- hn | arxiv | rss
    url         TEXT NOT NULL,
    active      BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS runs (
    id           SERIAL PRIMARY KEY,
    service      TEXT NOT NULL,           -- collector | worker | bot
    status       TEXT NOT NULL,           -- started | running | finished | failed
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at  TIMESTAMPTZ,
    items        INTEGER NOT NULL DEFAULT 0,
    note         TEXT
);

CREATE TABLE IF NOT EXISTS materials (
    id            SERIAL PRIMARY KEY,
    source_id     INTEGER NOT NULL REFERENCES sources(id),
    run_id        INTEGER REFERENCES runs(id),
    url           TEXT NOT NULL UNIQUE,
    title         TEXT NOT NULL,
    text          TEXT,
    published_at  TIMESTAMPTZ,
    collected_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    status        TEXT NOT NULL DEFAULT 'new'   -- new | done | skipped | failed
);

CREATE TABLE IF NOT EXISTS findings (
    id              SERIAL PRIMARY KEY,
    material_id     INTEGER NOT NULL UNIQUE REFERENCES materials(id),
    entity          TEXT,                 -- company the material is about
    summary         TEXT NOT NULL,
    model           TEXT NOT NULL,
    prompt_version  TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- the bot marks a finding when it has been sent to subscribers
ALTER TABLE findings ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ;

-- tone of the news, written by the worker since prompt v2: хорошая | плохая | нейтральная
ALTER TABLE findings ADD COLUMN IF NOT EXISTS sentiment TEXT;

CREATE TABLE IF NOT EXISTS subscribers (
    chat_id     BIGINT PRIMARY KEY,
    name        TEXT,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO sources (name, kind, url) VALUES
    ('Hacker News', 'hn',    'https://hn.algolia.com/api/v1/search_by_date?query=AI&tags=story&hitsPerPage=15'),
    ('Hacker News: Anthropic', 'hn', 'https://hn.algolia.com/api/v1/search_by_date?query=Anthropic&tags=story&hitsPerPage=15'),
    ('Hacker News: OpenAI',    'hn', 'https://hn.algolia.com/api/v1/search_by_date?query=OpenAI&tags=story&hitsPerPage=15'),
    ('arXiv cs.AI', 'arxiv', 'https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=10'),
    ('Хабр: ИИ',    'rss',   'https://habr.com/ru/rss/hubs/artificial_intelligence/articles/')
ON CONFLICT (name) DO NOTHING;
