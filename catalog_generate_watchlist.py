import csv

CATALOG_FILE = "card_catalog.csv"
OUTPUT_FILE = "watchlist.csv"


def safe_text(value):
    if value is None:
        return ""
    return str(value).strip()


def load_catalog():
    with open(CATALOG_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    catalog = load_catalog()
    rows = []

    for card in catalog:
        year = safe_text(card.get("year"))
        brand = safe_text(card.get("brand"))
        insert_set = safe_text(card.get("insert_set"))
        player = safe_text(card.get("player"))
        priority = safe_text(card.get("priority")) or "5"
        aliases = safe_text(card.get("aliases"))

        alias_terms = [a.strip() for a in aliases.split(";") if a.strip()]

        base_queries = [
            f"{player} {brand} {insert_set}",
            f"{player} {year} {insert_set}",
            f"{player} {insert_set}",
        ]

        for alias in alias_terms:
            base_queries.append(f"{player} {alias}")

        for query in base_queries:
            rows.append({
                "query": query,
                "max_price": 2500,
                "priority": priority,
            })

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["query", "max_price", "priority"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} catalog-based searches in {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
