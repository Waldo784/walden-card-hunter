import csv
import json
import os
import base64
import requests
from pathlib import Path

WATCHLIST_FILE = "watchlist.csv"
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


def load_watchlist():
    with open(WATCHLIST_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


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


def normalize(text):
    return " ".join(text.lower().split())


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
    return (
        f"🔥 WALDEN CARD HUNTER\n\n"
        f"Query: {hit['query']}\n"
        f"Title: {hit['title']}\n\n"
        f"Price: ${hit['price']:.2f}\n"
        f"Max Watch Price: ${hit['max_price']:.2f}\n"
        f"Priority: {hit['priority']}/5\n"
        f"Buying Option: {hit['buying_option']}\n\n"
        f"{hit['url']}"
    )


def main():
    watchlist = load_watchlist()
    seen = load_seen()
    new_seen = set(seen)

    token = get_ebay_token()
    hits = []

    for row in watchlist:
        query = row["query"].strip()
        max_price = float(row["max_price"])
        priority = int(row["priority"])

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

            url = item.get("itemWebUrl", "")
            buying_options = item.get("buyingOptions", [])
            buying_option = ", ".join(buying_options)

            hits.append({
                "key": key,
                "query": query,
                "title": title,
                "price": price,
                "max_price": max_price,
                "priority": priority,
                "buying_option": buying_option,
                "url": url,
            })

            new_seen.add(key)

    hits.sort(key=lambda h: (h["priority"], -h["price"]), reverse=True)

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
