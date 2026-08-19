from typing import Any
from pydantic import BaseModel, Field, field_validator

from app.core.errors import PreviewRenderSizeExceededException
from app.schemas.document import MAX_CONTENT_BYTES


class PreviewRenderRequest(BaseModel):
    """API-0201 プレビューレンダリング補助API 入力スキーマ."""

    content: str = Field(..., description="変換対象Markdown (最大2MB)")

    @field_validator("content", mode="before")
    @classmethod
    def validate_and_normalize_content(cls, v: Any) -> str:
        if v is None:
            raise PreviewRenderSizeExceededException(
                details=[{"msg": "Content is required."}]
            )
        if not isinstance(v, str):
            v = str(v)
        # REQ-0003: \r\n を \n へ正規化
        normalized = v.replace("\r\n", "\n")
        # REQ-0003: UTF-8バイト数で2MB上限チェック
        if len(normalized.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise PreviewRenderSizeExceededException(
                details=[{"msg": f"Content size exceeds {MAX_CONTENT_BYTES} bytes."}]
            )
        return normalized


class PreviewRenderResponse(BaseModel):
    """API-0201 プレビューレンダリング補助API 出力スキーマ (正常)."""

    html_content: str = Field(..., description="変換後安全なHTML文字列")
