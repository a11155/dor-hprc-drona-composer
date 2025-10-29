#!/usr/bin/env python3
# drona_history_lib.py
#
# SQLite-backed history for Drona workflows - SIMPLIFIED VERSION
# - Core columns: drona_id, name, environment, location, runtime_meta, start_time, status
# - env_params: JSON TEXT column holding entire job information
# - CLI is READ-ONLY by default (enable admin writes with DRONA_HISTORY_ALLOW_WRITE=1).
# - CLI prints SQL columns by default; add -j/--with-json to include env_params.
# - No-args: compact usage line. -h/--help: full help.
# Python 3.6+ compatible.

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

ALLOW_WRITE = os.environ.get("DRONA_HISTORY_ALLOW_WRITE") == "1"

# Columns to display via CLI (exclude env_params by default)
_DISPLAY_COLUMNS = [
    "drona_id", "name", "environment", "location", "runtime_meta", "start_time", "status"
]

def _default_db_path(explicit_path: Optional[Union[str, Path]] = None) -> Path:
    if explicit_path:
        return Path(os.path.expanduser(os.path.expandvars(str(explicit_path)))).resolve()
    env_db = os.environ.get("DRONA_HISTORY_DB")
    if env_db:
        return Path(os.path.expanduser(os.path.expandvars(env_db))).resolve()
    base = os.environ.get("SCRATCH")
    base_path = Path(os.path.expanduser(os.path.expandvars(base))) if base else Path.home()
    return (base_path / "drona_composer" / "jobs" / "job_history.db").resolve()

_BASE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS job_history (
    drona_id     TEXT PRIMARY KEY,
    name         TEXT,
    environment  TEXT NOT NULL,
    location     TEXT,
    runtime_meta TEXT NOT NULL DEFAULT '',
    start_time   TEXT,   -- ISO8601
    status       TEXT,   -- e.g. Submitted, Running, Completed, Failed
    env_params   TEXT NOT NULL  -- JSON object (holds entire job information)
);

CREATE INDEX IF NOT EXISTS idx_job_history_environment ON job_history(environment);
CREATE INDEX IF NOT EXISTS idx_job_history_start_time ON job_history(start_time);
"""

_EXPECTED_COLUMNS = {
    "drona_id", "name", "environment", "location", "runtime_meta", "start_time", "status", "env_params"
}

def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_BASE_SCHEMA_SQL)
    cur = conn.execute("PRAGMA table_info(job_history)")
    have = {row[1] for row in cur.fetchall()}
    for col in _EXPECTED_COLUMNS - have:
        default_val = "NOT NULL DEFAULT ''" if col == "runtime_meta" else ""
        conn.execute("ALTER TABLE job_history ADD COLUMN {} TEXT {}".format(col, default_val))
    conn.commit()

def _connect(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    path = _default_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    _ensure_schema(conn)
    return conn

def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    d = dict(row)
    # Parse env_params JSON back to object for library/API callers
    if d.get("env_params") is not None:
        try:
            d["env_params"] = json.loads(d["env_params"])
        except Exception:
            pass
    return d

# -----------------------------
# Library API (returns dict/list)
# -----------------------------

def get_record(drona_id: str, db_path: Optional[Union[str, Path]] = None) -> Optional[Dict[str, Any]]:
    """Get a single record by drona_id."""
    conn = _connect(db_path)
    try:
        cur = conn.execute("SELECT * FROM job_history WHERE drona_id = ?", (drona_id,))
        return _row_to_dict(cur.fetchone())
    finally:
        conn.close()

def list_records_by_env(
    environment: str,
    db_path: Optional[Union[str, Path]] = None,
    limit: Optional[int] = None,
    start_time_after: Optional[str] = None,
    start_time_before: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List records filtered by environment."""
    conn = _connect(db_path)
    try:
        clauses = ["environment = ?"]
        params: List[Any] = [environment]
        if start_time_after:
            clauses.append("(start_time IS NULL OR start_time >= ?)")
            params.append(start_time_after)
        if start_time_before:
            clauses.append("(start_time IS NULL OR start_time < ?)")
            params.append(start_time_before)
        where = " AND ".join(clauses)
        order = "ORDER BY COALESCE(start_time, '') DESC, drona_id DESC"
        limit_sql = " LIMIT {}".format(int(limit)) if (isinstance(limit, int) and limit > 0) else ""
        sql = "SELECT * FROM job_history WHERE {} {}{}".format(where, order, limit_sql)
        cur = conn.execute(sql, tuple(params))
        return [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def update_status(
    drona_id: str,
    status: str,
    db_path: Optional[Union[str, Path]] = None,
) -> Optional[Dict[str, Any]]:
    """Update the status of a record."""
    conn = _connect(db_path)
    try:
        cur = conn.execute("SELECT 1 FROM job_history WHERE drona_id = ?", (drona_id,))
        if not cur.fetchone():
            return None
        conn.execute("UPDATE job_history SET status = ? WHERE drona_id = ?", (status, drona_id))
        conn.commit()
        return get_record(drona_id, db_path=db_path)
    finally:
        conn.close()

def update_runtime_meta(
    drona_id: str,
    runtime_meta: str,
    db_path: Optional[Union[str, Path]] = None,
) -> Optional[Dict[str, Any]]:
    """Update the runtime_meta of a record."""
    conn = _connect(db_path)
    try:
        cur = conn.execute("SELECT 1 FROM job_history WHERE drona_id = ?", (drona_id,))
        if not cur.fetchone():
            return None
        conn.execute("UPDATE job_history SET runtime_meta = ? WHERE drona_id = ?", (runtime_meta, drona_id))
        conn.commit()
        return get_record(drona_id, db_path=db_path)
    finally:
        conn.close()

def update_start_time(
    drona_id: str,
    start_time: str,
    db_path: Optional[Union[str, Path]] = None,
) -> Optional[Dict[str, Any]]:
    """Update the start_time of a record."""
    conn = _connect(db_path)
    try:
        cur = conn.execute("SELECT 1 FROM job_history WHERE drona_id = ?", (drona_id,))
        if not cur.fetchone():
            return None
        conn.execute("UPDATE job_history SET start_time = ? WHERE drona_id = ?", (start_time, drona_id))
        conn.commit()
        return get_record(drona_id, db_path=db_path)
    finally:
        conn.close()

def update_record(
    drona_id: str,
    db_path: Optional[Union[str, Path]] = None,
    status: Optional[str] = None,
    runtime_meta: Optional[str] = None,
    start_time: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update one or more fields of a record."""
    conn = _connect(db_path)
    try:
        cur = conn.execute("SELECT 1 FROM job_history WHERE drona_id = ?", (drona_id,))
        if not cur.fetchone():
            return None
        
        updates = []
        params = []
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if runtime_meta is not None:
            updates.append("runtime_meta = ?")
            params.append(runtime_meta)
        if start_time is not None:
            updates.append("start_time = ?")
            params.append(start_time)
        
        if not updates:
            return get_record(drona_id, db_path=db_path)
        
        sql = "UPDATE job_history SET {} WHERE drona_id = ?".format(", ".join(updates))
        params.append(drona_id)
        
        conn.execute(sql, tuple(params))
        conn.commit()
        return get_record(drona_id, db_path=db_path)
    finally:
        conn.close()

def add_kv(
    drona_id: str,
    key: str,
    value: Any,
    db_path: Optional[Union[str, Path]] = None,
) -> Optional[Dict[str, Any]]:
    """Add or update a key-value pair in env_params."""
    conn = _connect(db_path)
    try:
        cur = conn.execute("SELECT env_params FROM job_history WHERE drona_id = ?", (drona_id,))
        row = cur.fetchone()
        if not row:
            return None
        try:
            env_params = json.loads(row["env_params"]) if row["env_params"] else {}
        except Exception:
            env_params = {}
        if key in env_params:
            existing = env_params[key]
            if isinstance(existing, list):
                env_params[key] = existing + [value]
            else:
                env_params[key] = [existing, value]
        else:
            env_params[key] = value
        env_params_str = json.dumps(env_params, separators=(",", ":"))
        conn.execute("UPDATE job_history SET env_params = ? WHERE drona_id = ?", (env_params_str, drona_id))
        conn.commit()
        return get_record(drona_id, db_path=db_path)
    finally:
        conn.close()

# -----------------------------
# CLI behavior
# -----------------------------

def _print_compact_usage(prog: str) -> None:
    line = ("Usage (compact): {prog} [-h] [--db PATH] "
            "[-j|--with-json] "
            "(-i ID | -e ENV [--after ISO] [--before ISO] [--limit N])").format(prog=prog)
    if ALLOW_WRITE:
        line += ("\nAdmin (DRONA_HISTORY_ALLOW_WRITE=1): "
                 "{p} --edit -i ID [--status STATUS] [--runtime-meta META] [--start-time ISO]  |  {p} -i ID -a KEY -v VAL").format(p=prog)
    sys.stderr.write(line + "\n")

def _print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))

def _sql_only(record: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if record is None:
        return None
    return {k: record.get(k) for k in _DISPLAY_COLUMNS}

def _present(record: Optional[Dict[str, Any]], include_json: bool) -> Optional[Dict[str, Any]]:
    if record is None:
        return None
    out = _sql_only(record)
    if include_json:
        out["env_params"] = record.get("env_params")
    return out

def _present_list(records: List[Dict[str, Any]], include_json: bool) -> List[Dict[str, Any]]:
    return [_present(r, include_json) for r in records]

def _load_json_arg(s: Optional[str], file_path: Optional[str]) -> Optional[Dict[str, Any]]:
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    if s:
        return json.loads(s)
    return None

def main():
    prog = Path(sys.argv[0]).name
    if len(sys.argv) == 1:
        _print_compact_usage(prog)
        sys.exit(2)

    parser = argparse.ArgumentParser(
        prog=prog,
        description="Read job history from the Drona SQLite database (read-only by default)."
    )
    parser.add_argument("--db", help="Path to the SQLite file (overrides env defaults).")

    # Output control
    parser.add_argument("-j", "--with-json", action="store_true",
                        help="Include env_params JSON in output.")

    # Core read-only operations
    parser.add_argument("-i", "--id", dest="drona_id", help="Get a record by drona_id.")
    parser.add_argument("-e", "--env", dest="environment", help="List records by environment name.")
    parser.add_argument("--after", dest="start_after", help="Filter list by start_time >= ISO8601.")
    parser.add_argument("--before", dest="start_before", help="Filter list by start_time < ISO8601.")
    parser.add_argument("--limit", type=int, help="Max results for list.")

    # Admin/write operations (hidden unless env flag set)
    if ALLOW_WRITE:
        parser.add_argument("--edit", action="store_true",
                            help="(admin) Edit an existing record (requires -i).")
        parser.add_argument("--status", dest="status", help="(admin) Update status for --edit.")
        parser.add_argument("--runtime-meta", dest="runtime_meta", help="(admin) Update runtime_meta for --edit.")
        parser.add_argument("--start-time", dest="start_time", help="(admin) Update start_time (ISO8601) for --edit.")
        parser.add_argument("-a", "--add", dest="add_key",
                            help="(admin) Add a key to env_params for -i record (use with -v).")
        parser.add_argument("-v", "--value", dest="add_value",
                            help="(admin) Value for --add (parsed as JSON if possible; else string).")

    args = parser.parse_args()
    dbp = args.db

    include_json = args.with_json

    # Guard writes if CLI is not in admin mode
    if not ALLOW_WRITE and (getattr(args, "edit", False) or getattr(args, "add_key", None)):
        parser.error("write operations are disabled; set DRONA_HISTORY_ALLOW_WRITE=1 to enable admin mode")

    # EDIT (admin)
    if ALLOW_WRITE and getattr(args, "edit", False):
        if not args.drona_id:
            parser.error("--edit requires -i/--id")
        rec = update_record(
            drona_id=args.drona_id,
            db_path=dbp,
            status=getattr(args, "status", None),
            runtime_meta=getattr(args, "runtime_meta", None),
            start_time=getattr(args, "start_time", None),
        )
        _print_json(_present(rec, include_json) if rec is not None else {"error": "not found"}); return

    # ADD key/value (admin)
    if ALLOW_WRITE and getattr(args, "add_key", None):
        if not args.drona_id:
            parser.error("--add requires -i/--id of the record")
        val_raw = args.add_value
        if val_raw is None:
            parser.error("--add also needs -v/--value")
        try:
            val = json.loads(val_raw)
        except Exception:
            val = val_raw
        rec = add_kv(args.drona_id, args.add_key, val, db_path=dbp)
        _print_json(_present(rec, include_json) if rec is not None else {"error": "not found"}); return

    # GET by id (read-only)
    if args.drona_id and not args.environment:
        rec = get_record(args.drona_id, db_path=dbp)
        _print_json(_present(rec, include_json) if rec is not None else {"error": "not found"}); return

    # LIST by env (read-only)
    if args.environment and not args.drona_id:
        lst = list_records_by_env(
            args.environment, db_path=dbp, limit=args.limit,
            start_time_after=args.start_after, start_time_before=args.start_before
        )
        _print_json(_present_list(lst, include_json)); return

    _print_compact_usage(prog)
    sys.exit(2)

if __name__ == "__main__":
    main()
