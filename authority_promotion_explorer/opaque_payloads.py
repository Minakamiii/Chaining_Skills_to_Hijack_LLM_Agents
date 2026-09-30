from __future__ import annotations

import base64
import gzip

OPAQUE_PACKAGING_PLAIN = "plain"
OPAQUE_PACKAGING_GZIP_BASE64 = "gzip-base64"
OPAQUE_PACKAGING_XOR_FIXED_KEY = "xor-fixed-key"
_FIXED_XOR_KEY = b"agent-sec-lab-fixed-key-v1"

SUPPORTED_OPAQUE_PACKAGING = {
    OPAQUE_PACKAGING_PLAIN,
    OPAQUE_PACKAGING_GZIP_BASE64,
    OPAQUE_PACKAGING_XOR_FIXED_KEY,
}


def _xor_bytes(payload: bytes, key: bytes) -> bytes:
    if not key:
        raise ValueError("xor key must not be empty")
    return bytes(byte ^ key[index % len(key)] for index, byte in enumerate(payload))


def normalize_opaque_packaging(packaging: str) -> str:
    normalized = packaging.strip().lower()
    if normalized not in SUPPORTED_OPAQUE_PACKAGING:
        supported = ", ".join(sorted(SUPPORTED_OPAQUE_PACKAGING))
        raise ValueError(f"Unsupported opaque packaging mode: {packaging!r}. Expected one of: {supported}")
    return normalized


def encode_opaque_payload(text: str, packaging: str) -> str:
    normalized = normalize_opaque_packaging(packaging)
    raw = text.encode("utf-8")
    if normalized == OPAQUE_PACKAGING_PLAIN:
        return text
    if normalized == OPAQUE_PACKAGING_GZIP_BASE64:
        return base64.b64encode(gzip.compress(raw)).decode("ascii")
    if normalized == OPAQUE_PACKAGING_XOR_FIXED_KEY:
        wrapped = _xor_bytes(raw, _FIXED_XOR_KEY)
        return base64.b64encode(wrapped).decode("ascii")
    raise AssertionError(f"Unhandled opaque packaging mode: {normalized}")


def decode_opaque_payload(payload: str, packaging: str) -> str:
    normalized = normalize_opaque_packaging(packaging)
    if normalized == OPAQUE_PACKAGING_PLAIN:
        return payload
    encoded = payload.encode("ascii")
    if normalized == OPAQUE_PACKAGING_GZIP_BASE64:
        return gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
    if normalized == OPAQUE_PACKAGING_XOR_FIXED_KEY:
        wrapped = base64.b64decode(encoded)
        return _xor_bytes(wrapped, _FIXED_XOR_KEY).decode("utf-8")
    raise AssertionError(f"Unhandled opaque packaging mode: {normalized}")
