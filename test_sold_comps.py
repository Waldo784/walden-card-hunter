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

    r = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers=headers,
        data=data,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def test_search(token, query):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
    }

    params = {
        "q": query,
        "limit": 10,
        "filter": "buyingOptions:{FIXED_PRICE}",
        "sort": "newlyListed",
    }

    r = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers=headers,
        params=params,
        timeout=30,
    )

    print("ACTIVE SEARCH STATUS:", r.status_code)
    print(r.text[:1000])


def main():
    token = get_ebay_token()
    query = "Scottie Pippen Soul of the Game"

    print("Testing active eBay Browse API...")
    test_search(token, query)

    print("\nNOTE:")
    print("If this works, active search is available.")
    print("Next we test whether sold/completed endpoints are available through your account.")


if __name__ == "__main__":
    main()
