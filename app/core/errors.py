from typing import Any, List, Optional
from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.messages import MessageKeys


class AppException(HTTPException):
    """アプリケーション共通例外基底クラス."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message_key: str,
        details: Optional[List[Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message_key)
        self.code = code
        self.message_key = message_key
        self.details = details or []


# API-0102 定義済み例外
class DocumentSizeExceededException(AppException):
    """E-0102-001 本文サイズ制限(2MB)超過."""

    def __init__(self, details: Optional[List[Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="E-0102-001",
            message_key=MessageKeys.ERROR_DOC_SIZE_EXCEEDED,
            details=details,
        )


class DocumentTitleRequiredException(AppException):
    """E-0102-002 タイトル文字数制限(255文字)超過 / タイトル必須."""

    def __init__(self, details: Optional[List[Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="E-0102-002",
            message_key=MessageKeys.ERROR_DOC_TITLE_REQUIRED,
            details=details,
        )


class SystemErrorException(AppException):
    """E-0102-999 / E-0401-999 システム内部エラー."""

    def __init__(self, code: str = "E-0102-999", details: Optional[List[Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=code,
            message_key=MessageKeys.ERROR_COMMON_SYSTEM_ERROR,
            details=details,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """AppException用ハンドラー."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "messageKey": exc.message_key,
            "details": exc.details,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Pydantic バリデーションエラーハンドラー."""
    errors = exc.errors()
    # タイトルまたは本文のエラーを特定
    for err in errors:
        loc = err.get("loc", ())
        if "title" in loc:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "code": "E-0102-002",
                    "messageKey": MessageKeys.ERROR_DOC_TITLE_REQUIRED,
                    "details": errors,
                },
            )
        if "content" in loc:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "code": "E-0102-001",
                    "messageKey": MessageKeys.ERROR_DOC_SIZE_EXCEEDED,
                    "details": errors,
                },
            )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": "E-0102-002",
            "messageKey": MessageKeys.ERROR_DOC_TITLE_REQUIRED,
            "details": errors,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """未処理例外用ハンドラー (500)."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "E-0102-999",
            "messageKey": MessageKeys.ERROR_COMMON_SYSTEM_ERROR,
            "details": [],
        },
    )
