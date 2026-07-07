from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from bot.db.models import User
from bot.services import trading as trading_service
from bot.utils.formatting import format_krw


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="순위", description="총 자산 기준 순위를 확인합니다.")
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        async with self.bot.sessionmaker() as session:
            async with session.begin():
                result = await session.execute(select(User.discord_id))
                user_ids = [row[0] for row in result.all()]

                rankings = []
                for uid in user_ids:
                    data = await trading_service.get_portfolio_value(session, uid)
                    rankings.append((uid, data["total_assets"]))

        rankings.sort(key=lambda r: r[1], reverse=True)

        if not rankings:
            await interaction.followup.send("아직 등록된 유저가 없습니다.")
            return

        lines = []
        for i, (uid, total) in enumerate(rankings[:10], start=1):
            member = interaction.guild.get_member(uid) if interaction.guild else None
            name = member.display_name if member else f"<@{uid}>"
            lines.append(f"{i}. {name} — {format_krw(total)}")

        await interaction.followup.send("🏆 **자산 순위 TOP 10**\n" + "\n".join(lines))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LeaderboardCog(bot))
