from uuid import uuid4

from prediction_terminal.domain.errors import TerminalError


class Watchlists:
    def __init__(self, repo):
        self.repo = repo

    def save(self, id, name, match_ids):
        for match in match_ids:
            if not self.repo.get("match_groups", match):
                raise TerminalError("NOT_FOUND", "Watchlist match not found", 404)
        id = id or "wl_" + uuid4().hex
        row = {"id": id, "name": name, "match_ids": list(dict.fromkeys(match_ids))}
        self.repo.put("watchlists", id, row)
        for old in self.repo.list("watchlist_items", 10000):
            if old["watchlist_id"] == id:
                self.repo.delete("watchlist_items", old["id"])
        for match in row["match_ids"]:
            key = id + "_" + match
            self.repo.put(
                "watchlist_items",
                key,
                {"id": key, "watchlist_id": id, "match_id": match},
                watchlist_id=id,
                match_id=match,
            )
        return row
