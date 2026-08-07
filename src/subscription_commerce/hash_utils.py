import hashlib


def stable_unit_interval(*parts: object) -> float:
    """Return a deterministic pseudo-random value in [0, 1)."""
    payload = "|".join("" if p is None else str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    integer = int.from_bytes(digest[:8], "big", signed=False)
    return integer / 2**64
