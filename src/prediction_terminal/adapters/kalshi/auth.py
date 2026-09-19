"""Market-data handshake signing only; never exported to the browser."""

import base64
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def market_data_headers(key_id: str, key_path: str):
    if not key_id or not key_path:
        return None
    key = serialization.load_pem_private_key(Path(key_path).read_bytes(), password=None)
    if not isinstance(key, rsa.RSAPrivateKey):
        raise ValueError("Kalshi market-data signing requires an RSA private key")
    stamp = str(int(time.time() * 1000))
    signature = key.sign(
        (stamp + "GET/trade-api/ws/v2").encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )
    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-TIMESTAMP": stamp,
        "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode(),
    }
