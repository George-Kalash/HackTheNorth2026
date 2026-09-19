import re
from difflib import SequenceMatcher

from prediction_terminal.domain.markets import VenueMarket, stable_id
from prediction_terminal.domain.matches import MatchGroup, MatchLeg

from .equivalence import compare_rules
from .predicates import bucket


def similarity(left: str, right: str) -> float:
    def words(text):
        text = text.lower().replace("federal reserve", "fed")
        text = re.sub(r"\boct\b", "october", text)
        return set(re.findall(r"\w+", text)) - {
            "will",
            "the",
            "in",
            "a",
            "their",
            "at",
            "meeting",
            "by",
            "of",
            "after",
        }

    a, b = words(left), words(right)
    return (
        0.8 * len(a & b) / max(1, len(a))
        + 0.2 * SequenceMatcher(None, " ".join(sorted(a)), " ".join(sorted(b))).ratio()
    )


def propose(a: VenueMarket, b: VenueMarket) -> MatchGroup | None:
    if a.venue == b.venue:
        return None
    ab, bb = bucket(a.title + " " + a.outcome), bucket(b.title + " " + b.outcome)
    if ab and bb and ab != bb:
        return None
    score = max(similarity(a.title, b.title), 0.85 if ab and ab == bb else 0)
    if score < 0.3:
        return None
    classification, differences = compare_rules(a, b)
    if a.close_time and b.close_time and abs((a.close_time - b.close_time).total_seconds()) > 172800:
        score *= 0.4
    return MatchGroup(
        id=stable_id("match", *sorted([a.id, b.id])),
        title=a.outcome + " ↔ " + b.outcome,
        market_ids=[a.id, b.id],
        score=score,
        classification=classification,
        reasons=[
            "Candidate based on event wording, outcome bucket and dates; score is not profit probability."
        ],
        differences=differences,
        rule_hashes={a.id: a.settlement.rule_hash, b.id: b.settlement.rule_hash},
        legs=[MatchLeg(market_id=a.id), MatchLeg(market_id=b.id)],
    )
