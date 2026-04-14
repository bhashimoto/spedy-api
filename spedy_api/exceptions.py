from __future__ import annotations


class SpedyError(Exception):
    """Base exception for all Spedy SDK errors."""


class ValidationError(SpedyError):
    """HTTP 400 — field validation or business rule violation before the invoice is created."""

    def __init__(self, errors: list[dict]) -> None:
        self.errors = errors
        messages = "; ".join(e.get("message", str(e)) for e in errors)
        super().__init__(messages)


class AuthenticationError(SpedyError):
    """HTTP 403 — invalid API key or insufficient permissions."""


class NotFoundError(SpedyError):
    """HTTP 404 — resource not found."""


class RateLimitError(SpedyError):
    """HTTP 429 — rate limit exceeded."""

    def __init__(self, remaining: str | None, reset: str | None) -> None:
        self.remaining = remaining
        self.reset = reset
        super().__init__(f"Rate limit exceeded. Resets at {reset}.")


class SpedyServerError(SpedyError):
    """HTTP 5xx — internal server error."""

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        super().__init__(f"Server error {status_code}: {body}")
