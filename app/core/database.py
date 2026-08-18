import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional
from app.core.config import settings


def init_db(db_path: Optional[str] = None) -> None:
    """TBL-0001 ドキュメントテーブルおよびインデックスを初期化する."""
    target_path = db_path or settings.DB_PATH
    conn = sqlite3.connect(target_path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT '無題のドキュメント',
                    content TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_documents_updated_at 
                ON documents(updated_at DESC);
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_histories (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    version_no INTEGER NOT NULL DEFAULT 1,
                    content TEXT NOT NULL DEFAULT '',
                    saved_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                );
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_document_histories_doc_version 
                ON document_histories(document_id, version_no DESC);
                """
            )
    finally:
        conn.close()


@contextmanager
def get_db_connection(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """データベース接続のコンテキストマネージャ."""
    target_path = db_path or settings.DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
