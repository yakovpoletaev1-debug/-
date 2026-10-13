"""Загрузка базы знаний: все .md и .txt файлы из папки."""

from __future__ import annotations

from pathlib import Path

SUPPORTED_SUFFIXES = {".md", ".txt"}


def load_knowledge(directory: Path) -> str:
    """Склеивает все файлы базы знаний в один текст с заголовками-именами файлов.

    Файлы читаются в алфавитном порядке, чтобы текст был стабильным
    (это важно для кэширования промпта).
    """
    if not directory.is_dir():
        return ""
    parts: list[str] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8").strip()
        if text:
            name = path.relative_to(directory).as_posix()
            parts.append(f'<document name="{name}">\n{text}\n</document>')
    return "\n\n".join(parts)
