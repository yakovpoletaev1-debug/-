from bot.knowledge import load_knowledge


def test_missing_dir_gives_empty(tmp_path):
    assert load_knowledge(tmp_path / "nope") == ""


def test_reads_md_and_txt_sorted_and_skips_others(tmp_path):
    (tmp_path / "b.txt").write_text("второй", encoding="utf-8")
    (tmp_path / "a.md").write_text("первый", encoding="utf-8")
    (tmp_path / "empty.md").write_text("   ", encoding="utf-8")
    (tmp_path / "pic.png").write_bytes(b"\x89PNG")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.md").write_text("третий", encoding="utf-8")

    text = load_knowledge(tmp_path)

    assert text.index("первый") < text.index("второй") < text.index("третий")
    assert '<document name="sub/c.md">' in text
    assert "empty.md" not in text
    assert "PNG" not in text
