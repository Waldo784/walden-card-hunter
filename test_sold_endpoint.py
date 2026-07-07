import requests
from wch.ebay_api import get_token

if __name__ == "__main__":
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
    }
    url = "https://api.ebay.com/buy/marketplace_insights/v1_beta/item_sales/search"
    r = requests.get(url, headers=headers, params={"q": "Scottie Pippen Soul of the Game", "limit": 10}, timeout=30)
    print("SOLD SEARCH STATUS:", r.status_code)
    print(r.text[:3000])
