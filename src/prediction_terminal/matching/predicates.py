import re
from hashlib import sha256

from prediction_terminal.domain.markets import SettlementSpec


def settlement(text: str, currency: str = "USD") -> SettlementSpec:
    lower = text.lower()
    return SettlementSpec(
        rule_text=text,
        rule_hash=sha256(text.encode()).hexdigest(),
        currency=currency,
        variable="upper bound of target federal funds range"
        if "upper bound" in lower and "federal funds" in lower
        else None,
        authority="FOMC" if "fomc" in lower or "federal open market committee" in lower else None,
        baseline="before scheduled meeting" if "prior to" in lower and "meeting" in lower else None,
    )


def bucket(text: str) -> str | None:
    text = text.lower()
    if "fed" not in text and "federal reserve" not in text:
        return None
    if any(s in text for s in ["maintains", "no change"]) or re.search(r"(?<!\d)0\s*bps", text):
        return "hold"
    direction = (
        "cut" if re.search("cut|decrease", text) else "hike" if re.search("hike|increase", text) else None
    )
    if direction and re.search(r">\s*25|50\s*\+", text):
        return direction + "_large"
    if direction and re.search(r"(?<!\d)25\s*bps", text):
        return direction + "_25"
    return None
