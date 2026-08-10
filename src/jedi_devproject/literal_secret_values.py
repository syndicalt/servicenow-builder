"""Safe projection for configured literal secret values."""

from __future__ import annotations

from collections.abc import Iterable

MAX_LITERAL_SECRETS = 100
MAX_LITERAL_SECRET_CHARS = 4096


def safe_literal_secret_values(secret_values: Iterable[str]) -> tuple[str, ...]:
    """Return a bounded exact-string tuple of literal secrets.

    Literal secret collections are often passed into diagnostic and work-note
    redaction paths after an error has already occurred. Treat the collection as
    untrusted so secondary iterator failures cannot replace the original
    diagnostic.
    """
    safe_values: set[str] = set()
    try:
        iterator = iter(secret_values)
    except Exception:
        return ()
    while len(safe_values) < MAX_LITERAL_SECRETS:
        try:
            secret = next(iterator)
        except StopIteration:
            break
        except Exception:
            return tuple(sorted(safe_values, key=len, reverse=True))
        # Empty string is an invalid sentinel, not a hardcoded secret.
        if type(secret) is not str or secret == "":  # nosec B105
            continue
        safe_values.add(secret[:MAX_LITERAL_SECRET_CHARS])
    return tuple(sorted(safe_values, key=len, reverse=True))
