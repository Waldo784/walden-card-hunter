import csv
import json
from pathlib import Path


def normalize(text: object) -> str:
    return " ".join(str(text).lower().split())


def safe_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def load_csv(path: str) -> list[dict]:
    if not Path(path).exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_seen(path: str) -> set[str]:
    p = Path(path)
    if not p.exists():
        return set()
    try:
        return set(json.loads(p.read_text(encoding="utf-8")))
    except Exception:
        return set()


def save_seen(path: str, seen: set[str]) -> None:
    Path(path).write_text(json.dumps(sorted(seen), indent=2), encoding="utf-8")
