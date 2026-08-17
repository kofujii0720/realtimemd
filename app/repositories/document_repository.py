import sqlite3
from typing import Optional, Protocol

from app.core.database import get_db_connection
from app.models.tbl_0001 import DocumentModel


class DocumentRepositoryProtocol(Protocol):
    """ドキュメントリポジトリのインターフェース."""

    def create(self, document: DocumentModel) -> DocumentModel:
        ...

    def get_by_id(self, document_id: str) -> Optional[DocumentModel]:
        ...


class SqliteDocumentRepository:
    """SQLite を用いた TBL-0001 ドキュメントリポジトリ実装."""

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
