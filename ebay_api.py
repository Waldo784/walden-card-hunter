import base64
import os
import requests
from settings import RESULTS_PER_QUERY


def get_token() -> str:
    client_id = os.environ["EBAY_CLIENT_ID"]
    client_secret = os.environ["EBAY_CLIENT_SECRET"]
    creds = f"{client_id}:{client_secret}".encode("utf-8")
    headers = {
        "Authorization": "Basic " + base64.b64encode(creds).decode("utf-8"),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
    r = requests.post("https://api.ebay.com/identity/v1/oauth2/token", headers=headers, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def search(token: str, query: str) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
    }
    params = {
        "q": query,
        "limit": RESULTS_PER_QUERY,
        "sort": "newlyListed",
        "filter": "buyingOptions:{AUCTION|FIXED_PRICE}",
    }
    r = requests.get("https://api.ebay.com/buy/browse/v1/item_summary/search", headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("itemSummaries", [])


def item_id(item: dict) -> str:
    return item.get("itemId") or item.get("legacyItemId") or item.get("itemWebUrl") or ""


def price(item: dict) -> float | None:
    data = item.get("currentBidPrice") or item.get("price")
    if not data:
        return None
    try:
        return float(data["value"])
    except Exception:
        return None


def buying_option(item: dict) -> str:
    options = item.get("buyingOptions", [])
    return ", ".join(options) if options else "Unknown"
