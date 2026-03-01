"""Persistent SQLite store for diff/review artifacts."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 3


class IndexStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.db_path = root / ".docgenie" / "index.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        row = self._conn.execute(
            "SELECT value FROM schema_meta WHERE key='schema_version'"
        ).fetchone()
        current = int(row["value"]) if row else 0
        if current >= SCHEMA_VERSION:
            return

        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at REAL NOT NULL,
                finished_at REAL,
                mode TEXT,
                metrics_json TEXT
            );

            CREATE TABLE IF NOT EXISTS diff_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                from_ref TEXT,
                to_ref TEXT,
                summary_json TEXT,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            );

            CREATE TABLE IF NOT EXISTS file_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                path TEXT NOT NULL,
                folder TEXT,
                risk_level TEXT,
                risk_score REAL,
                review_json TEXT,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            );

            CREATE TABLE IF NOT EXISTS output_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                source_file TEXT NOT NULL,
                source_line INTEGER,
                target_file TEXT,
                operation TEXT,
                confidence TEXT,
                resolved INTEGER NOT NULL DEFAULT 0,
                evidence_snippet TEXT,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            );

            CREATE TABLE IF NOT EXISTS doc_artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                artifact_path TEXT NOT NULL,
                target TEXT,
                content_hash TEXT,
                section_hashes_json TEXT,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            );
            """
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) VALUES('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def commit(self) -> None:
        self._conn.commit()

    def start_run(self, *, mode: str = "generate") -> int:
        cur = self._conn.execute(
            "INSERT INTO runs(started_at,mode) VALUES(?,?)",
            (time.time(), mode),
        )
        row_id = cur.lastrowid
        if row_id is None:
            raise RuntimeError("INSERT into runs returned no lastrowid")
        return row_id

    def finish_run(self, run_id: int, metrics: dict[str, Any] | None = None) -> None:
        self._conn.execute(
            "UPDATE runs SET finished_at=?, metrics_json=? WHERE id=?",
            (time.time(), json.dumps(metrics or {}, sort_keys=True), run_id),
        )

    def add_diff_run(
        self, run_id: int, from_ref: str | None, to_ref: str | None, summary: dict[str, Any]
    ) -> None:
        self._conn.execute(
            "INSERT INTO diff_runs(run_id,from_ref,to_ref,summary_json) VALUES(?,?,?,?)",
            (run_id, from_ref, to_ref, json.dumps(summary, sort_keys=True)),
        )

    def replace_file_reviews(self, run_id: int, reviews: list[dict[str, Any]]) -> None:
        self._conn.execute("DELETE FROM file_reviews WHERE run_id=?", (run_id,))
        stmt = (
            "INSERT INTO file_reviews(run_id,path,folder,risk_level,risk_score,review_json) "
            "VALUES(?,?,?,?,?,?)"
        )
        for review in reviews:
            self._conn.execute(
                stmt,
                (
                    run_id,
                    review.get("path", ""),
                    review.get("folder", "."),
                    review.get("risk_level", "low"),
                    float(review.get("risk_score", 0.0)),
                    json.dumps(review, sort_keys=True),
                ),
            )

    def replace_output_links(self, run_id: int, links: list[dict[str, Any]]) -> None:
        self._conn.execute("DELETE FROM output_links WHERE run_id=?", (run_id,))
        for link in links:
            self._conn.execute(
                """
                INSERT INTO output_links(
                    run_id,source_file,source_line,target_file,operation,confidence,resolved,evidence_snippet
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    run_id,
                    link.get("source_file", ""),
                    int(link.get("source_line", 0)),
                    link.get("target_file"),
                    link.get("operation", ""),
                    link.get("confidence", "low"),
                    1 if link.get("resolved") else 0,
                    link.get("evidence_snippet", ""),
                ),
            )

    def latest_run_id(self) -> int | None:
        row = self._conn.execute("SELECT id FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        return int(row["id"]) if row else None

    def add_doc_artifact(
        self,
        run_id: int,
        artifact_path: str,
        target: str,
        content_hash: str,
        section_hashes: dict[str, str],
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO doc_artifacts(run_id,artifact_path,target,content_hash,section_hashes_json)
            VALUES(?,?,?,?,?)
            """,
            (
                run_id,
                artifact_path,
                target,
                content_hash,
                json.dumps(section_hashes, sort_keys=True),
            ),
        )

    def list_artifacts_for_run(self, run_id: int) -> list[dict[str, Any]]:
        query = (
            "SELECT artifact_path, target, content_hash, section_hashes_json"
            " FROM doc_artifacts WHERE run_id=?"
        )
        rows = self._conn.execute(query, (run_id,)).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            result.append(
                {
                    "artifact_path": row["artifact_path"],
                    "target": row["target"],
                    "content_hash": row["content_hash"],
                    "section_hashes": json.loads(row["section_hashes_json"] or "{}"),
                }
            )
        return result

    def clear_all(self) -> None:
        self._conn.executescript(
            """
            DELETE FROM doc_artifacts;
            DELETE FROM output_links;
            DELETE FROM file_reviews;
            DELETE FROM diff_runs;
            DELETE FROM runs;
            """
        )

    def stats(self) -> dict[str, Any]:
        run_count = self._conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        artifact_count = self._conn.execute("SELECT COUNT(*) FROM doc_artifacts").fetchone()[0]
        review_count = self._conn.execute("SELECT COUNT(*) FROM file_reviews").fetchone()[0]
        return {
            "runs": int(run_count),
            "doc_artifacts": int(artifact_count),
            "file_reviews": int(review_count),
        }
