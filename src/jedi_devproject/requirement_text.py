from __future__ import annotations

import re

FORBIDDEN_BOUNDARY_PATTERNS = [
    r"\bacls?\b",
    r"\bapi\s+keys?\b",
    r"\basync\b",
    r"\bbrowser\s+storage\b",
    r"\bbusiness\s+rules?\b",
    r"\bclient\s+scripts?\b",
    r"\bcredentials?\b",
    r"\bcross-table\b",
    r"\bdata\s+migration\b",
    r"\bdeletes?\b",
    r"\bdisplay\b",
    r"\bdom\b",
    r"\bendpoints?\b",
    r"\bexternal\b",
    r"\bflows?\b",
    r"\bflow\s+designer\b",
    r"\bglideajax\b",
    r"\bgliderecord\b",
    r"\bglobals?\b",
    r"\bintegrations?\b",
    r"\bintegration\s+calls?\b",
    r"\bmigrations?\b",
    r"\boutbound\b",
    r"\bpasswords?\b",
    r"\brest\b",
    r"\bsecrets?\b",
    r"\bserver-side\s+scripts?\b",
    r"\bscript\s+includes?\b",
    r"\bsoap\b",
    r"\btokens?\b",
    r"http://",
    r"https://",
]

NEGATIVE_BOUNDARY_MARKER = re.compile(
    r"\bforbidden\s+behavior\s*:"
    r"|\b(?:do|does|must|should|shall)\s+not\b"
    r"|\bdon't\b"
    r"|\bnot\s+(?:as|use|create|modify|call|write|read|include)\b"
    r"|\bwithout\s+using\b"
    r"|[,;]\s*not\b"
    r"|^\s*no\s+",
    flags=re.IGNORECASE,
)


def positive_requirement_text(text: str) -> str:
    normalized = text.lower()
    clauses = re.split(r"(?:[.;]\s+|\n+)", normalized)
    return " ".join(
        clause
        for clause in clauses
        if not is_negative_boundary_clause(clause)
    )


def is_negative_boundary_clause(clause: str) -> bool:
    cleaned = clause.strip().lstrip("-* ").lower()
    if not cleaned:
        return False
    if NEGATIVE_BOUNDARY_MARKER.search(cleaned) is None:
        return False
    return any(re.search(pattern, cleaned) for pattern in FORBIDDEN_BOUNDARY_PATTERNS)
