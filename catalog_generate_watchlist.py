from wch.catalog import generate_watchlist

if __name__ == "__main__":
    count = generate_watchlist()
    print(f"Generated {count} catalog-based searches in watchlist.csv")
