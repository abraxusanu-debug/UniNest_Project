import time

_attempts = {}
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60


def _key(email):
    return str(email or "").strip().lower()


def is_locked(email):
    key = _key(email)
    record = _attempts.get(key)
    if not record:
        return False
    if time.monotonic() >= record["locked_until"]:
        _attempts.pop(key, None)
        return False
    return record["count"] >= MAX_ATTEMPTS


def record_failure(email):
    key = _key(email)
    record = _attempts.setdefault(key, {"count": 0, "locked_until": 0})
    if time.monotonic() >= record["locked_until"]:
        record["count"] = 0
    record["count"] += 1
    if record["count"] >= MAX_ATTEMPTS:
        record["locked_until"] = time.monotonic() + LOCKOUT_SECONDS


def clear(email):
    _attempts.pop(_key(email), None)
