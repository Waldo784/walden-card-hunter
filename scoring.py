
def discount_percent(price: float, market_value: float) -> float:
    if market_value <= 0:
        return 0.0
    return max(0.0, (market_value - price) / market_value)


def walden_score(price: float, market_value: float, max_bid: float, priority: int) -> int:
    if market_value <= 0:
        return 50
    discount = discount_percent(price, market_value)
    score = 50 + discount * 40
    if price <= max_bid:
        score += 10
    else:
        over = (price - max_bid) / max_bid if max_bid else 1
        score -= min(20, over * 20)
    score += (priority - 3) * 3
    return max(0, min(100, round(score)))


def recommendation(score: int, price: float, max_bid: float) -> str:
    if score >= 90 and price <= max_bid:
        return "🔥 STRONG BUY"
    if score >= 80 and price <= max_bid:
        return "✅ BUY / WATCH CLOSELY"
    if score >= 70:
        return "👀 WATCHLIST"
    return "⚠️ PASS UNLESS PHOTOS ARE EXCELLENT"
