from types import SimpleNamespace as NS

from bot.main import author_name, to_incoming, typing_delay

BOT_ID = 42


class Entity(NS):
    def extract_from(self, text):
        return text[self.offset : self.offset + self.length]


def message(text="", entities=None, reply_from=None, from_user=None, chat_type="supergroup"):
    return NS(
        text=text,
        caption=None,
        entities=entities,
        caption_entities=None,
        chat=NS(type=chat_type),
        reply_to_message=NS(from_user=reply_from) if reply_from else None,
        from_user=from_user or NS(id=1, is_bot=False, full_name="Петя", username="petya"),
        sender_chat=None,
    )


def test_detects_username_mention_case_insensitive():
    m = message("@Marathon_Bot когда старт?", [Entity(type="mention", offset=0, length=13)])
    assert to_incoming(m, BOT_ID, "marathon_bot").mentions_bot is True


def test_other_mention_is_not_ours():
    m = message("@someone привет", [Entity(type="mention", offset=0, length=8)])
    assert to_incoming(m, BOT_ID, "marathon_bot").mentions_bot is False


def test_text_mention_by_id():
    m = message("Бот, привет", [Entity(type="text_mention", offset=0, length=3, user=NS(id=BOT_ID))])
    assert to_incoming(m, BOT_ID, "marathon_bot").mentions_bot is True


def test_reply_to_bot_and_from_bot():
    m = message("а точно?", reply_from=NS(id=BOT_ID))
    assert to_incoming(m, BOT_ID, "b").is_reply_to_bot is True
    other = message("а точно?", reply_from=NS(id=7))
    assert to_incoming(other, BOT_ID, "b").is_reply_to_bot is False
    bot_msg = message("hi", from_user=NS(id=9, is_bot=True))
    assert to_incoming(bot_msg, BOT_ID, "b").from_bot is True


def test_caption_used_when_no_text():
    m = message(None)
    m.caption = "подпись к фото"
    assert to_incoming(m, BOT_ID, "b").text == "подпись к фото"


def test_author_name_fallbacks():
    assert author_name(message()) == "Петя"
    assert author_name(NS(from_user=None, sender_chat=NS(title="Канал"))) == "Канал"
    assert author_name(NS(from_user=None, sender_chat=None)) == "Аноним"
    assert author_name(NS(from_user=NS(full_name="", username="", id=5))) == "5"


def test_typing_delay_bounds():
    assert 1.5 <= typing_delay("") <= 3.0
    assert typing_delay("x" * 10_000) <= 9.5
