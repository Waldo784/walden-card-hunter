from wch.utils import normalize

BAD_WORDS = [
    "reprint", "custom", "digital", "proxy", "facsimile",
    "poster", "photo", "photograph", "jersey", "shirt",
    "t-shirt", "hoodie", "print", "art card", "sticker",
    "panini", "prizm", "mosaic", "select"
]


def is_junk(title: str) -> bool:
    title_norm = normalize(title)
    return any(bad in title_norm for bad in BAD_WORDS)
