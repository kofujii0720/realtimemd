from app.core.errors import DocumentDeleteNotFoundException
from app.repositories.document_repository import DocumentRepositoryProtocol


class DeleteDocumentUseCase:
    """API-0104 ドキュメント削除ユースケース."""

    def __init__(self, repository: DocumentRepositoryProtocol) -> None:
        self.repository = repository

    def execute(self, document_id: str) -> None:
        """
        ドキュメント削除を実行する.

        制約・条件:
        - 事前条件: document_id に一致するレコードが TBL-0001 に存在すること (API-0104 3. 事前条件)
        - 事後条件: TBL-0001 および関連する TBL-0002 の該当レコードが削除されること (API-0104 3. 事後条件)
        - 不変条件: 削除対象外のドキュメントに影響を与えないこと (API-0104 3. 不変条件)
        - 副作用: DB更新: TBL-0001 および TBL-0002 DELETE (API-0104 4. 副作用)
        - べき等性: あり (API-0104 5. 非機能制約)
        """
        # リポジトリの delete メソッドを呼び出し
        if hasattr(self.repository, "delete"):
            deleted = self.repository.delete(document_id)
            if not deleted:
                raise DocumentDeleteNotFoundException(
                    details=[{"msg": f"Document with id '{document_id}' not found."}]
                )
        else:
            # delete メソッド未定義時の事前チェックフォールバック
            doc = self.repository.get_by_id(document_id)
            if doc is None:
                raise DocumentDeleteNotFoundException(
                    details=[{"msg": f"Document with id '{document_id}' not found."}]
                )
