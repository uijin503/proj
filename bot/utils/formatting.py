from decimal import Decimal


def format_krw(amount: Decimal) -> str:
    return f"{int(amount):,}원"


def format_native(amount: Decimal, currency: str) -> str:
    if currency == "KRW":
        return f"{int(amount):,}원"
    return f"${amount:,.2f}"
