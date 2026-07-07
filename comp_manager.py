from settings import CATALOG_FILE, COMPS_FILE
from wch.utils import load_csv, write_csv

REPORT_FILE = "missing_comps_report.csv"


def main() -> None:
    catalog = load_csv(CATALOG_FILE)
    comps = load_csv(COMPS_FILE)
    comp_keys = {row["card_key"].strip() for row in comps if row.get("card_key")}
    missing = [card for card in catalog if card.get("card_key", "").strip() not in comp_keys]
    fieldnames = ["card_key", "year", "brand", "insert_set", "player", "card_number", "serial_number", "priority", "aliases"]
    write_csv(REPORT_FILE, missing, fieldnames)
    print(f"Catalog cards: {len(catalog)}")
    print(f"Comp rows: {len(comps)}")
    print(f"Missing comps: {len(missing)}")
    print(f"Wrote report: {REPORT_FILE}")

if __name__ == "__main__":
    main()
