import pytest

from bot.triggers import IncomingMessage, should_reply


def group(**kw):
    return IncomingMessage(chat_type="supergroup", text=kw.pop("text", "привет"), **kw)


@pytest.mark.parametrize(
    "message, expected",
    [
        (IncomingMessage("private", "привет"), True),
        (group(), False),
        (group(mentions_bot=True), True),
        (group(is_reply_to_bot=True), True),
        (group(mentions_bot=True, from_bot=True), False),
        (group(mentions_bot=True, text="   "), False),
    ],
)
def test_default_rules(message, expected):
    assert should_reply(message, rules=[]) is expected


def test_custom_rule_can_force_reply_or_silence():
    questions = lambda m: True if m.text.endswith("?") else None
    never_private = lambda m: False if m.chat_type == "private" else None

    assert should_reply(group(text="Когда старт?"), rules=[questions]) is True
    assert should_reply(group(text="Ок"), rules=[questions]) is False
    assert should_reply(IncomingMessage("private", "hi"), rules=[never_private]) is False


def test_first_deciding_rule_wins():
    rules = [lambda m: None, lambda m: False, lambda m: True]
    assert should_reply(group(mentions_bot=True), rules=rules) is False
