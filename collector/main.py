"""Collector: visits every active source once, saves new materials, exits."""

import json
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import db

SERVICE = "collector"
MAX_PER_SOURCE = 15
ATOM = "{http://www.w3.org/2005/Atom}"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "desk-research/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def read_hn(url):
    for hit in json.loads(fetch(url))["hits"]:
        link = (
            hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        )
        yield {
            "url": link,
            "title": hit["title"],
            "text": hit.get("story_text") or "",
            "published_at": hit["created_at"],
        }


def read_arxiv(url):
    root = ET.fromstring(fetch(url))
    for entry in root.iter(f"{ATOM}entry"):
        yield {
            "url": entry.findtext(f"{ATOM}id"),
            "title": " ".join(entry.findtext(f"{ATOM}title").split()),
            "text": " ".join(entry.findtext(f"{ATOM}summary").split())[:1500],
            "published_at": entry.findtext(f"{ATOM}published"),
        }


def read_rss(url):
    root = ET.fromstring(fetch(url))
    for item in root.iter("item"):
        pub = item.findtext("pubDate")
        yield {
            "url": item.findtext("link").strip(),
            "title": item.findtext("title").strip(),
            "text": (item.findtext("description") or "")[:1500],
            "published_at": parsedate_to_datetime(pub).isoformat() if pub else None,
        }


READERS = {"hn": read_hn, "arxiv": read_arxiv, "rss": read_rss}


def main():
    conn = db.connect()
    db.init_schema(conn)
    run_id = db.start_run(conn, SERVICE)
    total_new = 0
    try:
        sources = conn.execute(
            "SELECT id, name, kind, url FROM sources WHERE active"
        ).fetchall()
        for source_id, name, kind, url in sources:
            try:
                items = list(READERS[kind](url))[:MAX_PER_SOURCE]
            except Exception as error:
                # one broken source does not stop the run
                db.log(SERVICE, f"источник «{name}» недоступен: {error}")
                continue
            new = 0
            for item in items:
                row = conn.execute(
                    """INSERT INTO materials (source_id, run_id, url, title, text, published_at)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (url) DO NOTHING RETURNING id""",
                    (
                        source_id,
                        run_id,
                        item["url"],
                        item["title"],
                        item["text"],
                        item["published_at"],
                    ),
                ).fetchone()
                new += row is not None
            total_new += new
            db.progress_run(
                conn,
                SERVICE,
                run_id,
                total_new,
                f"{name}: взял {len(items)}, новых {new}",
            )
        db.finish_run(
            conn, SERVICE, run_id, total_new, f"новых материалов в базе: {total_new}"
        )
    except Exception as error:
        db.fail_run(conn, SERVICE, run_id, error)
        raise


if __name__ == "__main__":
    main()
