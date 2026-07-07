import csv
import json
import os
import base64
import requests
from pathlib import Path

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
    "reprint", "custom", "digital", "proxy", "facsimile",
    "poster", "photo", "photograph", "jersey", "shirt",
    "t-shirt", "hoodie", "print", "art card", "sticker",
    "panini", "prizm", "mosaic", "select"
]


def normalize(text):
    return " ".join(str(text).lower().split())


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_watchlist():
    return load_csv(WATCHLIST_FILE)


def load_comps():
    comps = {}
    if not Path(COMPS_FILE).exists():
        return comps

    for row in load_csv(COMPS_FILE):
        query = row["query"].strip()
        comps[query] = {
            "market_value": float(row["market_value"]),
            "max_bid": float(row["max_bid"]),
            "notes": row.get("notes", "").strip(),
        }
    return comps


def load_seen():
    path = Path(SEEN_FILE)
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return set()


def save_seen(seen):
    Path(SEEN_FILE).write_text(
        json.dumps(sorted(seen), indent=2),
        encoding="utf-8"
    )


def is_junk(title):
    title = normalize(title)
    return any(bad in title for bad in BAD_WORDS)


def get_ebay_token():
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


def search_ebay(token, query):
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


def price_of(item):
    data = item.get("currentBidPrice") or item.get("price")
    if not data:
        return None
    try:
        return float(data["value"])
    except Exception:
        return None


def item_key(item):
    return item.get("itemId") or item.get("legacyItemId") or item.get("itemWebUrl")


def buying_option(item):
    options = item.get("buyingOptions", [])
    return ", ".join(options) if options else "Unknown"


def discount_percent(price, market_value):
    if market_value <= 0:
        return 0
    return max(0, (market_value - price) / market_value)


def walden_score(price, market_value, max_bid, priority):
    if market_value <= 0:
        return 50

    discount = discount_percent(price, market_value)

    score = 50
    score += discount * 40

    if price <= max_bid:
        score += 10
    else:
        over = (price - max_bid) / max_bid if max_bid else 1
        score -= min(20, over * 20)

    score += (priority - 3) * 3

    return max(0, min(100, round(score)))


def recommendation(score, price, max_bid):
    if score >= 90 and price <= max_bid:
        return "🔥 STRONG BUY"
    if score >= 80 and price <= max_bid:
        return "✅ BUY / WATCH CLOSELY"
    if score >= 70:
        return "👀 WATCHLIST"
    return "⚠️ PASS UNLESS PHOTOS ARE EXCELLENT"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True,
    }

    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()


def build_alert(hit):
    discount = discount_percent(hit["price"], hit["market_value"])
    score = hit["walden_score"]
    rec = recommendation(score, hit["price"], hit["max_bid"])

    return (
        f"🔥 WALDEN CARD HUNTER\n\n"
        f"{rec}\n"
        f"Walden Score: {score}/100\n\n"
        f"Query: {hit['query']}\n"
        f"Title: {hit['title']}\n\n"
        f"Current Price: ${hit['price']:.2f}\n"
        f"Estimated Market Value: ${hit['market_value']:.2f}\n"
        f"Discount: {discount:.0%} under market\n"
        f"Suggested Max Bid: ${hit['max_bid']:.2f}\n"
        f"Buying Option: {hit['buying_option']}\n"
        f"Priority: {hit['priority']}/5\n\n"
        f"Comp Notes: {hit['notes']}\n\n"
        f"{hit['url']}"
    )


def main():
    watchlist = load_watchlist()
    comps = load_comps()
    seen = load_seen()
    new_seen = set(seen)

    token = get_ebay_token()
    hits = []

    for row in watchlist:
        query = row["query"].strip()
        priority = int(row.get("priority", 3))
        max_price = float(row.get("max_price", 999999))

    comp = comps.get(query)

    if not comp:
    print(f"No comp found for query: {query} — using default estimate")
    comp = {
        "market_value": max_price,
        "max_bid": max_price * 0.65,
        "notes": "No manual comp yet — verify sold comps before buying."
        }

        market_value = comp["market_value"]
        max_bid = comp["max_bid"]
        notes = comp["notes"]

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
            if price is None:
                continue

            if price > max_price:
                continue

            score = walden_score(price, market_value, max_bid, priority)

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
            })

            new_seen.add(key)

    hits.sort(key=lambda h: h["walden_score"], reverse=True)

    if not hits:
        send_telegram("Walden Card Hunter ran — no matching deals found.")
        save_seen(new_seen)
        return

    sent = 0
    for hit in hits[:MAX_ALERTS_PER_RUN]:
        send_telegram(build_alert(hit))
        sent += 1

    save_seen(new_seen)
    print(f"Sent {sent} alerts.")


if __name__ == "__main__":
    main()
