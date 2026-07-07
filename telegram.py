import os
import requests
from wch.scoring import discount_percent, recommendation


def send(message: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "disable_web_page_preview": True}
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()


def build_alert(hit: dict) -> str:
    discount = discount_percent(hit["price"], hit["market_value"])
    score = hit["walden_score"]
    rec = recommendation(score, hit["price"], hit["max_bid"])
    matched_lines = [f"- {m['card_key']} | {m['query']}" for m in hit["matches"]]
    matched_text = "\n".join(matched_lines[:10])
    if len(matched_lines) > 10:
        matched_text += f"\n...and {len(matched_lines) - 10} more matches"
    return (
        "🔥 WALDEN CARD HUNTER\n\n"
        f"{rec}\n"
        f"Walden Score: {score}/100\n"
        f"Matched Searches: {len(hit['matches'])}\n\n"
        f"Title: {hit['title']}\n\n"
        f"Current Price: ${hit['price']:.2f}\n"
        f"Estimated Market Value: ${hit['market_value']:.2f}\n"
        f"Discount: {discount:.0%} under market\n"
        f"Suggested Max Bid: ${hit['max_bid']:.2f}\n"
        f"Buying Option: {hit['buying_option']}\n"
        f"Priority: {hit['priority']}/5\n\n"
        f"Best Card Key: {hit['card_key']}\n"
        f"Comp Source: {hit['source']}\n"
        f"Last Checked: {hit['last_checked']}\n"
        f"Comp Notes: {hit['notes']}\n\n"
        f"Matched:\n{matched_text}\n\n"
        f"{hit['url']}"
    )
