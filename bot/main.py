"""Запуск бота: python -m bot.main"""

from __future__ import annotations

import asyncio
import logging
import random

import anthropic
from aiogram import Bot, Dispatcher
from aiogram.enums import ChatAction
from aiogram.types import Message
from dotenv import load_dotenv

from .chat_export import format_examples, load_examples
from .config import Settings
from .history import ChatHistory
from .knowledge import load_knowledge
from .llm import Responder, build_system
from .triggers import IncomingMessage, should_reply

log = logging.getLogger(__name__)


def author_name(message: Message) -> str:
    user = message.from_user
    if user is None:
        return message.sender_chat.title if message.sender_chat else "Аноним"
    return user.full_name or user.username or str(user.id)


def to_incoming(message: Message, bot_id: int, bot_username: str) -> IncomingMessage:
    text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []
    mention = f"@{bot_username}".lower()
    mentions_bot = any(
        (e.type == "mention" and e.extract_from(text).lower() == mention)
        or (e.type == "text_mention" and e.user is not None and e.user.id == bot_id)
        for e in entities
    )
    reply = message.reply_to_message
    is_reply_to_bot = bool(reply and reply.from_user and reply.from_user.id == bot_id)
    return IncomingMessage(
        chat_type=message.chat.type,
        text=text,
        mentions_bot=mentions_bot,
        is_reply_to_bot=is_reply_to_bot,
        from_bot=bool(message.from_user and message.from_user.is_bot),
    )


def typing_delay(answer: str) -> float:
    """Пауза «печатает…», чтобы ответ не прилетал мгновенно, как у робота."""
    return min(1.5 + len(answer) * 0.03, 8.0) + random.uniform(0, 1.5)


async def run(settings: Settings) -> None:
    knowledge = load_knowledge(settings.knowledge_dir)
    examples = load_examples(
        settings.chat_export_path, settings.expert_authors, settings.max_examples
    )
    log.info("База знаний: %d символов, примеров из чата: %d", len(knowledge), len(examples))

    responder = Responder(
        client=anthropic.AsyncAnthropic(),
        model=settings.claude_model,
        effort=settings.claude_effort,
        system=build_system(settings.bot_persona, knowledge, format_examples(examples)),
    )
    history = ChatHistory(settings.history_size)
    bot = Bot(settings.telegram_token)
    me = await bot.get_me()
    dp = Dispatcher()

    @dp.message()
    async def on_message(message: Message) -> None:
        if settings.allowed_chat_ids and message.chat.id not in settings.allowed_chat_ids:
            return
        incoming = to_incoming(message, me.id, me.username or "")
        author = author_name(message)
        context = history.recent(message.chat.id)
        history.add(message.chat.id, author, incoming.text)
        if not should_reply(incoming):
            return
        try:
            await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
            answer = await responder.reply(context, author, incoming.text)
        except anthropic.APIError:
            log.exception("Ошибка Claude API")
            return
        if not answer:
            return
        if settings.human_delay:
            await asyncio.sleep(typing_delay(answer))
        answer = answer[:4096]  # лимит длины сообщения Telegram
        await message.reply(answer)
        history.add(message.chat.id, me.full_name, answer)

    log.info("Бот @%s запущен", me.username)
    await dp.start_polling(bot)


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(run(Settings.from_env()))


if __name__ == "__main__":
    main()
