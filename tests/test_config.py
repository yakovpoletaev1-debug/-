from pathlib import Path

import pytest

from bot.config import Settings


def test_requires_telegram_token():
    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        Settings.from_env({})


def test_defaults():
    s = Settings.from_env({"TELEGRAM_BOT_TOKEN": "t"})
    assert s.claude_model == "claude-opus-5-5"
    assert s.claude_effort == "low"
    assert s.knowledge_dir == Path("data/knowledge")
    assert s.chat_export_path is None
    assert s.expert_authors == []
    assert s.allowed_chat_ids == []
    assert s.human_delay is True


def test_parses_lists_numbers_and_flags():
    s = Settings.from_env({
        "TELEGRAM_BOT_TOKEN": " t ",
        "EXPERT_AUTHORS": "Анна, user42 ,",
        "ALLOWED_CHAT_IDS": "-100123, 5",
        "MAX_EXAMPLES": "10",
        "HISTORY_SIZE": "5",
        "HUMAN_DELAY": "no",
        "CHAT_EXPORT_PATH": "x/result.json",
    })
    assert s.telegram_token == "t"
    assert s.expert_authors == ["Анна", "user42"]
    assert s.allowed_chat_ids == [-100123, 5]
    assert (s.max_examples, s.history_size) == (10, 5)
    assert s.human_delay is False
    assert s.chat_export_path == Path("x/result.json")
