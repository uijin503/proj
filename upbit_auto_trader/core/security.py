from __future__ import annotations

import base64
import os
from hashlib import scrypt

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def derive_key(password: str, salt: bytes) -> bytes:
    return scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)


def encrypt_secret(plain_text: str, password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or os.urandom(16)
    key = derive_key(password, salt)
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    ct = cipher.encrypt(nonce, plain_text.encode("utf-8"), None)
    payload = base64.b64encode(nonce + ct).decode("utf-8")
    return base64.b64encode(salt).decode("utf-8"), payload


def decrypt_secret(payload_b64: str, password: str, salt_b64: str) -> str:
    raw = base64.b64decode(payload_b64)
    salt = base64.b64decode(salt_b64)
    nonce, ct = raw[:12], raw[12:]
    key = derive_key(password, salt)
    plain = AESGCM(key).decrypt(nonce, ct, None)
    return plain.decode("utf-8")
