import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.errors import DocumentSizeExceededException, DocumentTitleRequiredException
from app.models.tbl_0001 import DocumentModel
from app.repositories.document_repository import DocumentRepositoryProtocol
from app.schemas.document import (
    DEFAULT_CONTENT,
    DEFAULT_TITLE,
    MAX_CONTENT_BYTES,
    MAX_TITLE_LENGTH,
    DocumentCreateRequest,
    DocumentResponse,
)


def format_iso8601_utc(dt: datetime) -> str:
    """UTC日時を ISO8601 形式 (YYYY-MM-DDTHH:mm:ss.sssZ) 文字列にフォーマットする (REQ-0003)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    # ミリ秒3桁 + 'Z' 表記
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class CreateDocumentUseCase:
    """API-0102 ドキュメント新規作成ユースケース."""

    def __init__(self, repository: DocumentRepositoryProtocol) -> None:
        self.repository = repository

    def execute(
        self,
        request: DocumentCreateRequest,
        now: datetime,
    ) -> DocumentResponse:
        """
        ドキュメント新規作成を実行する.
        
        制約:
        - 現在時刻は引数 now で受け取る (.agent/rules/usecases.md)
        - 不変条件: created_at と updated_at は同値であること (API-0102 3. 不変条件)
        - 事後条件: TBL-0001 に新規レコードが1件追加されること (API-0102 3. 事後条件)
        """
        title = request.title if request.title is not None else DEFAULT_TITLE
        content = request.content if request.content is not None else DEFAULT_CONTENT

        # 改行コード正規化 (REQ-0003: \r\n -> \n)
        normalized_content = content.replace("\r\n", "\n")

        # 業務バリデーション
        if len(title) > MAX_TITLE_LENGTH:
            raise DocumentTitleRequiredException(
                details=[{"msg": f"Title exceeds maximum length of {MAX_TITLE_LENGTH} characters."}]
            )

        if len(normalized_content.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise DocumentSizeExceededException(
                details=[{"msg": f"Content exceeds maximum size of {MAX_CONTENT_BYTES} bytes."}]
            )

        # ID発行 (UUIDv4)
        doc_id = str(uuid.uuid4())

        # 日時文字列生成 (不変条件: created_at == updated_at)
        formatted_now = format_iso8601_utc(now)
        created_at = formatted_now
        updated_at = formatted_now

        # モデル作成
        document = DocumentModel(
            id=doc_id,
            title=title,
            content=normalized_content,
            created_at=created_at,
            updated_at=updated_at,
        )

        # DB永続化 (事後条件)
        saved = self.repository.create(document)

        return DocumentResponse(
            id=saved.id,
            title=saved.title,
            content=saved.content,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )
