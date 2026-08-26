from typing import List, Protocol, Tuple

from app.schemas.document import DocumentHeader, DocumentListResponse


class DocumentListRepositoryProtocol(Protocol):
    """ドキュメント一覧取得リポジトリのインターフェース."""

    def list_documents(
        self, limit: int, offset: int
    ) -> Tuple[int, List[DocumentHeader]]:
        ...


class ListDocumentsUseCase:
    """API-0101 ドキュメント一覧取得ユースケース."""

    def __init__(self, repository: DocumentListRepositoryProtocol) -> None:
        self.repository = repository

    def execute(self, limit: int = 50, offset: int = 0) -> DocumentListResponse:
        """
        ドキュメント一覧取得を実行する.

        制約・条件:
        - 事前条件: 特になし (API-0101 3. 事前条件)
        - 事後条件: DBの状態変更なし (API-0101 3. 事後条件)
        - 不変条件: 特になし (API-0101 3. 不変条件)
        - べき等性: あり (API-0101 5. 非機能制約)
        - 応答性能: 200ms 以内 (API-0101 5. 非機能制約)
        """
        total, items = self.repository.list_documents(limit=limit, offset=offset)
        return DocumentListResponse(total=total, items=items)
