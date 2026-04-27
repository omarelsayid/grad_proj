"""Shared psycopg2 connection pool for SkillSync dashboards."""
import os
import psycopg2
import psycopg2.pool
import psycopg2.extras
import pandas as pd
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

_pool: psycopg2.pool.SimpleConnectionPool | None = None


def _get_pool() -> psycopg2.pool.SimpleConnectionPool:
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "skillsync_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        )
    return _pool


def query_df(sql: str, params=None) -> pd.DataFrame:
    pool = _get_pool()
    conn = pool.getconn()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        pool.putconn(conn)


def query_scalar(sql: str, params=None):
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        pool.putconn(conn)


def query_one(sql: str, params=None) -> dict | None:
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        pool.putconn(conn)
