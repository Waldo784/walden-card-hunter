from wch import ebay_api

if __name__ == "__main__":
    token = ebay_api.get_token()
    print("Testing active eBay Browse API...")
    items = ebay_api.search(token, "Scottie Pippen Soul of the Game")
    print(f"ACTIVE SEARCH STATUS: OK")
    print(f"Returned items: {len(items)}")
    for item in items[:3]:
        print(item.get("title"), item.get("itemWebUrl"))
