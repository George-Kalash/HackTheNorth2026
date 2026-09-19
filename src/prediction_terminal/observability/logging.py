import json
import logging


def event(name, **fields):
    logging.getLogger("terminal").info(
        json.dumps(
            {
                "event": name,
                **{
                    k: v
                    for k, v in fields.items()
                    if k not in {"headers", "credentials", "secret", "private_key"}
                },
            },
            default=str,
        )
    )
