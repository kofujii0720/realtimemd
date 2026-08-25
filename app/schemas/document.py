from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator

from app.core.errors import (
    DocumentQueryValidationException,
    DocumentSizeExceededException,
    DocumentTitleRequiredException,
    DocumentUpdateSizeExceededException,
    DocumentUpdateTitleRequiredException,
)

MAX_CONTENT_BYTES = 2 * 1024 * 1024  # 2MB (2,097,152 bytes)
MAX_TITLE_LENGTH = 255
DEFAULT_TITLE = "無題のドキュメント"
DEFAULT_CONTENT = ""


class DocumentHeader(BaseModel):
    """API-0101 ドキュメントメタデータヘッダー."""

    id: str = Field(..., description="ドキュメントID (UUID)")
    title: str = Field(..., description="タイトル")
    updated_at: str = Field(..., description="最終更新日時 (ISO8601 UTC)")


class DocumentListResponse(BaseModel):
    """API-0101 出力スキーマ (正常)."""

    total: int = Field(..., description="登録総件数")
    items: List[DocumentHeader] = Field(default_factory=list, description="ドキュメントメタデータ一覧")


class DocumentListQueryParams(BaseModel):
    """API-0101 クエリパラメータ入力スキーマ."""

    limit: Optional[int] = Field(default=50, ge=1, le=100, description="取得件数上限 (1〜100, デフォルト50)")
    offset: Optional[int] = Field(default=0, ge=0, description="取得開始位置 (0以上, デフォルト0)")

    @field_validator("limit", mode="before")
    @classmethod
    def validate_limit(cls, v: Any) -> int:
        if v is None:
            return 50
        try:
            val = int(v)
        except (ValueError, TypeError):
            raise DocumentQueryValidationException(
                details=[{"msg": "Query parameter 'limit' must be an integer."}]
            )
        if val < 1 or val > 100:
            raise DocumentQueryValidationException(
                details=[{"msg": "Query parameter 'limit' must be between 1 and 100."}]
            )
        return val

    @field_validator("offset", mode="before")
    @classmethod
    def validate_offset(cls, v: Any) -> int:
        if v is None:
            return 0
        try:
            val = int(v)
        except (ValueError, TypeError):
            raise DocumentQueryValidationException(
                details=[{"msg": "Query parameter 'offset' must be an integer."}]
            )
        if val < 0:
            raise DocumentQueryValidationException(
                details=[{"msg": "Query parameter 'offset' must be greater than or equal to 0."}]
            )
        return val


class DocumentCreateRequest(BaseModel):
    """API-0102 入力スキーマ."""

    title: Optional[str] = Field(default=DEFAULT_TITLE, description="ドキュメントタイトル (最大255文字)")
    content: Optional[str] = Field(default=DEFAULT_CONTENT, description="Markdown本文データ (最大2MB)")

    @field_validator("title", mode="before")
    @classmethod
    def validate_and_normalize_title(cls, v: Any) -> str:
        if v is None:
            return DEFAULT_TITLE
        if not isinstance(v, str):
            v = str(v)
        if len(v) > MAX_TITLE_LENGTH:
            raise DocumentTitleRequiredException(
                details=[{"msg": f"Title length exceeds {MAX_TITLE_LENGTH} characters."}]
            )
        return v

    @field_validator("content", mode="before")
    @classmethod
    def validate_and_normalize_content(cls, v: Any) -> str:
        if v is None:
            return DEFAULT_CONTENT
        if not isinstance(v, str):
            v = str(v)
        # REQ-0003: \r\n を \n へ正規化
        normalized = v.replace("\r\n", "\n")
        # REQ-0003: UTF-8バイト数で2MB上限チェック
        if len(normalized.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise DocumentSizeExceededException(
                details=[{"msg": f"Content size exceeds {MAX_CONTENT_BYTES} bytes."}]
            )
        return normalized


class DocumentResponse(BaseModel):
    """API-0102 出力スキーマ (正常)."""

    id: str
    title: str
    content: str
    created_at: str
    updated_at: str


class DocumentUpdateRequest(BaseModel):
    """API-0103 入力スキーマ."""

    title: str = Field(..., description="ドキュメントタイトル (1〜255文字)")
    content: str = Field(..., description="Markdown本文 (最大2MB)")
    is_explicit_save: bool = Field(default=False, description="明示保存フラグ (デフォルト: false)")

    @field_validator("title", mode="before")
    @classmethod
    def validate_and_normalize_title(cls, v: Any) -> str:
        if v is None:
            raise DocumentUpdateTitleRequiredException(
                details=[{"msg": "Title is required."}]
            )
        if not isinstance(v, str):
            v = str(v)
        # タイトル未入力・空文字・空白のみのチェック
        if len(v.strip()) == 0:
            raise DocumentUpdateTitleRequiredException(
                details=[{"msg": "Title cannot be empty."}]
            )
        if len(v) < 1 or len(v) > MAX_TITLE_LENGTH:
            raise DocumentUpdateTitleRequiredException(
                details=[{"msg": f"Title must be between 1 and {MAX_TITLE_LENGTH} characters."}]
            )
        return v

    @field_validator("content", mode="before")
    @classmethod
    def validate_and_normalize_content(cls, v: Any) -> str:
        if v is None:
            raise DocumentUpdateSizeExceededException(
                details=[{"msg": "Content is required."}]
            )
        if not isinstance(v, str):
            v = str(v)
        # REQ-0003: \r\n を \n へ正規化
        normalized = v.replace("\r\n", "\n")
        # REQ-0003: UTF-8バイト数で2MB上限チェック
        if len(normalized.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise DocumentUpdateSizeExceededException(
                details=[{"msg": f"Content size exceeds {MAX_CONTENT_BYTES} bytes."}]
            )
        return normalized


class DocumentUpdateResponse(BaseModel):
    """API-0103 出力スキーマ (正常)."""

    id: str
    title: str
    content: str
    updated_at: str


class ErrorResponse(BaseModel):
    """共通エラーレスポンススキーマ."""

    code: str
    messageKey: str
    details: List[Any] = []
