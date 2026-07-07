import base64
import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests

WATCHLIST_FILE = "watchlist.csv"
COMPS_FILE = "comps_cache.csv"
SEEN_FILE = "seen_items.json"

RESULTS_PER_QUERY = 20
MAX_ALERTS_PER_RUN = 15

EBAY_CLIENT_ID = os.environ["EBAY_CLIENT_ID"]
EBAY_CLIENT_SECRET = os.environ["EBAY_CLIENT_SECRET"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

BAD_WORDS = [
    "reprint", "custom", "digital", "proxy", "facsimile", "poster",
    "photograph", "jersey", "shirt", "t-shirt", "hoodie", "art card",
    "sticker", "panini", "prizm", "mosaic", "select", "funko",
]


def normalize(text: str) -> str:
    return " ".join(str(text).lower().split())


def load_csv(path: str) -> List[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_watchlist() -> List[dict]:
    return load_csv(WATCHLIST_FILE)


def load_comps() -> Dict[str, dict]:
    if not Path(COMPS_FILE).exists():
        return {}
    comps: Dict[str, dict] = {}
    for row in load_csv(COMPS_FILE):
        query = row.get("query", "").strip()
        if not query:
            continue
        try:
            comps[query] = {
                "market_value": float(row.get("market_value", 0) or 0),
                "max_bid": float(row.get("max_bid", 0) or 0),
                "notes": row.get("notes", "").strip(),
            }
        except ValueError:
            print(f"Skipping invalid comp row for query: {query}")
    return comps


def load_seen() -> Set[str]:
    path = Path(SEEN_FILE)
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return set()


def save_seen(seen: Set[str]) -> None:
    Path(SEEN_FILE).write_text(json.dumps(sorted(seen), indent=2), encoding="utf-8")


def is_junk(title: str) -> bool:
    title_norm = normalize(title)
    return any(bad in title_norm for bad in BAD_WORDS)


def get_ebay_token() -> str:
    creds = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}".encode("utf-8")
    headers = {
        "Authorization": "Basic " + base64.b64encode(creds).decode("utf-8"),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }
    r = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers=headers,
        data=data,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def search_ebay(token: str, query: str) -> List[dict]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
    }
    params = {
        "q": query,
        "limit": RESULTS_PER_QUERY,
        "sort": "newlyListed",
        "filter": "buyingOptions:{AUCTION|FIXED_PRICE}",
    }
    r = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers=headers,
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("itemSummaries", [])


def price_of(item: dict) -> Optional[float]:
    data = item.get("currentBidPrice") or item.get("price")
    if not data:
        return None
    try:
        return float(data.get("value", 0))
    except Exception:
        return None


def item_key(item: dict) -> str:
    return item.get("itemId") or item.get("legacyItemId") or item.get("itemWebUrl", "")


def buying_option(item: dict) -> str:
    options = item.get("buyingOptions", [])
    return ", ".join(options) if options else "Unknown"


def discount_percent(price: float, market_value: float) -> float:
    if market_value <= 0:
        return 0.0
    return max(0.0, (market_value - price) / market_value)


def walden_score(price: float, market_value: float, max_bid: float, priority: int, has_manual_comp: bool) -> int:
    if market_value <= 0:
        return 50

    discount = discount_percent(price, market_value)
    score = 45 + (discount * 40)

    if price <= max_bid:
        score += 12
    else:
        over = (price - max_bid) / max(max_bid, 1)
        score -= min(20, over * 20)

    score += (priority - 3) * 3

    if not has_manual_comp:
        score -= 8

    return int(max(0, min(100, round(score))))


def recommendation(score: int, price: float, max_bid: float, has_manual_comp: bool) -> str:
    prefix = "⚠️ COMP NEEDED | " if not has_manual_comp else ""
    if score >= 90 and price <= max_bid:
        return prefix + "🔥 STRONG BUY"
    if score >= 80 and price <= max_bid:
        return prefix + "✅ BUY / WATCH CLOSELY"
    if score >= 70:
        return prefix + "👀 WATCHLIST"
    return prefix + "⚠️ PASS UNLESS PHOTOS ARE EXCELLENT"


def send_telegram(message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True,
    }
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()


def build_alert(hit: dict) -> str:
    discount = discount_percent(hit["price"], hit["market_value"])
    rec = recommendation(hit["walden_score"], hit["price"], hit["max_bid"], hit["has_manual_comp"])
    comp_label = "Manual comp" if hit["has_manual_comp"] else "Default estimate"
    return (
        "🔥 WALDEN CARD HUNTER\n\n"
        f"{rec}\n"
        f"Walden Score: {hit['walden_score']}/100\n\n"
        f"Query: {hit['query']}\n"
        f"Title: {hit['title']}\n\n"
        f"Current Price: ${hit['price']:.2f}\n"
        f"Estimated Market Value: ${hit['market_value']:.2f}\n"
        f"Discount: {discount:.0%} under market\n"
        f"Suggested Max Bid: ${hit['max_bid']:.2f}\n"
        f"Buying Option: {hit['buying_option']}\n"
        f"Priority: {hit['priority']}/5\n"
        f"Comp Source: {comp_label}\n\n"
        f"Comp Notes: {hit['notes']}\n\n"
        f"{hit['url']}"
    )


def comp_for_query(query: str, comps: Dict[str, dict], max_price: float) -> tuple[dict, bool]:
    comp = comps.get(query)
    if comp:
        return comp, True
    print(f"No comp found for query: {query} — using default estimate")
    return {
        "market_value": max_price,
        "max_bid": max_price * 0.65,
        "notes": "No manual comp yet — verify sold comps before buying.",
    }, False


def main() -> None:
    watchlist = load_watchlist()
    comps = load_comps()
    seen = load_seen()
    new_seen = set(seen)
    token = get_ebay_token()
    hits: List[dict] = []

    for row in watchlist:
        query = row.get("query", "").strip()
        if not query:
            continue
        priority = int(row.get("priority", 3) or 3)
        max_price = float(row.get("max_price", 999999) or 999999)
        comp, has_manual_comp = comp_for_query(query, comps, max_price)

        market_value = float(comp["market_value"])
        max_bid = float(comp["max_bid"])
        notes = str(comp.get("notes", ""))

        print(f"Searching: {query}")
        try:
            items = search_ebay(token, query)
        except Exception as e:
            print(f"Search failed for {query}: {e}")
            continue

        for item in items:
            key = item_key(item)
            if not key or key in seen:
                continue

            title = item.get("title", "")
            if not title or is_junk(title):
                continue

            price = price_of(item)
            if price is None or price > max_price:
                continue

            score = walden_score(price, market_value, max_bid, priority, has_manual_comp)
            hits.append({
                "key": key,
                "query": query,
                "title": title,
                "price": price,
                "market_value": market_value,
                "max_bid": max_bid,
                "notes": notes,
                "priority": priority,
                "buying_option": buying_option(item),
                "url": item.get("itemWebUrl", ""),
                "walden_score": score,
                "has_manual_comp": has_manual_comp,
            })
            new_seen.add(key)

    hits.sort(key=lambda h: (h["walden_score"], h["priority"]), reverse=True)

    if not hits:
        send_telegram("Walden Card Hunter ran — no matching deals found.")
        save_seen(new_seen)
        print("No matching deals found.")
        return

    sent = 0
    for hit in hits[:MAX_ALERTS_PER_RUN]:
        send_telegram(build_alert(hit))
        sent += 1

    save_seen(new_seen)
    print(f"Sent {sent} alerts.")


if __name__ == "__main__":
    main()
