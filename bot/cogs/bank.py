from __future__ import annotations

from decimal import Decimal, InvalidOperation

import discord
from discord import app_commands
from discord.ext import commands

from bot.services import bank as bank_service
from bot.utils.formatting import format_krw


class BankCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="계좌", description="계좌를 조회하거나 없으면 새로 개설합니다.")
    async def account(self, interaction: discord.Interaction) -> None:
        async with self.bot.sessionmaker() as session:
            async with session.begin():
                user = await bank_service.get_or_create_user(
                    session, interaction.user.id, str(interaction.user), self.bot.settings.initial_balance
                )
                balance = user.cash_balance
        await interaction.response.send_message(
            f"💰 **{interaction.user.display_name}**님의 계좌 잔고: {format_krw(balance)}"
        )

    @app_commands.command(name="잔고", description="현재 보유 현금을 확인합니다.")
    async def balance(self, interaction: discord.Interaction) -> None:
        async with self.bot.sessionmaker() as session:
            async with session.begin():
                user = await bank_service.get_or_create_user(
                    session, interaction.user.id, str(interaction.user), self.bot.settings.initial_balance
                )
                balance = user.cash_balance
        await interaction.response.send_message(f"💰 현재 잔고: {format_krw(balance)}")

    @app_commands.command(name="송금", description="다른 유저에게 가상 자금을 송금합니다.")
    @app_commands.describe(대상="송금 받을 유저", 금액="송금할 금액(원)")
    async def send_money(self, interaction: discord.Interaction, 대상: discord.Member, 금액: str) -> None:
        try:
            amount = Decimal(금액)
        except InvalidOperation:
            await interaction.response.send_message("금액은 숫자로 입력해주세요.", ephemeral=True)
            return

        async with self.bot.sessionmaker() as session:
            async with session.begin():
                await bank_service.get_or_create_user(
                    session, interaction.user.id, str(interaction.user), self.bot.settings.initial_balance
                )
                await bank_service.get_or_create_user(
                    session, 대상.id, str(대상), self.bot.settings.initial_balance
                )
                try:
                    await bank_service.transfer(session, interaction.user.id, 대상.id, amount)
                except bank_service.InsufficientFundsError:
                    await interaction.response.send_message("잔액이 부족합니다.", ephemeral=True)
                    return
                except ValueError as e:
                    await interaction.response.send_message(str(e), ephemeral=True)
                    return

        await interaction.response.send_message(
            f"✅ {interaction.user.display_name} → {대상.display_name}: {format_krw(amount)} 송금 완료"
        )

    @app_commands.command(name="출석", description="하루에 한 번 출석 보너스를 받습니다.")
    async def daily(self, interaction: discord.Interaction) -> None:
        async with self.bot.sessionmaker() as session:
            async with session.begin():
                await bank_service.get_or_create_user(
                    session, interaction.user.id, str(interaction.user), self.bot.settings.initial_balance
                )
                try:
                    balance = await bank_service.claim_daily(
                        session, interaction.user.id, self.bot.settings.daily_bonus
                    )
                except bank_service.CooldownError as e:
                    hours, remainder = divmod(int(e.remaining.total_seconds()), 3600)
                    minutes = remainder // 60
                    await interaction.response.send_message(
                        f"⏳ 이미 출석하셨습니다. {hours}시간 {minutes}분 후 다시 시도해주세요.", ephemeral=True
                    )
                    return

        await interaction.response.send_message(
            f"🎁 출석 보너스 {format_krw(self.bot.settings.daily_bonus)} 지급! 현재 잔고: {format_krw(balance)}"
        )

    @app_commands.command(name="거래내역", description="최근 거래 내역을 확인합니다.")
    async def history(self, interaction: discord.Interaction) -> None:
        async with self.bot.sessionmaker() as session:
            async with session.begin():
                txs = await bank_service.get_recent_transactions(session, interaction.user.id, limit=10)

        if not txs:
            await interaction.response.send_message("거래 내역이 없습니다.", ephemeral=True)
            return

        lines = []
        for tx in txs:
            sign = "+" if tx.amount_krw >= 0 else ""
            lines.append(f"`{tx.created_at:%m/%d %H:%M}` {tx.type} {sign}{format_krw(tx.amount_krw)}")
        await interaction.response.send_message("\n".join(lines), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BankCog(bot))
