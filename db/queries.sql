-- Example queries for Postgres.

-- 1. All findings from Hacker News for the last week (two links: finding -> material -> source)
SELECT m.published_at, f.entity, f.summary, m.url
FROM findings f
JOIN materials m ON m.id = f.material_id
JOIN sources s ON s.id = m.source_id
WHERE s.name = 'Hacker News' AND m.published_at > now() - interval '7 days'
ORDER BY m.published_at DESC;

-- 2. Runs of every block, newest first
SELECT id, service, status, items, note, started_at, finished_at
FROM runs ORDER BY id DESC LIMIT 20;
