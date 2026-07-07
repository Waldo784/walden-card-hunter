from settings import WATCHLIST_FILE, SEEN_FILE, MAX_ALERTS_PER_RUN, MIN_WALDEN_SCORE
from wch.utils import load_csv, load_seen, save_seen
from wch.comps import load_comps, default_comp
from wch import ebay_api
from wch.filters import is_junk
from wch.scoring import walden_score
from wch.telegram import send, build_alert


def main() -> None:
    watchlist = load_csv(WATCHLIST_FILE)
    comps = load_comps()
    seen = load_seen(SEEN_FILE)
    new_seen = set(seen)
    token = ebay_api.get_token()
    grouped_hits: dict[str, dict] = {}

    for row in watchlist:
        card_key = (row.get("card_key") or "").strip()
        query = (row.get("query") or "").strip()
        priority = int(row.get("priority") or 3)
        max_price = float(row.get("max_price") or 999999)
        comp = comps.get(card_key) or default_comp(max_price)

        print(f"Searching: {query}")
        try:
            items = ebay_api.search(token, query)
        except Exception as e:
            print(f"Search failed for {query}: {e}")
            continue

        for item in items:
            key = ebay_api.item_id(item)
            if not key or key in seen:
                continue
            title = item.get("title", "")
            if not title or is_junk(title):
                continue
            price = ebay_api.price(item)
            if price is None or price > max_price:
                continue

            score = walden_score(price, comp["market_value"], comp["max_bid"], priority)
            match_info = {"card_key": card_key, "query": query, "priority": priority, "walden_score": score}

            if key not in grouped_hits:
                grouped_hits[key] = {
                    "key": key,
                    "title": title,
                    "price": price,
                    "buying_option": ebay_api.buying_option(item),
                    "url": item.get("itemWebUrl", ""),
                    "matches": [match_info],
                    "card_key": card_key,
                    "market_value": comp["market_value"],
                    "max_bid": comp["max_bid"],
                    "source": comp["source"],
                    "last_checked": comp["last_checked"],
                    "notes": comp["notes"],
                    "priority": priority,
                    "walden_score": score,
                }
            else:
                grouped_hits[key]["matches"].append(match_info)
                if score > grouped_hits[key]["walden_score"]:
                    grouped_hits[key].update({
                        "card_key": card_key,
                        "market_value": comp["market_value"],
                        "max_bid": comp["max_bid"],
                        "source": comp["source"],
                        "last_checked": comp["last_checked"],
                        "notes": comp["notes"],
                        "priority": priority,
                        "walden_score": score,
                    })
            new_seen.add(key)

    hits = [h for h in grouped_hits.values() if h["walden_score"] >= MIN_WALDEN_SCORE]
    hits.sort(key=lambda h: h["walden_score"], reverse=True)

    if not hits:
        send(f"Walden Card Hunter ran — no listings at/above score {MIN_WALDEN_SCORE}.")
        save_seen(SEEN_FILE, new_seen)
        return

    sent = 0
    for hit in hits[:MAX_ALERTS_PER_RUN]:
        send(build_alert(hit))
        sent += 1

    save_seen(SEEN_FILE, new_seen)
    print(f"Sent {sent} grouped alerts.")


if __name__ == "__main__":
    main()
