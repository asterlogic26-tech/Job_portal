from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str, id: str = ""):
        msg = f"{resource} not found" if not id else f"{resource} '{id}' not found"
        super().__init__(msg, status_code=404)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class ExternalServiceError(AppError):
    def __init__(self, service: str, detail: str = ""):
        msg = f"External service error: {service}" + (f" — {detail}" if detail else "")
        super().__init__(msg, status_code=503)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "type": type(exc).__name__},
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging, traceback
    logging.getLogger("backend").error(
        f"Unhandled {type(exc).__name__} on {request.method} {request.url.path}: {exc}\n"
        + traceback.format_exc()
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc), "type": type(exc).__name__},
    )
