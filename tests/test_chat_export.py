import json

from bot.chat_export import (
    Example,
    extract_examples,
    format_examples,
    load_examples,
    message_text,
)


def msg(id, frm, from_id, text, reply_to=None, type="message"):
    m = {"id": id, "type": type, "from": frm, "from_id": from_id, "text": text}
    if reply_to is not None:
        m["reply_to_message_id"] = reply_to
    return m


EXPORT = {
    "messages": [
        msg(1, "Петя", "user1", "Когда старт?"),
        msg(2, "Анна", "user2", "В понедельник в 9:00", reply_to=1),
        msg(3, "Петя", "user1", "А я уточню", reply_to=1),  # сам себе
        msg(4, "Вася", "user3", [{"type": "bold", "text": "Где"}, " задания?"]),
        msg(5, "Олег", "user4", "В закрепе", reply_to=4),
        msg(6, "Олег", "user4", "Ответ на удалённое", reply_to=999),
        msg(7, "Олег", "user4", "", reply_to=4),
        {"id": 8, "type": "service", "action": "pin_message"},
    ]
}


def test_message_text_handles_strings_entities_and_garbage():
    assert message_text("  привет ") == "привет"
    assert message_text(["a", {"type": "link", "text": "b"}, {"x": 1}]) == "ab"
    assert message_text(None) == ""


def test_extracts_reply_pairs():
    assert extract_examples(EXPORT) == [
        Example("Когда старт?", "В понедельник в 9:00", "Анна"),
        Example("Где задания?", "В закрепе", "Олег"),
    ]


def test_filters_by_expert_name_or_id():
    assert [e.answer for e in extract_examples(EXPORT, ["анна"])] == ["В понедельник в 9:00"]
    assert [e.answer for e in extract_examples(EXPORT, ["user4"])] == ["В закрепе"]


def test_limit_keeps_most_recent():
    assert [e.answer for e in extract_examples(EXPORT, limit=1)] == ["В закрепе"]
    assert extract_examples(EXPORT, limit=0) == []


def test_skips_too_long_messages():
    export = {"messages": [msg(1, "A", "u1", "x" * 1001), msg(2, "B", "u2", "ok", reply_to=1)]}
    assert extract_examples(export) == []


def test_load_examples_from_file(tmp_path):
    path = tmp_path / "result.json"
    path.write_text(json.dumps(EXPORT, ensure_ascii=False), encoding="utf-8")
    assert len(load_examples(path)) == 2
    assert load_examples(None) == []
    assert load_examples(tmp_path / "missing.json") == []


def test_format_examples():
    text = format_examples([Example("Q", "A", "Анна")])
    assert text == "<example>\nСообщение: Q\nОтвет: A\n</example>"
