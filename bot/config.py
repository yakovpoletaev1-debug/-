"""Настройки бота из переменных окружения (или файла .env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "да"}


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    claude_model: str = "claude-opus-5-5"
    claude_effort: str = "low"
    bot_persona: str = "Помощник марафона"
    knowledge_dir: Path = Path("data/knowledge")
    chat_export_path: Path | None = None
    expert_authors: list[str] = field(default_factory=list)
    max_examples: int = 150
    history_size: int = 30
    allowed_chat_ids: list[int] = field(default_factory=list)
    human_delay: bool = True

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        env = dict(os.environ if env is None else env)
        token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise ValueError("Не задан TELEGRAM_BOT_TOKEN (токен от @BotFather).")
        export = env.get("CHAT_EXPORT_PATH", "").strip()
        return cls(
            telegram_token=token,
            claude_model=env.get("CLAUDE_MODEL", "").strip() or cls.claude_model,
            claude_effort=env.get("CLAUDE_EFFORT", "").strip() or cls.claude_effort,
            bot_persona=env.get("BOT_PERSONA", "").strip() or cls.bot_persona,
            knowledge_dir=Path(env.get("KNOWLEDGE_DIR", "").strip() or "data/knowledge"),
            chat_export_path=Path(export) if export else None,
            expert_authors=_split(env.get("EXPERT_AUTHORS")),
            max_examples=int(env.get("MAX_EXAMPLES") or cls.max_examples),
            history_size=int(env.get("HISTORY_SIZE") or cls.history_size),
            allowed_chat_ids=[int(x) for x in _split(env.get("ALLOWED_CHAT_IDS"))],
            human_delay=_bool(env.get("HUMAN_DELAY"), True),
        )
