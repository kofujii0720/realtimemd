from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator

from app.core.errors import InvalidExportFormatException
from app.schemas.document import MAX_CONTENT_BYTES

VALID_FORMATS = {"pdf", "html"}
VALID_PAPER_SIZES = {"A4", "Letter"}


class ExportRequest(BaseModel):
    """API-0301 ドキュメントエクスポートAPI 入力スキーマ."""

    content: str = Field(..., description="Markdown本文 (最大2MB)")
    format: str = Field(..., description="出力形式 ('pdf' または 'html')")
    paper_size: Optional[str] = Field(default="A4", description="PDF出力時用紙サイズ ('A4' または 'Letter', 既定: 'A4')")

    @field_validator("content", mode="before")
    @classmethod
    def validate_and_normalize_content(cls, v: Any) -> str:
        if v is None:
            raise InvalidExportFormatException(
                details=[{"msg": "Content is required."}]
            )
        if not isinstance(v, str):
            v = str(v)
        # REQ-0003: \r\n を \n へ正規化
        normalized = v.replace("\r\n", "\n")
        # REQ-0003: UTF-8バイト数で2MB上限チェック
        if len(normalized.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise InvalidExportFormatException(
                details=[{"msg": f"Content size exceeds {MAX_CONTENT_BYTES} bytes."}]
            )
        return normalized

    @field_validator("format", mode="before")
    @classmethod
    def validate_format(cls, v: Any) -> str:
        if v is None or not isinstance(v, str):
            raise InvalidExportFormatException(
                details=[{"msg": "Format is required and must be a string."}]
            )
        fmt = v.strip().lower()
        if fmt not in VALID_FORMATS:
            raise InvalidExportFormatException(
                details=[{"msg": f"Invalid format '{v}'. Must be 'pdf' or 'html'."}]
            )
        return fmt

    @field_validator("paper_size", mode="before")
    @classmethod
    def validate_paper_size(cls, v: Any) -> str:
        if v is None:
            return "A4"
        if not isinstance(v, str):
            raise InvalidExportFormatException(
                details=[{"msg": "paper_size must be a string."}]
            )
        matched = None
        for valid_size in VALID_PAPER_SIZES:
            if v.strip().lower() == valid_size.lower():
                matched = valid_size
                break
        if matched is None:
            raise InvalidExportFormatException(
                details=[{"msg": f"Invalid paper_size '{v}'. Must be 'A4' or 'Letter'."}]
            )
        return matched
