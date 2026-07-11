"""Custom exceptions for the FastAPI app."""


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code


class NotFound(AppException):
    """Resource not found."""

    def __init__(self, message: str = "Not found") -> None:
        super().__init__(message, status_code=404)


class BadRequest(AppException):
    """Bad request."""

    def __init__(self, message: str = "Bad request") -> None:
        super().__init__(message, status_code=400)


class Unauthorized(AppException):
    """Unauthorized."""

    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, status_code=401)
