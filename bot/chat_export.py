"""Примеры ответов из экспорта чата Telegram.

Экспорт делается в Telegram Desktop: меню чата → «Экспорт истории чата» →
формат «Машиночитаемый JSON». Получается файл result.json.

Из него берутся пары «сообщение → ответ на него» (ответы, сделанные через
«Ответить»), чтобы бот видел, как в чате на самом деле отвечают люди.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

MAX_TEXT_LEN = 1000


@dataclass(frozen=True)
class Example:
    question: str
    answer: str
    answer_author: str


def message_text(raw: object) -> str:
    """Текст сообщения из экспорта: строка или список строк и сущностей."""
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, list):
        chunks = []
        for item in raw:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                chunks.append(str(item.get("text", "")))
        return "".join(chunks).strip()
    return ""


def _author_matches(msg: dict, experts: list[str]) -> bool:
    if not experts:
        return True
    wanted = {e.lower() for e in experts}
    candidates = {str(msg.get("from", "")).lower(), str(msg.get("from_id", "")).lower()}
    return bool(wanted & candidates)


def extract_examples(
    export: dict, experts: list[str] | None = None, limit: int = 150
) -> list[Example]:
    """Пары вопрос-ответ из экспорта. Берутся самые свежие ``limit`` пар.

    ``experts`` — имена или from_id (например ``user123456``) тех, чьи ответы
    считаются образцовыми (организаторы, кураторы). Пусто — учитываются все.
    """
    experts = experts or []
    messages = [m for m in export.get("messages", []) if m.get("type") == "message"]
    by_id = {m.get("id"): m for m in messages}
    examples: list[Example] = []
    for msg in messages:
        parent = by_id.get(msg.get("reply_to_message_id"))
        if parent is None:
            continue
        if parent.get("from_id") == msg.get("from_id"):
            continue  # человек отвечает сам себе — это не пример ответа
        if not _author_matches(msg, experts):
            continue
        question = message_text(parent.get("text"))
        answer = message_text(msg.get("text"))
        if not question or not answer:
            continue
        if len(question) > MAX_TEXT_LEN or len(answer) > MAX_TEXT_LEN:
            continue
        examples.append(Example(question, answer, str(msg.get("from", ""))))
    if limit <= 0:
        return []
    return examples[-limit:]


def load_examples(
    path: Path | None, experts: list[str] | None = None, limit: int = 150
) -> list[Example]:
    if path is None or not path.is_file():
        return []
    export = json.loads(path.read_text(encoding="utf-8"))
    return extract_examples(export, experts, limit)


def format_examples(examples: list[Example]) -> str:
    return "\n\n".join(
        f"<example>\nСообщение: {e.question}\nОтвет: {e.answer}\n</example>"
        for e in examples
    )
