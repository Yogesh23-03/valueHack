"""GSTIN and PAN validation based on standard formats and checksum algorithms.

Implements the base-36 weighted checksum verification specified in Appendix B.
Sample valid GSTIN: 27AAPFU0939F1ZV
"""

from __future__ import annotations

import re

ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")


def pan_valid(p: str | None) -> bool:
    """Validate 10-character Indian Permanent Account Number (PAN) format."""
    if not p:
        return False
    p = p.strip().upper()
    return bool(PAN_RE.match(p))


def gstin_checksum(first14: str) -> str:
    """Compute the 15th checksum character of a 14-character GSTIN prefix using base-36 arithmetic."""
    total = 0
    for i, ch in enumerate(first14):
        prod = ALPHA.index(ch) * (1 if i % 2 == 0 else 2)
        total += (prod // 36) + (prod % 36)
    check_val = (36 - (total % 36)) % 36
    return ALPHA[check_val]


def gstin_valid(g: str | None) -> bool:
    """Validate a 15-character GSTIN string including length, charset, PAN match, and checksum."""
    if not g:
        return False
    g = g.strip().upper()
    if len(g) != 15 or any(ch not in ALPHA for ch in g):
        return False
    if g[13] != "Z" or not PAN_RE.match(g[2:12]):
        return False
    return gstin_checksum(g[:14]) == g[14]


def extract_pan_from_gstin(g: str) -> str | None:
    """Extract the 10-character PAN from a valid GSTIN."""
    g = g.strip().upper()
    if len(g) >= 12 and PAN_RE.match(g[2:12]):
        return g[2:12]
    return None
