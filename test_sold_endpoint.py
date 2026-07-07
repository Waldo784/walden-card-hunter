import base64
import os
import requests

EBAY_CLIENT_ID = os.environ["EBAY_CLIENT_ID"]
EBAY_CLIENT_SECRET = os.environ["EBAY_CLIENT_SECRET"]

def get_ebay_token():
    creds = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}".encode("utf-8")
    headers = {
        "Authorization": "Basic " + base64.b64encode(creds).decode("utf-8"),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }
    r = requests.post("https://api.ebay.com/identity/v1/oauth2/token", headers=headers, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def main():
    token = get_ebay_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
    }

    url = "https://api.ebay.com/buy/marketplace_insights/v1_beta/item_sales/search"
    params = {
        "q": "Scottie Pippen Soul of the Game",
        "limit": 10,
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)

    print("SOLD SEARCH STATUS:", r.status_code)
    print(r.text[:3000])

if __name__ == "__main__":
    main()
