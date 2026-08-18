import uuid
from typing import Optional, Protocol

from app.core.database import get_db_connection
from app.models.tbl_0001 import DocumentModel
from app.models.tbl_0002 import DocumentHistoryModel


class DocumentRepositoryProtocol(Protocol):
    """ドキュメントリポジトリのインターフェース."""

    def create(self, document: DocumentModel) -> DocumentModel:
        ...

    def get_by_id(self, document_id: str) -> Optional[DocumentModel]:
        ...

    def update_with_history(
        self,
        document: DocumentModel,
        is_explicit_save: bool,
        saved_at: str,
    ) -> Optional[DocumentModel]:
        ...


class SqliteDocumentRepository:
    """SQLite を用いた TBL-0001 / TBL-0002 ドキュメントリポジトリ実装."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path

    def _get_connection(self):
        if self.db_path:
            return get_db_connection(self.db_path)
        return get_db_connection()

    def create(self, document: DocumentModel) -> DocumentModel:
        """TBL-0001 にドキュメントレコードを新規挿入する (事後条件)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO documents (id, title, content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.title,
                    document.content,
                    document.created_at,
                    document.updated_at,
                ),
            )
        return document

    def get_by_id(self, document_id: str) -> Optional[DocumentModel]:
        """IDでドキュメントを取得する."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, title, content, created_at, updated_at
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return DocumentModel(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def update_with_history(
        self,
        document: DocumentModel,
        is_explicit_save: bool,
        saved_at: str,
    ) -> Optional[DocumentModel]:
        """
        ドキュメントを更新し、is_explicit_save=True の場合は履歴レコードを追加する (同一トランザクション).
        対象ドキュメントが存在しない場合は None を返す.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 対象ドキュメントの存在確認
            cursor.execute("SELECT id FROM documents WHERE id = ?", (document.id,))
            if cursor.fetchone() is None:
                return None

            # TBL-0001 UPDATE (created_at は更新しない: 不変条件)
            cursor.execute(
                """
                UPDATE documents
                SET title = ?, content = ?, updated_at = ?
                WHERE id = ?
                """,
                (document.title, document.content, document.updated_at, document.id),
            )

            # TBL-0002 INSERT (明示保存時)
            if is_explicit_save:
                cursor.execute(
                    """
                    SELECT COALESCE(MAX(version_no), 0) AS max_v
                    FROM document_histories
                    WHERE document_id = ?
                    """,
                    (document.id,),
                )
                row = cursor.fetchone()
                next_version = (row["max_v"] if row else 0) + 1
                history_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO document_histories (id, document_id, version_no, content, saved_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (history_id, document.id, next_version, document.content, saved_at),
                )

        return document
