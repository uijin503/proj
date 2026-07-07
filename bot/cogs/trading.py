from __future__ import annotations

from decimal import Decimal

import discord
from discord import app_commands
from discord.ext import commands

from bot.services import bank as bank_service
from bot.services import market
from bot.services import trading as trading_service
from bot.utils.formatting import format_krw, format_native


class TradingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _ensure_user(self, session, interaction: discord.Interaction) -> None:
        await bank_service.get_or_create_user(
            session, interaction.user.id, str(interaction.user), self.bot.settings.initial_balance
        )

    @app_commands.command(name="시세", description="종목의 실시간 시세를 조회합니다.")
    @app_commands.describe(종목="종목코드(6자리)/티커/한글 종목명 (예: 005930, AAPL, 삼성전자)")
    async def quote(self, interaction: discord.Interaction, 종목: str) -> None:
        await interaction.response.defer()
        try:
            q = await market.get_quote(종목)
        except market.SymbolNotFoundError as e:
            await interaction.followup.send(str(e))
            return

        arrow = "🔺" if q.change > 0 else ("🔻" if q.change < 0 else "➖")
        await interaction.followup.send(
            f"**{q.name}** ({q.symbol}/{q.market})\n"
            f"{format_native(q.price, q.currency)} {arrow} {format_native(abs(q.change), q.currency)} "
            f"({q.change_pct:.2f}%)"
        )

    @app_commands.command(name="매수", description="주식을 매수합니다.")
    @app_commands.describe(종목="종목코드/티커/종목명", 수량="매수할 수량")
    async def buy(self, interaction: discord.Interaction, 종목: str, 수량: int) -> None:
        if 수량 <= 0:
            await interaction.response.send_message("수량은 1 이상이어야 합니다.", ephemeral=True)
            return
        await interaction.response.defer()

        async with self.bot.sessionmaker() as session:
            async with session.begin():
                await self._ensure_user(session, interaction)
                try:
                    result = await trading_service.buy(session, interaction.user.id, 종목, Decimal(수량))
                except market.SymbolNotFoundError as e:
                    await interaction.followup.send(str(e))
                    return
                except trading_service.InsufficientFundsError:
                    await interaction.followup.send("잔액이 부족합니다.")
                    return

        q = result["quote"]
        await interaction.followup.send(
            f"✅ **{q.name}** {수량}주 매수 완료 (총 {format_krw(result['cost_krw'])})\n"
            f"잔여 현금: {format_krw(result['balance'])}"
        )

    @app_commands.command(name="매도", description="보유 주식을 매도합니다.")
    @app_commands.describe(종목="종목코드/티커/종목명", 수량="매도할 수량")
    async def sell(self, interaction: discord.Interaction, 종목: str, 수량: int) -> None:
        if 수량 <= 0:
            await interaction.response.send_message("수량은 1 이상이어야 합니다.", ephemeral=True)
            return
        await interaction.response.defer()

        async with self.bot.sessionmaker() as session:
            async with session.begin():
                await self._ensure_user(session, interaction)
                try:
                    result = await trading_service.sell(session, interaction.user.id, 종목, Decimal(수량))
                except market.SymbolNotFoundError as e:
                    await interaction.followup.send(str(e))
                    return
                except trading_service.InsufficientSharesError:
                    await interaction.followup.send("보유 수량이 부족합니다.")
                    return

        q = result["quote"]
        pnl = result["realized_pnl"]
        pnl_text = f"(+{format_krw(pnl)})" if pnl >= 0 else f"({format_krw(pnl)})"
        await interaction.followup.send(
            f"✅ **{q.name}** {수량}주 매도 완료 (총 {format_krw(result['proceeds_krw'])}) {pnl_text}\n"
            f"잔여 현금: {format_krw(result['balance'])}"
        )

    @app_commands.command(name="포트폴리오", description="보유 종목과 평가금액을 확인합니다.")
    async def portfolio(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        async with self.bot.sessionmaker() as session:
            async with session.begin():
                await self._ensure_user(session, interaction)
                data = await trading_service.get_portfolio_value(session, interaction.user.id)

        if not data["positions"]:
            await interaction.followup.send(f"보유 종목이 없습니다.\n현금: {format_krw(data['cash'])}")
            return

        lines = [f"💵 현금: {format_krw(data['cash'])}", ""]
        for p in data["positions"]:
            sign = "+" if p["pnl"] >= 0 else ""
            lines.append(
                f"**{p['quote'].name}** {p['quantity']}주 | 평가액 {format_krw(p['value_krw'])} | "
                f"손익 {sign}{format_krw(p['pnl'])} ({sign}{p['pnl_pct']:.2f}%)"
            )
        lines.append("")
        lines.append(f"📊 총 자산: {format_krw(data['total_assets'])}")
        await interaction.followup.send("\n".join(lines))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TradingCog(bot))
