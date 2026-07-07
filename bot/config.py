from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    discord_token: str
    database_url: str
    initial_balance: Decimal
    daily_bonus: Decimal
    guild_id: int | None


def load_settings() -> Settings:
    guild_id_raw = os.environ.get("GUILD_ID")
    return Settings(
        discord_token=os.environ["DISCORD_TOKEN"],
        database_url=os.environ["DATABASE_URL"],
        initial_balance=Decimal(os.environ.get("INITIAL_BALANCE", "10000000")),
        daily_bonus=Decimal(os.environ.get("DAILY_BONUS", "100000")),
        guild_id=int(guild_id_raw) if guild_id_raw else None,
    )
