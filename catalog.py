from settings import CATALOG_FILE, WATCHLIST_FILE, DEFAULT_MAX_PRICE
from wch.utils import load_csv, safe_text, write_csv


def load_catalog() -> list[dict]:
    return load_csv(CATALOG_FILE)


def generate_watchlist() -> int:
    catalog = load_catalog()
    rows: list[dict] = []
    seen_queries: set[tuple[str, str]] = set()

    for card in catalog:
        card_key = safe_text(card.get("card_key"))
        year = safe_text(card.get("year"))
        brand = safe_text(card.get("brand"))
        insert_set = safe_text(card.get("insert_set"))
        player = safe_text(card.get("player"))
        priority = safe_text(card.get("priority")) or "5"
        aliases = safe_text(card.get("aliases"))
        alias_terms = [a.strip() for a in aliases.split(";") if a.strip()]

        queries = [
            f"{player} {brand} {insert_set}",
            f"{player} {year} {insert_set}",
            f"{player} {insert_set}",
        ]
        queries += [f"{player} {alias}" for alias in alias_terms]

        for query in queries:
            query = " ".join(query.split())
            key = (card_key, query.lower())
            if not query or key in seen_queries:
                continue
            rows.append({
                "card_key": card_key,
                "query": query,
                "max_price": str(int(DEFAULT_MAX_PRICE)),
                "priority": priority,
            })
            seen_queries.add(key)

    write_csv(WATCHLIST_FILE, rows, ["card_key", "query", "max_price", "priority"])
    return len(rows)
