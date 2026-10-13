"""Последние сообщения каждого чата — чтобы бот понимал контекст разговора."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class ChatLine:
    author: str
    text: str


class ChatHistory:
    def __init__(self, size: int = 30) -> None:
        self._size = size
        self._chats: dict[int, deque[ChatLine]] = defaultdict(lambda: deque(maxlen=size))

    def add(self, chat_id: int, author: str, text: str) -> None:
        if self._size > 0 and text.strip():
            self._chats[chat_id].append(ChatLine(author, text.strip()))

    def recent(self, chat_id: int) -> list[ChatLine]:
        return list(self._chats.get(chat_id, ()))
