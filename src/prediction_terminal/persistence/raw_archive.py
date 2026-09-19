import json
from hashlib import sha256

from prediction_terminal.domain.markets import utcnow

SENSITIVE = {"authorization", "signature", "api_key", "secret", "private_key", "token", "password"}


def redact(value):
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if k.lower() in SENSITIVE else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


class RawArchive:
    def __init__(self, repo):
        self.repo = repo

    def record(self, source, data):
        clean = redact(data)
        digest = sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()
        self.repo.put(
            "raw_inputs",
            digest,
            {"id": digest, "source": source, "received_at": utcnow().isoformat(), "data": clean},
        )
        return digest
