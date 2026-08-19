from typing import Optional

from app.core.errors import DocumentDetailNotFoundException
from app.repositories.document_repository import DocumentRepositoryProtocol
from app.schemas.document import DocumentResponse


class GetDocumentDetailUseCase:
    """API-0105 ドキュメント詳細取得ユースケース."""

    def __init__(self, repository: DocumentRepositoryProtocol) -> None:
        self.repository = repository

    def execute(self, document_id: str) -> DocumentResponse:
        """
        ドキュメント詳細取得を実行する.

        制約・条件:
        - 事前条件: document_id に一致するレコードが TBL-0001 に存在すること (API-0105 3. 事前条件)
        - 事後条件: DBの状態変更なし (API-0105 3. 事後条件)
        - 不変条件: 特になし (API-0105 3. 不変条件)
        - べき等性: あり (API-0105 5. 非機能制約)
        """
        document = self.repository.get_by_id(document_id)
        if document is None:
            raise DocumentDetailNotFoundException(
                details=[{"msg": f"Document with id '{document_id}' not found."}]
            )

        return DocumentResponse(
            id=document.id,
            title=document.title,
            content=document.content,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
