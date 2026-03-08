"""Custom domain errors and centralized HTTP error mapping."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error with HTTP mapping metadata."""

    status_code: int = 500
    error: str = "app_error"

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class QueryValidationError(AppError):
    status_code = 400
    error = "query_validation_error"


class DependencyNotReadyError(AppError):
    status_code = 503
    error = "dependency_not_ready"


class SearchExecutionError(AppError):
    status_code = 500
    error = "search_execution_error"


def register_exception_handlers(app: FastAPI) -> None:
    """Register handlers for domain exceptions."""

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error, "detail": exc.detail},
        )
