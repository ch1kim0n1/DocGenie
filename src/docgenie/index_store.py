"""Persistent SQLite index for scalable/incremental DocGenie analysis."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


class IndexStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.db_path = root / ".docgenie" / "index.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._migrate()

    def close(self) -> None:
        self._conn.close()

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
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                size INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL,
                hash TEXT NOT NULL,
                language TEXT,
                is_generated INTEGER NOT NULL DEFAULT 0,
                is_hidden INTEGER NOT NULL DEFAULT 0,
                ignored_reason TEXT,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol_type TEXT NOT NULL,
                qualified_name TEXT NOT NULL,
                path TEXT NOT NULL,
                line INTEGER,
                signature_hash TEXT,
                UNIQUE(symbol_type, qualified_name, path, line)
            );

            CREATE TABLE IF NOT EXISTS imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                language TEXT,
                imported TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS packages (
                path TEXT PRIMARY KEY,
                package_type TEXT NOT NULL,
                manifest TEXT,
                parent_path TEXT
            );

            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at REAL NOT NULL,
                finished_at REAL,
                mode TEXT,
                engine TEXT,
                incremental INTEGER NOT NULL,
                scanned_files INTEGER NOT NULL DEFAULT 0,
                changed_files INTEGER NOT NULL DEFAULT 0,
                skipped_files INTEGER NOT NULL DEFAULT 0,
                duration_sec REAL,
                cache_hit_ratio REAL,
                metrics_json TEXT
            );

            CREATE TABLE IF NOT EXISTS docs_artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                artifact_path TEXT NOT NULL,
                target TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                section_hashes TEXT,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            );
            """
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) VALUES('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        self._conn.commit()

    def clear_all(self) -> None:
        for table in ["docs_artifacts", "symbols", "imports", "files", "packages", "runs"]:
            self._conn.execute(f"DELETE FROM {table}")
        self._conn.commit()

    def get_file_record(self, path: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT path,size,mtime_ns,hash,language,is_generated,is_hidden,ignored_reason FROM files WHERE path=?",
            (path,),
        ).fetchone()
        return dict(row) if row else None

    def upsert_file(
        self,
        *,
        path: str,
        size: int,
        mtime_ns: int,
        digest: str,
        language: str | None,
        is_generated: bool,
        is_hidden: bool,
        ignored_reason: str | None,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO files(path,size,mtime_ns,hash,language,is_generated,is_hidden,ignored_reason,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(path) DO UPDATE SET
              size=excluded.size,
              mtime_ns=excluded.mtime_ns,
              hash=excluded.hash,
              language=excluded.language,
              is_generated=excluded.is_generated,
              is_hidden=excluded.is_hidden,
              ignored_reason=excluded.ignored_reason,
              updated_at=excluded.updated_at
            """,
            (
                path,
                size,
                mtime_ns,
                digest,
                language,
                1 if is_generated else 0,
                1 if is_hidden else 0,
                ignored_reason,
                time.time(),
            ),
        )

    def replace_packages(self, packages: list[dict[str, Any]]) -> None:
        self._conn.execute("DELETE FROM packages")
        for pkg in packages:
            self._conn.execute(
                "INSERT INTO packages(path,package_type,manifest,parent_path) VALUES(?,?,?,?)",
                (
                    pkg.get("path", ""),
                    pkg.get("package_type", "unknown"),
                    pkg.get("manifest"),
                    pkg.get("parent_path"),
                ),
            )

    def replace_symbols_and_imports(self, path: str, symbols: list[dict[str, Any]], imports: list[str], language: str) -> None:
        self._conn.execute("DELETE FROM symbols WHERE path=?", (path,))
        self._conn.execute("DELETE FROM imports WHERE path=?", (path,))
        for sym in symbols:
            self._conn.execute(
                "INSERT OR IGNORE INTO symbols(symbol_type,qualified_name,path,line,signature_hash) VALUES(?,?,?,?,?)",
                (
                    sym.get("symbol_type", "function"),
                    sym.get("qualified_name") or sym.get("name", ""),
                    path,
                    int(sym.get("line", 0) or 0),
                    sym.get("signature_hash"),
                ),
            )
        for imp in imports:
            self._conn.execute(
                "INSERT INTO imports(path,language,imported) VALUES(?,?,?)",
                (path, language, imp),
            )

    def start_run(self, *, mode: str, engine: str, incremental: bool) -> int:
        cur = self._conn.execute(
            "INSERT INTO runs(started_at,mode,engine,incremental) VALUES(?,?,?,?)",
            (time.time(), mode, engine, 1 if incremental else 0),
        )
        return int(cur.lastrowid)

    def finish_run(self, run_id: int, metrics: dict[str, Any]) -> None:
        self._conn.execute(
            """
            UPDATE runs
               SET finished_at=?,
                   scanned_files=?,
                   changed_files=?,
                   skipped_files=?,
                   duration_sec=?,
                   cache_hit_ratio=?,
                   metrics_json=?
             WHERE id=?
            """,
            (
                time.time(),
                int(metrics.get("scanned_files", 0)),
                int(metrics.get("changed_files", 0)),
                int(metrics.get("skipped_files", 0)),
                float(metrics.get("duration_sec", 0.0)),
                float(metrics.get("cache_hit_ratio", 0.0)),
                json.dumps(metrics, sort_keys=True),
                run_id,
            ),
        )

    def add_doc_artifact(
        self,
        *,
        run_id: int,
        artifact_path: str,
        target: str,
        content_hash: str,
        section_hashes: dict[str, str] | None,
    ) -> None:
        self._conn.execute(
            "INSERT INTO docs_artifacts(run_id,artifact_path,target,content_hash,section_hashes) VALUES(?,?,?,?,?)",
            (
                run_id,
                artifact_path,
                target,
                content_hash,
                json.dumps(section_hashes or {}, sort_keys=True),
            ),
        )

    def latest_run_id(self) -> int | None:
        row = self._conn.execute("SELECT id FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        return int(row["id"]) if row else None

    def get_run(self, run_id: int) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        return dict(row) if row else None

    def list_artifacts_for_run(self, run_id: int) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT artifact_path,target,content_hash,section_hashes FROM docs_artifacts WHERE run_id=?",
            (run_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> dict[str, Any]:
        def count(table: str) -> int:
            row = self._conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
            return int(row["c"] if row else 0)

        latest = self.latest_run_id()
        latest_run = self.get_run(latest) if latest else None
        return {
            "db_path": str(self.db_path),
            "schema_version": SCHEMA_VERSION,
            "files": count("files"),
            "symbols": count("symbols"),
            "imports": count("imports"),
            "packages": count("packages"),
            "runs": count("runs"),
            "docs_artifacts": count("docs_artifacts"),
            "latest_run": latest_run,
        }

    def commit(self) -> None:
        self._conn.commit()
