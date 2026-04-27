def expected_average_fill_price(asks: list[tuple[float, float]], krw_budget: float) -> float:
    remaining = krw_budget
    total_qty = 0.0
    spent = 0.0
    for price, qty in asks:
        level_value = price * qty
        take_value = min(level_value, remaining)
        take_qty = take_value / price
        spent += take_value
        total_qty += take_qty
        remaining -= take_value
        if remaining <= 0:
            break
    if total_qty == 0:
        return 0.0
    return spent / total_qty
