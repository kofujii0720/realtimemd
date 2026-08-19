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


# API-0103 定義済み例外
class DocumentNotFoundException(AppException):
    """E-0103-001 対象ドキュメントが存在しない."""

    def __init__(self, code: str = "E-0103-001", details: Optional[List[Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=code,
            message_key=MessageKeys.ERROR_DOC_NOT_FOUND,
            details=details,
        )


class DocumentUpdateSizeExceededException(AppException):
    """E-0103-002 本文サイズ制限(2MB)超過."""

    def __init__(self, details: Optional[List[Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="E-0103-002",
            message_key=MessageKeys.ERROR_DOC_SIZE_EXCEEDED,
            details=details,
        )


class DocumentUpdateTitleRequiredException(AppException):
    """E-0103-003 タイトル未入力・空・文字数超過."""

    def __init__(self, details: Optional[List[Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="E-0103-003",
            message_key=MessageKeys.ERROR_DOC_TITLE_REQUIRED,
            details=details,
        )


# API-0105 定義済み例外
class DocumentDetailNotFoundException(AppException):
    """E-0105-001 対象ドキュメントが存在しない."""

    def __init__(self, details: Optional[List[Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="E-0105-001",
            message_key=MessageKeys.ERROR_DOC_NOT_FOUND,
            details=details,
        )


# API-0201 定義済み例外
class PreviewRenderSizeExceededException(AppException):
    """E-0201-001 入力サイズ制限(2MB)超過."""

    def __init__(self, details: Optional[List[Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="E-0201-001",
            message_key=MessageKeys.ERROR_DOC_SIZE_EXCEEDED,
            details=details,
        )


class SystemErrorException(AppException):
    """E-0102-999 / E-0103-999 / E-0105-999 / E-0201-999 / E-0401-999 システム内部エラー."""

    def __init__(self, code: str = "E-0103-999", details: Optional[List[Any]] = None) -> None:
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
    path = request.url.path
    is_put = request.method == "PUT"
    is_preview = "/preview" in path

    # API-0201 プレビューエンドポイントの場合
    if is_preview:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": "E-0201-001",
                "messageKey": MessageKeys.ERROR_DOC_SIZE_EXCEEDED,
                "details": errors,
            },
        )

    # タイトルまたは本文のエラーを特定
    for err in errors:
        loc = err.get("loc", ())
        if "title" in loc:
            code = "E-0103-003" if is_put else "E-0102-002"
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "code": code,
                    "messageKey": MessageKeys.ERROR_DOC_TITLE_REQUIRED,
                    "details": errors,
                },
            )
        if "content" in loc:
            code = "E-0103-002" if is_put else "E-0102-001"
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "code": code,
                    "messageKey": MessageKeys.ERROR_DOC_SIZE_EXCEEDED,
                    "details": errors,
                },
            )

    default_code = "E-0103-003" if is_put else "E-0102-002"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": default_code,
            "messageKey": MessageKeys.ERROR_DOC_TITLE_REQUIRED,
            "details": errors,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """未処理例外用ハンドラー (500)."""
    path = request.url.path
    if "/preview" in path:
        code = "E-0201-999"
    elif request.method == "PUT":
        code = "E-0103-999"
    elif request.method == "GET" and "/documents/" in path:
        code = "E-0105-999"
    elif request.method == "POST" and "/documents" in path:
        code = "E-0102-999"
    else:
        code = "E-0105-999" if request.method == "GET" else "E-0102-999"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": code,
            "messageKey": MessageKeys.ERROR_COMMON_SYSTEM_ERROR,
            "details": [],
        },
    )
