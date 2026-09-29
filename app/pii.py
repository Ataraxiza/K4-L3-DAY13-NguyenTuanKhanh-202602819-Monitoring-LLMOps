from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, str] = {
    # Email
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",

    # Vietnamese phone:
    # 0xxxxxxxxx / +84xxxxxxxxx
    # Cho phép khoảng trắng hoặc dấu -
    "phone_vn": (
        r"(?<!\d)"
        r"(?:\+84|0)"
        r"(?:[ .-]?\d){9}"
        r"(?!\d)"
    ),

    # Vietnamese CCCD: exactly 12 digits
    "cccd": r"(?<!\d)\d{12}(?!\d)",

    # Credit card: 16 digits, optionally separated by space/hyphen
    "credit_card": (
        r"(?<!\d)"
        r"(?:\d{4}[- ]?){3}\d{4}"
        r"(?!\d)"
    ),
}


def scrub_text(text: str) -> str:
    safe = text

    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(
            pattern,
            f"[REDACTED_{name.upper()}]",
            safe,
        )

    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(
        user_id.encode("utf-8")
    ).hexdigest()[:12]
