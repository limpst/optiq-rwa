"""SQLite store for live Deribit snapshots and the paper (dry-run) book.

One file (default data/optiq.db). Tables:
  snapshots       one row per collection run
  instruments     static instrument metadata (first/last seen)
  book_summary    per snapshot x instrument: bid/ask/mark/iv/volume/OI (all listed options)
  order_book      per snapshot x instrument x level: top-of-book depth (focus + universe bases)
  inst_state      per snapshot x instrument: greeks, bid/ask iv, index & underlying price
  index_price     per snapshot x index
  delivery_price  settlement price per index x date (expiry 08:00 UTC)
  volume_daily    per date x base: 24h option volume (USD) and the universe flag
  paper_orders / paper_positions / paper_nav   dry-run book (see paper.engine)

Parquet export: one file per table per UTC date in data/parquet/.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sqlite3

import pandas as pd

from ..config import SETTINGS

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (snap_id INTEGER PRIMARY KEY AUTOINCREMENT, ts_ms INTEGER NOT NULL,
    date TEXT NOT NULL, n_summary INTEGER, n_depth INTEGER, seconds REAL, note TEXT);
CREATE TABLE IF NOT EXISTS instruments (instrument_name TEXT PRIMARY KEY, base TEXT, currency TEXT,
    settlement_currency TEXT, option_type TEXT, strike REAL, expiration_ts INTEGER, contract_size REAL,
    inverse INTEGER, tick_size REAL, min_trade_amount REAL, first_seen_ms INTEGER, last_seen_ms INTEGER);
CREATE TABLE IF NOT EXISTS book_summary (snap_id INTEGER, instrument_name TEXT, bid REAL, ask REAL,
    mid REAL, mark_price REAL, mark_iv REAL, volume REAL, volume_usd REAL, open_interest REAL,
    underlying_price REAL, PRIMARY KEY (snap_id, instrument_name));
CREATE TABLE IF NOT EXISTS order_book (snap_id INTEGER, instrument_name TEXT, level INTEGER,
    bid_px REAL, bid_amt REAL, ask_px REAL, ask_amt REAL, PRIMARY KEY (snap_id, instrument_name, level));
CREATE TABLE IF NOT EXISTS inst_state (snap_id INTEGER, instrument_name TEXT, mark_price REAL, mark_iv REAL,
    bid_iv REAL, ask_iv REAL, delta REAL, gamma REAL, vega REAL, theta REAL, index_price REAL,
    underlying_price REAL, open_interest REAL, interest_rate REAL, PRIMARY KEY (snap_id, instrument_name));
CREATE TABLE IF NOT EXISTS index_price (snap_id INTEGER, index_name TEXT, price REAL, PRIMARY KEY (snap_id, index_name));
CREATE TABLE IF NOT EXISTS delivery_price (index_name TEXT, date TEXT, price REAL, PRIMARY KEY (index_name, date));
CREATE TABLE IF NOT EXISTS volume_daily (date TEXT, base TEXT, volume_usd REAL, n_traded INTEGER,
    n_listed INTEGER, universe_pass INTEGER, PRIMARY KEY (date, base));
CREATE TABLE IF NOT EXISTS paper_orders (order_id INTEGER PRIMARY KEY AUTOINCREMENT, ts_ms INTEGER, date TEXT,
    strategy TEXT, instrument_name TEXT, side TEXT, qty REAL, limit_px REAL, status TEXT, fill_px REAL,
    fill_usd REAL, fill_ts_ms INTEGER, spot REAL, snap_id INTEGER, note TEXT, fill_mid REAL,
    fee_usd REAL, slippage_usd REAL, levels_used INTEGER);
CREATE TABLE IF NOT EXISTS paper_positions (pos_id INTEGER PRIMARY KEY AUTOINCREMENT, strategy TEXT,
    instrument_name TEXT, side TEXT, qty REAL, entry_px REAL, entry_usd REAL, entry_ts_ms INTEGER,
    expiry_ts INTEGER, spot_entry REAL, settled INTEGER DEFAULT 0, settle_px REAL, payoff_usd REAL, pnl_usd REAL, settle_fee_usd REAL);
CREATE TABLE IF NOT EXISTS paper_nav (date TEXT, strategy TEXT, nav REAL, cash REAL, rwa_accrual REAL,
    option_pnl REAL, premium_paid REAL, premium_received REAL, n_open INTEGER, fees_usd REAL, PRIMARY KEY (date, strategy));
CREATE INDEX IF NOT EXISTS ix_bs_inst ON book_summary (instrument_name, snap_id);
CREATE INDEX IF NOT EXISTS ix_ob_inst ON order_book (instrument_name, snap_id);
CREATE INDEX IF NOT EXISTS ix_snap_date ON snapshots (date);
"""

DATE_TABLES = ("snapshots", "book_summary", "order_book", "inst_state", "index_price")


def connect(path: pathlib.Path | str | None = None) -> sqlite3.Connection:
    p = pathlib.Path(path or SETTINGS.db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA busy_timeout=60000")
    con.executescript(SCHEMA)
    _migrate(con)
    return con


def _migrate(con: sqlite3.Connection) -> None:
    ocols = {r[1] for r in con.execute("PRAGMA table_info(paper_orders)")}
    if "fill_mid" not in ocols:
        con.execute("ALTER TABLE paper_orders ADD COLUMN fill_mid REAL")     # mid at the moment a resting order fills (adverse selection)
    cols = {r[1] for r in con.execute("PRAGMA table_info(instruments)")}
    if "min_trade_amount" not in cols:
        con.execute("ALTER TABLE instruments ADD COLUMN min_trade_amount REAL")
    for table, col, typ in (("paper_orders", "fee_usd", "REAL"), ("paper_orders", "slippage_usd", "REAL"),
                            ("paper_orders", "levels_used", "INTEGER"), ("paper_positions", "settle_fee_usd", "REAL"),
                            ("paper_nav", "fees_usd", "REAL")):
        have = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
        if col not in have:
            con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")


def utc_date(ts_ms: int) -> str:
    return dt.datetime.fromtimestamp(ts_ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def insert_df(con: sqlite3.Connection, table: str, df: pd.DataFrame, replace: bool = True) -> int:
    if df.empty:
        return 0
    cols = list(df.columns)
    verb = "INSERT OR REPLACE" if replace else "INSERT OR IGNORE"
    sql = f"{verb} INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})"
    rows = [tuple(None if pd.isna(v) else (v.item() if hasattr(v, "item") else v) for v in r)
            for r in df.itertuples(index=False, name=None)]
    con.executemany(sql, rows)
    return len(rows)


def read(con: sqlite3.Connection, sql: str, params=()) -> pd.DataFrame:
    return pd.read_sql_query(sql, con, params=params)


def latest_snap_id(con: sqlite3.Connection) -> int | None:
    r = con.execute("SELECT MAX(snap_id) FROM snapshots").fetchone()
    return r[0]


def export_parquet(con: sqlite3.Connection, date: str | None = None, out_dir: pathlib.Path | None = None) -> list[str]:
    """Write <table>_<date>.parquet for every date-partitioned table (default: yesterday+today UTC)."""
    out = pathlib.Path(out_dir or SETTINGS.parquet_dir)
    out.mkdir(parents=True, exist_ok=True)
    dates = [date] if date else sorted(set(read(con, "SELECT DISTINCT date FROM snapshots ORDER BY date DESC LIMIT 2").date))
    written = []
    for d in dates:
        snaps = read(con, "SELECT snap_id FROM snapshots WHERE date=?", (d,)).snap_id.tolist()
        if not snaps:
            continue
        ph = ",".join("?" * len(snaps))
        for t in DATE_TABLES:
            df = read(con, f"SELECT * FROM {t} WHERE snap_id IN ({ph})", snaps)
            if df.empty:
                continue
            f = out / f"{t}_{d}.parquet"
            df.to_parquet(f, index=False, compression="zstd")
            written.append(str(f))
    for t in ("instruments", "delivery_price", "volume_daily", "paper_orders", "paper_positions", "paper_nav"):
        df = read(con, f"SELECT * FROM {t}")
        if not df.empty:
            f = out / f"{t}.parquet"
            df.to_parquet(f, index=False, compression="zstd")
            written.append(str(f))
    return written


def prune_summary(con: sqlite3.Connection, max_days: float = 8.0, vacuum: bool = True) -> int:
    """Delete book_summary rows whose expiry was more than `max_days` after the snapshot time (storage policy 2026-11-23)."""
    n = con.execute("""DELETE FROM book_summary WHERE rowid IN (
                         SELECT b.rowid FROM book_summary b JOIN instruments i USING (instrument_name) JOIN snapshots s USING (snap_id)
                         WHERE i.expiration_ts - s.ts_ms > ? )""", (max_days * 86_400_000,)).rowcount
    con.commit()
    if vacuum:
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        con.execute("VACUUM")
    return n


def table_counts(con: sqlite3.Connection) -> dict:
    names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    return {n: con.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0] for n in sorted(names)}
