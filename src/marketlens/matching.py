"""Candidate ranking only: text similarity never establishes settlement equivalence."""

import re
from datetime import datetime
from difflib import SequenceMatcher

STOP = {
    "will",
    "the",
    "a",
    "an",
    "in",
    "at",
    "on",
    "by",
    "of",
    "be",
    "their",
    "after",
    "meeting",
    "2026",
    "2027",
}


def words(text):
    text = text.lower().replace("federal reserve", "fed")
    text = re.sub(r"\boct\b", "october", text)
    return set(re.findall(r"[a-z0-9]+", text)) - STOP


def similarity(a, b):
    left, right = words(a), words(b)
    overlap = len(left & right) / max(1, len(left))
    return (
        0.8 * overlap
        + 0.2 * SequenceMatcher(None, " ".join(sorted(left)), " ".join(sorted(right))).ratio()
    )


def fed_bucket(market):
    text = (market.outcome + " " + market.title).lower()
    if "fed" not in text and "federal reserve" not in text:
        return None
    if any(x in text for x in ["no change", "maintains", "0bps", "0 bps"]):
        # Don't accidentally classify 50bps as 0bps.
        if re.search(r"(?<!\d)0\s*bps", text) or "no change" in text or "maintains" in text:
            return "hold"
    direction = (
        "cut"
        if re.search(r"cut|decrease", text)
        else "hike"
        if re.search(r"hike|increase", text)
        else None
    )
    if not direction:
        return None
    if re.search(r">\s*25|50\s*\+", text):
        return direction + "_large"
    if re.search(r"(?<!\d)25\s*bps", text):
        return direction + "_25"
    return None


def candidates(kalshi, polymarket):
    result = []
    for k in kalshi:
        for p in polymarket:
            kb, pb = fed_bucket(k), fed_bucket(p)
            if kb and pb and kb != pb:
                continue
            score = similarity(k.title, p.title)
            reason = "Related wording; verify event, date, direction and threshold."
            if kb and kb == pb:
                score = max(score, 0.85)
                reason = "Similar Fed outcome bucket; rounding and cancellation rules can differ."
            if score < 0.3:
                continue
            if k.close_time and p.close_time:
                difference = abs(
                    (
                        datetime.fromisoformat(k.close_time.replace("Z", "+00:00"))
                        - datetime.fromisoformat(p.close_time.replace("Z", "+00:00"))
                    ).total_seconds()
                )
                if difference > 2 * 86400:
                    score *= 0.45
                    reason += " Closing dates differ by more than two days."
            result.append(
                {
                    "kalshi_id": k.id,
                    "polymarket_id": p.id,
                    "score": round(score, 3),
                    "reason": reason,
                    "equivalence": "unverified",
                }
            )
    return sorted(result, key=lambda x: x["score"], reverse=True)[:40]
