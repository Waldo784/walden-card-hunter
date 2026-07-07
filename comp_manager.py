import csv
from pathlib import Path

CATALOG_FILE = "card_catalog.csv"
COMPS_FILE = "comps_by_card.csv"
REPORT_FILE = "missing_comps_report.csv"


def load_csv(path):
    if not Path(path).exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    catalog = load_csv(CATALOG_FILE)
    comps = load_csv(COMPS_FILE)

    comp_keys = {row["card_key"].strip() for row in comps if row.get("card_key")}

    missing = []

    for card in catalog:
        card_key = card.get("card_key", "").strip()
        if not card_key:
            continue

        if card_key not in comp_keys:
            missing.append(card)

    with open(REPORT_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "card_key",
            "year",
            "brand",
            "insert_set",
            "player",
            "card_number",
            "serial_number",
            "priority",
            "aliases",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(missing)

    print(f"Catalog cards: {len(catalog)}")
    print(f"Comp rows: {len(comps)}")
    print(f"Missing comps: {len(missing)}")
    print(f"Wrote report: {REPORT_FILE}")


if __name__ == "__main__":
    main()
