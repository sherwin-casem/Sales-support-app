from fastapi import Request
from fastapi.responses import JSONResponse

from src.common.exceptions import AppException


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"detail": str(exc.detail), "code": "ERROR"}
    return JSONResponse(status_code=exc.status_code, content=detail)
