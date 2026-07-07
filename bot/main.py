from __future__ import annotations

import logging

import discord
from discord.ext import commands

from bot.config import Settings, load_settings
from bot.db.base import make_engine, make_sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("paper_trading_bot")

EXTENSIONS = (
    "bot.cogs.bank",
    "bot.cogs.trading",
    "bot.cogs.leaderboard",
)


class PaperTradingBot(commands.Bot):
    def __init__(self, settings: Settings):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.settings = settings
        engine = make_engine(settings.database_url)
        self.sessionmaker = make_sessionmaker(engine)

    async def setup_hook(self) -> None:
        for ext in EXTENSIONS:
            await self.load_extension(ext)

        if self.settings.guild_id:
            guild = discord.Object(id=self.settings.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()


def main() -> None:
    settings = load_settings()
    bot = PaperTradingBot(settings)

    @bot.event
    async def on_ready() -> None:
        logger.info("Logged in as %s", bot.user)

    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
