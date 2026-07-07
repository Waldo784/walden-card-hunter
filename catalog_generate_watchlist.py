import csv

CATALOG_FILE = "card_catalog.csv"
OUTPUT_FILE = "watchlist.csv"


def load_catalog():
    with open(CATALOG_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    catalog = load_catalog()
    rows = []

    for card in catalog:
        year = card.get("year", "").strip()
        brand = card.get("brand", "").strip()
        insert_set = card.get("insert_set", "").strip()
        player = card.get("player", "").strip()
        priority = card.get("priority", "5").strip() or "5"

        aliases = card.get("aliases", "").strip()
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
