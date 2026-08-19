from datetime import datetime
from typing import Optional

from app.core.errors import (
    DocumentNotFoundException,
    DocumentUpdateSizeExceededException,
    DocumentUpdateTitleRequiredException,
)
from app.models.tbl_0001 import DocumentModel
from app.repositories.document_repository import DocumentRepositoryProtocol
from app.schemas.document import (
    MAX_CONTENT_BYTES,
    MAX_TITLE_LENGTH,
    DocumentUpdateRequest,
    DocumentUpdateResponse,
)
from app.usecases.create_document import format_iso8601_utc


class UpdateDocumentUseCase:
    """API-0103 ドキュメント更新ユースケース."""

    def __init__(self, repository: DocumentRepositoryProtocol) -> None:
        self.repository = repository

    def execute(
        self,
        document_id: str,
        request: DocumentUpdateRequest,
        now: datetime,
    ) -> DocumentUpdateResponse:
        """
        ドキュメント更新を実行する.

        制約:
        - 現在時刻は引数 now で受け取る (.agent/rules/usecases.md)
        - 事前条件: document_id に一致するレコードが TBL-0001 に存在すること (API-0103 3. 事前条件)
        - 事後条件: TBL-0001.col.updated_at が現在時刻に更新されること。is_explicit_save=true の場合、TBL-0002 に履歴が追加されること (API-0103 3. 事後条件)
        - 不変条件: TBL-0001.col.created_at は変更されないこと (API-0103 3. 不変条件)
        - 処理順序: TBL-0001 の更新と TBL-0002 への履歴追加は同一トランザクション内で行うこと (API-0103 6. 処理順序の指定)
        """
        title = request.title
        content = request.content

        # タイトルバリデーション (1〜255文字)
        if not title or len(title.strip()) == 0 or len(title) > MAX_TITLE_LENGTH:
            raise DocumentUpdateTitleRequiredException(
                details=[{"msg": f"Title must be between 1 and {MAX_TITLE_LENGTH} characters."}]
            )

        # 改行コード正規化 (REQ-0003: \r\n -> \n)
        normalized_content = content.replace("\r\n", "\n")

        # 本文サイズバリデーション (最大2MB)
        if len(normalized_content.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise DocumentUpdateSizeExceededException(
                details=[{"msg": f"Content size exceeds maximum of {MAX_CONTENT_BYTES} bytes."}]
            )

        # 事前条件: document_id に一致するレコードが TBL-0001 に存在すること
        existing_doc = self.repository.get_by_id(document_id)
        if existing_doc is None:
            raise DocumentNotFoundException(
                code="E-0103-001",
                details=[{"msg": f"Document with id '{document_id}' not found."}],
            )

        # 日時文字列生成 (ISO8601 UTC)
        formatted_now = format_iso8601_utc(now)

        # 更新用モデル（不変条件: created_at は既存の値を保持）
        updated_doc = DocumentModel(
            id=document_id,
            title=title,
            content=normalized_content,
            created_at=existing_doc.created_at,
            updated_at=formatted_now,
        )

        # 同一トランザクションで更新および履歴作成 (処理順序の指定)
        saved = self.repository.update_with_history(
            document=updated_doc,
            is_explicit_save=request.is_explicit_save,
            saved_at=formatted_now,
        )

        if saved is None:
            raise DocumentNotFoundException(
                code="E-0103-001",
                details=[{"msg": f"Document with id '{document_id}' not found."}],
            )

        return DocumentUpdateResponse(
            id=saved.id,
            title=saved.title,
            content=saved.content,
            updated_at=saved.updated_at,
        )
