"""Single error type for the BizSim engine.

Every engine failure is raised as :class:`EngineError` and serialised with the
project-wide error format::

    {"code": "SOME_CODE", "message": "plain language"}

The default HTTP status is 422 (invalid input); callers may pass 404 for an
unknown entity.
"""

from __future__ import annotations

from typing import Any


class EngineError(Exception):
    """A validation or domain error raised by engine code.

    Parameters
    ----------
    code:
        Upper-snake-case machine code, e.g. ``"INVALID_SHOCK"``.
    message:
        A plain-language sentence an operator can read.
    status:
        Suggested HTTP status code (422 for invalid input, 404 for unknown).
    """

    def __init__(self, code: str, message: str, status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical error payload."""
        return {"code": self.code, "message": self.message}

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"EngineError(code={self.code!r}, message={self.message!r})"


# Canonical error codes used across the engine. Keeping them in one place lets
# the API contract document and the tests refer to the same strings.
INVALID_SHOCK = "INVALID_SHOCK"
INVALID_INPUT = "INVALID_INPUT"
UNKNOWN_SUPPLIER = "UNKNOWN_SUPPLIER"
UNKNOWN_CUSTOMER = "UNKNOWN_CUSTOMER"
UNKNOWN_PRODUCT = "UNKNOWN_PRODUCT"
MAGNITUDE_OUT_OF_RANGE = "MAGNITUDE_OUT_OF_RANGE"
ELASTICITY_OUT_OF_RANGE = "ELASTICITY_OUT_OF_RANGE"
DEMAND_BAND_OUT_OF_RANGE = "DEMAND_BAND_OUT_OF_RANGE"
