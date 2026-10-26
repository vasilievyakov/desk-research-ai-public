"""Shared helpers: connection to the database and run log."""

import os
import sys
from pathlib import Path

import psycopg

SCHEMA = Path(__file__).with_name("schema.sql")


def connect():
    return psycopg.connect(os.environ["DATABASE_URL"], autocommit=True)


SCHEMA_LOCK = 4207  # any fixed number shared by all blocks


def init_schema(conn):
    # blocks start at the same time on a fresh database; the lock lets one create the tables
    conn.execute("SELECT pg_advisory_lock(%s)", (SCHEMA_LOCK,))
    try:
        conn.execute(SCHEMA.read_text())
    finally:
        conn.execute("SELECT pg_advisory_unlock(%s)", (SCHEMA_LOCK,))


def log(service, message):
    print(f"[{service}] {message}", file=sys.stdout, flush=True)


def start_run(conn, service):
    run_id = conn.execute(
        "INSERT INTO runs (service, status) VALUES (%s, 'started') RETURNING id",
        (service,),
    ).fetchone()[0]
    log(service, f"прогон {run_id} начат")
    return run_id


def progress_run(conn, service, run_id, items, note):
    conn.execute(
        "UPDATE runs SET status = 'running', items = %s, note = %s WHERE id = %s",
        (items, note, run_id),
    )
    log(service, f"прогон {run_id} идет: {note}")


def finish_run(conn, service, run_id, items, note):
    conn.execute(
        "UPDATE runs SET status = 'finished', items = %s, note = %s, finished_at = now() WHERE id = %s",
        (items, note, run_id),
    )
    log(service, f"прогон {run_id} завершен: {note}")


def fail_run(conn, service, run_id, error):
    conn.execute(
        "UPDATE runs SET status = 'failed', note = %s, finished_at = now() WHERE id = %s",
        (str(error)[:500], run_id),
    )
    log(service, f"прогон {run_id} упал: {error}")
