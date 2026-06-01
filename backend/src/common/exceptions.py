from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(self, detail: str, code: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(status_code=status_code, detail={"detail": detail, "code": code})


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Not authenticated", code: str = "UNAUTHORIZED") -> None:
        super().__init__(detail=detail, code=code, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Insufficient permissions", code: str = "FORBIDDEN") -> None:
        super().__init__(detail=detail, code=code, status_code=status.HTTP_403_FORBIDDEN)


class ConflictException(AppException):
    def __init__(self, detail: str, code: str = "CONFLICT") -> None:
        super().__init__(detail=detail, code=code, status_code=status.HTTP_409_CONFLICT)


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found", code: str = "NOT_FOUND") -> None:
        super().__init__(detail=detail, code=code, status_code=status.HTTP_404_NOT_FOUND)
