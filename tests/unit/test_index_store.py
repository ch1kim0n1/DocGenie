from pathlib import Path

from docgenie.index_store import IndexStore


def test_index_store_lifecycle(tmp_path: Path) -> None:
    store = IndexStore(tmp_path)
    run_id = store.start_run(mode="auto", engine="hybrid_index", incremental=True)

    store.upsert_file(
        path="src/main.py",
        size=10,
        mtime_ns=1,
        digest="abc",
        language="python",
        is_generated=False,
        is_hidden=False,
        ignored_reason=None,
    )
    store.replace_packages([
        {"path": ".", "package_type": "python", "manifest": "pyproject.toml", "parent_path": None}
    ])
    store.replace_symbols_and_imports(
        "src/main.py",
        [{"symbol_type": "function", "qualified_name": "main", "line": 1}],
        ["os"],
        "python",
    )
    store.add_doc_artifact(
        run_id=run_id,
        artifact_path="README.md",
        target="root",
        content_hash="hash",
        section_hashes={"Intro": "h1"},
    )
    store.finish_run(
        run_id,
        {
            "scanned_files": 1,
            "changed_files": 1,
            "skipped_files": 0,
            "duration_sec": 0.1,
            "cache_hit_ratio": 0.0,
        },
    )
    store.commit()

    rec = store.get_file_record("src/main.py")
    assert rec is not None
    assert rec["hash"] == "abc"

    latest = store.latest_run_id()
    assert latest == run_id
    arts = store.list_artifacts_for_run(run_id)
    assert len(arts) == 1
    assert arts[0]["artifact_path"] == "README.md"

    stats = store.stats()
    assert stats["files"] >= 1
    assert stats["runs"] >= 1

    store.clear_all()
    store.commit()
    assert store.stats()["files"] == 0
    store.close()
