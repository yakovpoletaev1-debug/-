from types import SimpleNamespace as NS

from bot.history import ChatLine
from bot.llm import (
    FALLBACK_BETA,
    SKIP_MARKER,
    Responder,
    build_system,
    build_user_message,
    extract_reply,
)


def text(t):
    return NS(type="text", text=t)


def response(*blocks, stop_reason="end_turn"):
    return NS(content=list(blocks), stop_reason=stop_reason, stop_details=None)


class FakeMessages:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def create(self, **params):
        self.calls.append(params)
        return self.result


def fake_client(result):
    messages = FakeMessages(result)
    return NS(beta=NS(messages=messages)), messages


def test_system_contains_persona_knowledge_examples_and_is_cached():
    [block] = build_system("Куратор Аня", "СТАРТ 1 МАЯ", "<example>x</example>")
    assert "Куратор Аня" in block["text"]
    assert "СТАРТ 1 МАЯ" in block["text"]
    assert "<example>x</example>" in block["text"]
    assert SKIP_MARKER in block["text"]
    assert block["cache_control"] == {"type": "ephemeral"}


def test_system_placeholders_when_empty():
    [block] = build_system("Бот", "", "")
    assert "База знаний пока пуста." in block["text"]
    assert "Примеров пока нет." in block["text"]


def test_user_message_includes_history_and_question():
    msg = build_user_message([ChatLine("Петя", "всем привет")], "Аня", "Когда старт?")
    assert "Петя: всем привет" in msg
    assert '<message author="Аня">\nКогда старт?' in msg
    assert "(пусто)" in build_user_message([], "Аня", "?")


def test_extract_reply():
    assert extract_reply(response(NS(type="thinking"), text(" Ответ "))) == "Ответ"
    assert extract_reply(response(text(SKIP_MARKER))) is None
    assert extract_reply(response()) is None
    assert extract_reply(response(text("x"), stop_reason="refusal")) is None


async def test_responder_sends_expected_request_with_fallback():
    client, messages = fake_client(response(text("В понедельник")))
    system = build_system("Бот", "k", "e")
    r = Responder(client, "claude-opus-5-5", "low", system)

    answer = await r.reply([ChatLine("A", "hi")], "Петя", "Когда старт?")

    assert answer == "В понедельник"
    [call] = messages.calls
    assert call["model"] == "claude-opus-5-5"
    assert call["system"] is system
    assert call["output_config"] == {"effort": "low"}
    assert call["betas"] == [FALLBACK_BETA]
    assert call["fallbacks"] == "default"
    assert "Когда старт?" in call["messages"][0]["content"]


async def test_responder_omits_fallback_for_unsupported_models():
    client, messages = fake_client(response(text("ok")))
    await Responder(client, "claude-haiku-5-5", "low", []).reply([], "A", "hi")
    assert "fallbacks" not in messages.calls[0]
    assert "betas" not in messages.calls[0]
