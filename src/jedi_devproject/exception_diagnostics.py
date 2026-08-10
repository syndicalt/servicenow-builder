from __future__ import annotations

MAX_EXCEPTION_TYPE_LABEL_CHARS = 128


def exception_diagnostic_message(
    error: BaseException,
    *,
    fallback_subject: str,
) -> str:
    try:
        return str(error)
    except Exception:
        subject = _safe_fallback_subject(fallback_subject)
        exception_type = _safe_exception_type_label(error)
        if exception_type is None:
            return f"{subject} raised unstringifiable exception"
        return f"{subject} raised unstringifiable {exception_type}"


def _safe_exception_type_label(error: BaseException) -> str | None:
    label = type(error).__name__
    if (
        not label.isascii()
        or not label.isidentifier()
        or len(label) > MAX_EXCEPTION_TYPE_LABEL_CHARS
    ):
        return None
    return label


def _safe_fallback_subject(subject: str) -> str:
    if not subject.isascii() or subject != subject.strip() or len(subject) > 64:
        return "error"
    parts = subject.split(" ")
    if not parts or any(not part.isidentifier() for part in parts):
        return "error"
    return subject
