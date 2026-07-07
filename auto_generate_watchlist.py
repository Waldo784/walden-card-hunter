import csv

PLAYERS_FILE = "players.csv"
SETS_FILE = "insert_sets.csv"
OUTPUT_FILE = "watchlist.csv"


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    players = load_csv(PLAYERS_FILE)
    insert_sets = load_csv(SETS_FILE)

    rows = []

    for player in players:
        player_name = player["player"].strip()
        player_priority = int(player["priority"])

        for insert_set in insert_sets:
            set_name = insert_set["set_name"].strip()
            set_priority = int(insert_set["priority"])
            max_price = float(insert_set["max_price"])

            priority = max(player_priority, set_priority)

            rows.append({
                "query": f"{player_name} {set_name}",
                "max_price": int(max_price),
                "priority": priority,
            })

    extra_queries = [
        {"query": "1990s basketball insert lot", "max_price": 500, "priority": 4},
        {"query": "90s basketball insert lot", "max_price": 500, "priority": 4},
        {"query": "rare basketball insert lot", "max_price": 750, "priority": 4},
        {"query": "SkyBox basketball insert lot", "max_price": 500, "priority": 4},
        {"query": "Fleer basketball insert lot", "max_price": 500, "priority": 3},
    ]

    rows.extend(extra_queries)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["query", "max_price", "priority"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} watchlist searches in {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
