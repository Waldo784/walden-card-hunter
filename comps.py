from pathlib import Path
from settings import COMPS_FILE, DEFAULT_MAX_PRICE
from wch.utils import load_csv


def load_comps() -> dict[str, dict]:
    comps: dict[str, dict] = {}
    if not Path(COMPS_FILE).exists():
        return comps
    for row in load_csv(COMPS_FILE):
        card_key = (row.get("card_key") or "").strip()
        if not card_key:
            continue
        comps[card_key] = {
            "market_value": float(row["market_value"]),
            "max_bid": float(row["max_bid"]),
            "source": (row.get("source") or "").strip(),
            "last_checked": (row.get("last_checked") or "").strip(),
            "notes": (row.get("notes") or "").strip(),
        }
    return comps


def default_comp(max_price: float = DEFAULT_MAX_PRICE) -> dict:
    return {
        "market_value": max_price,
        "max_bid": max_price * 0.65,
        "source": "default",
        "last_checked": "",
        "notes": "No verified comp yet — check sold comps manually before buying.",
    }
