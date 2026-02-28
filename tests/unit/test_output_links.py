from __future__ import annotations

from pathlib import Path

from docgenie.output_links import scan_output_links


def test_scan_output_links_detects_patterns(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("open('out.txt', 'w').write('x')\n", encoding="utf-8")
    (tmp_path / "b.js").write_text("fs.writeFileSync('dist.txt', 'x')\n", encoding="utf-8")
    (tmp_path / "c.sh").write_text("echo hi > log.txt\n", encoding="utf-8")

    links = scan_output_links(tmp_path)
    assert len(links) >= 3
    targets = {x.get("target_file") for x in links}
    assert "out.txt" in targets
    assert "dist.txt" in targets
    assert "log.txt" in targets


def test_scan_output_links_marks_unresolved(tmp_path: Path) -> None:
    f = tmp_path / "x.py"
    f.write_text("open(f'{name}.txt', 'w')\n", encoding="utf-8")
    links = scan_output_links(tmp_path)
    assert links
    assert links[0]["target_file"] is None
    assert links[0]["resolved"] is False
