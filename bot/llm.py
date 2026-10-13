"""Составление ответа через Claude."""

from __future__ import annotations

import logging

import anthropic

from .history import ChatLine

log = logging.getLogger(__name__)

SKIP_MARKER = "<skip>"

# Модели, которые поддерживают серверный fallback при отказе (stop_reason "refusal").
FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}
FALLBACK_BETA = "server-side-fallback-2026-07-01"

INSTRUCTIONS = """\
Ты — {persona}, участник Telegram-чата марафона. Ты отвечаешь людям в чате.

Как отвечать:
- Пиши как живой человек в мессенджере: коротко, по делу, дружелюбно, своими словами.
  Обычно 1–3 предложения. Без приветствий-шаблонов и без «Отличный вопрос!».
- Подражай тону и манере ответов из раздела <examples> — так в этом чате отвечают люди.
- Не используй markdown (звёздочки, решётки, списки с дефисами): Telegram покажет их как есть.
- Отвечай на том языке, на котором написал человек.
- Факты бери только из <knowledge>. Если там нет ответа, не выдумывай: честно скажи,
  что уточнишь у организаторов, или спроси, что именно человек имеет в виду.
- Не говори, что ты ИИ, бот или языковая модель, если тебя прямо не спросили.
  Если спросили прямо — не обманывай.
- Если сообщение не требует ответа (просто реплика, благодарность, разговор не с тобой),
  ответь ровно {skip} и больше ничего.
"""


def build_system(persona: str, knowledge: str, examples: str) -> list[dict]:
    """Системный промпт. Неизменная часть идёт первой и кэшируется."""
    text = INSTRUCTIONS.format(persona=persona, skip=SKIP_MARKER)
    text += f"\n<knowledge>\n{knowledge or 'База знаний пока пуста.'}\n</knowledge>\n"
    text += f"\n<examples>\n{examples or 'Примеров пока нет.'}\n</examples>"
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def build_user_message(history: list[ChatLine], author: str, text: str) -> str:
    lines = "\n".join(f"{line.author}: {line.text}" for line in history)
    return (
        f"<chat_history>\n{lines or '(пусто)'}\n</chat_history>\n\n"
        f"Ответь на это сообщение.\n<message author=\"{author}\">\n{text}\n</message>"
    )


def extract_reply(response) -> str | None:
    """Текст ответа или None, если отвечать не нужно."""
    if response.stop_reason == "refusal":
        log.warning("Модель отказалась отвечать: %s", response.stop_details)
        return None
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if not text or SKIP_MARKER in text:
        return None
    return text


class Responder:
    def __init__(
        self,
        client: anthropic.AsyncAnthropic,
        model: str,
        effort: str,
        system: list[dict],
    ) -> None:
        self._client = client
        self._model = model
        self._effort = effort
        self._system = system

    async def reply(self, history: list[ChatLine], author: str, text: str) -> str | None:
        params: dict = {
            "model": self._model,
            "max_tokens": 4000,
            "system": self._system,
            "output_config": {"effort": self._effort},
            "messages": [{"role": "user", "content": build_user_message(history, author, text)}],
        }
        if self._model in FALLBACK_MODELS:
            params["betas"] = [FALLBACK_BETA]
            params["fallbacks"] = "default"
        response = await self._client.beta.messages.create(**params)
        return extract_reply(response)
