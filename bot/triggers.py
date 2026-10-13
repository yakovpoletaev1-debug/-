"""Когда бот отвечает на сообщение.

Здесь собраны правила «отвечать или промолчать». Чтобы поменять поведение,
правьте функцию ``should_reply`` или добавьте функцию в ``CUSTOM_RULES``.
Правила намеренно не зависят от aiogram — их легко тестировать.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class IncomingMessage:
    chat_type: str  # "private", "group", "supergroup"
    text: str
    mentions_bot: bool = False  # в тексте есть @username бота
    is_reply_to_bot: bool = False  # человек ответил на сообщение бота
    from_bot: bool = False  # сообщение написал бот


# Дополнительные правила: функция получает сообщение и возвращает
# True (ответить), False (промолчать) или None (правило не решает).
# Правила проверяются по порядку, первое ответившее True/False побеждает.
# Пример:
#     def answer_questions(msg): return True if msg.text.rstrip().endswith("?") else None
#     CUSTOM_RULES.append(answer_questions)
Rule = Callable[[IncomingMessage], "bool | None"]
CUSTOM_RULES: list[Rule] = []


def should_reply(message: IncomingMessage, rules: list[Rule] | None = None) -> bool:
    if message.from_bot or not message.text.strip():
        return False
    for rule in CUSTOM_RULES if rules is None else rules:
        decision = rule(message)
        if decision is not None:
            return decision
    if message.chat_type == "private":
        return True
    return message.mentions_bot or message.is_reply_to_bot
