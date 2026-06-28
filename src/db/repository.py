import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from src.config import DB_PATH


def _dict_factory(cursor, row):
    cols = [col[0] for col in cursor.description]
    return dict(zip(cols, row))


class Repository:
    def __init__(self, db_path: Path = DB_PATH):
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = _dict_factory
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def init_db(self):
        conn = self.connect()
        schema_path = Path(__file__).resolve().parent / "schema.sql"
        conn.executescript(schema_path.read_text())
        conn.commit()

    def insert_log(self, text: str, duration_ms: int = 0, tags: list[str] | None = None) -> int:
        conn = self.connect()
        cur = conn.execute(
            "INSERT INTO logs (text, duration_ms, tags) VALUES (?, ?, ?)",
            (text.strip(), duration_ms, json.dumps(tags or [])),
        )
        conn.commit()
        return cur.lastrowid

    def get_log(self, log_id: int) -> dict | None:
        conn = self.connect()
        row = conn.execute("SELECT * FROM logs WHERE id = ?", (log_id,)).fetchone()
        return row

    def get_logs(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        tag_filter: str | None = None,
        search: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict]:
        conn = self.connect()
        conditions = []
        params = []

        if date_from:
            conditions.append("DATE(timestamp) >= ?")
            params.append(date_from.isoformat())
        if date_to:
            conditions.append("DATE(timestamp) <= ?")
            params.append(date_to.isoformat())
        if tag_filter:
            conditions.append("tags LIKE ?")
            params.append(f"%\"{tag_filter}\"%")
        if search:
            conditions.append("text LIKE ?")
            params.append(f"%{search}%")

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        query = f"SELECT * FROM logs {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(query, params).fetchall()
        return rows

    def update_log(self, log_id: int, text: str | None = None, tags: list[str] | None = None) -> bool:
        conn = self.connect()
        fields = []
        params = []

        if text is not None:
            fields.append("text = ?")
            params.append(text.strip())
        if tags is not None:
            fields.append("tags = ?")
            params.append(json.dumps(tags))

        if not fields:
            return False

        params.append(log_id)
        cur = conn.execute(
            f"UPDATE logs SET {', '.join(fields)} WHERE id = ?", params
        )
        conn.commit()
        return cur.rowcount > 0

    def delete_log(self, log_id: int) -> bool:
        conn = self.connect()
        cur = conn.execute("DELETE FROM logs WHERE id = ?", (log_id,))
        conn.commit()
        return cur.rowcount > 0

    def get_all_tags(self) -> list[str]:
        conn = self.connect()
        rows = conn.execute("SELECT tags FROM logs").fetchall()
        all_tags: set[str] = set()
        for row in rows:
            try:
                all_tags.update(json.loads(row["tags"]))
            except (json.JSONDecodeError, TypeError):
                pass
        return sorted(all_tags)

    def get_logs_grouped_by_date(self, month: int | None = None, year: int | None = None) -> dict[str, list[dict]]:
        conn = self.connect()
        today = date.today()
        month = month or today.month
        year = year or today.year

        rows = conn.execute(
            """SELECT * FROM logs
               WHERE strftime('%m', timestamp) = ? AND strftime('%Y', timestamp) = ?
               ORDER BY timestamp DESC""",
            (f"{month:02d}", str(year)),
        ).fetchall()

        groups: dict[str, list[dict]] = {}
        for row in rows:
            ts = row["timestamp"]
            day_key = ts[:10] if ts else "unknown"
            groups.setdefault(day_key, []).append(row)

        return groups

    def get_logs_for_date(self, target_date: date) -> list[dict]:
        conn = self.connect()
        rows = conn.execute(
            """SELECT * FROM logs
               WHERE DATE(timestamp) = ?
               ORDER BY timestamp DESC""",
            (target_date.isoformat(),),
        ).fetchall()
        return rows
