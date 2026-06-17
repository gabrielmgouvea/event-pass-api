from fastapi import Request
from fastapi.responses import JSONResponse

class DomainException(Exception):
    def __init__(self, error_code: str, message: str, status_code: int = 400, details: dict = None):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )