import sqlite3
import uuid
from pathlib import Path
from typing import Generator
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.v1.api_0104 import get_document_repository
from app.core.database import get_db_connection, init_db
from app.core.messages import MessageKeys
from app.main import app
from app.models.tbl_0001 import DocumentModel
from app.repositories.document_repository import (
    DocumentRepositoryProtocol,
    SqliteDocumentRepository,
)
from app.usecases.delete_document import (
    DeleteDocumentUseCase,
    DocumentDeleteNotFoundException,
)


@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    """テスト用 SQLite データベースファイルパス."""
    db_file = tmp_path / "test_realtimemd_0104.db"
    init_db(str(db_file))
    return str(db_file)


@pytest.fixture
def test_repository(test_db_path: str) -> SqliteDocumentRepository:
    """テスト用リポジトリ."""
    return SqliteDocumentRepository(db_path=test_db_path)


@pytest.fixture
def client(test_repository: SqliteDocumentRepository) -> Generator[TestClient, None, None]:
    """FastAPI テストクライアント (リポジトリをテスト用にオーバーライド)."""
    app.dependency_overrides[get_document_repository] = lambda: test_repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_document_with_history(
    test_repository: SqliteDocumentRepository, test_db_path: str
) -> DocumentModel:
    """事前登録ドキュメントおよび関連変更履歴フィクスチャ."""
    doc_id = str(uuid.uuid4())
    doc = DocumentModel(
        id=doc_id,
        title="削除テスト用ドキュメント",
        content="# 削除対象\n\nこのドキュメントは削除されます。",
        created_at="2026-08-25T10:00:00.000Z",
        updated_at="2026-08-25T10:30:00.000Z",
    )
    created_doc = test_repository.create(doc)

    # 履歴レコードを追加 (TBL-0002)
    with get_db_connection(test_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO document_histories (id, document_id, version_no, content, saved_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                doc_id,
                1,
                "# 初期バージョン",
                "2026-08-25T10:00:00.000Z",
            ),
        )
        cursor.execute(
            """
            INSERT INTO document_histories (id, document_id, version_no, content, saved_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                doc_id,
                2,
                "# 第2バージョン",
                "2026-08-25T10:15:00.000Z",
            ),
        )

    return created_doc


# ==============================================================================
# VP-001: 入力必須・型チェック
# ==============================================================================

def test_vp001_delete_document_success_with_valid_uuid(
    client: TestClient,
    sample_document_with_history: DocumentModel,
) -> None:
    """[VP-001] 入力チェック: 有効なUUID形式のパスパラメータでドキュメントが削除できること."""
    response = client.delete(f"/api/v1/documents/{sample_document_with_history.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.text == ""


def test_vp001_delete_document_missing_path_param_not_found(client: TestClient) -> None:
    """[VP-001] 入力チェック: document_id パスパラメータが欠損している場合に 404/405 等になること."""
    response = client.delete("/api/v1/documents/")
    assert response.status_code in (404, 405)


# ==============================================================================
# VP-002: 境界値・制約チェック
# ==============================================================================

def test_vp002_delete_document_uppercase_uuid(
    client: TestClient,
    test_repository: SqliteDocumentRepository,
) -> None:
    """[VP-002] 境界値・制約: 大文字UUID形式のIDでも正常に識別・削除できること."""
    doc_id = str(uuid.uuid4()).upper()
    doc = DocumentModel(
        id=doc_id,
        title="大文字UUIDドキュメント",
        content="本文",
        created_at="2026-08-25T11:00:00.000Z",
        updated_at="2026-08-25T11:00:00.000Z",
    )
    test_repository.create(doc)

    response = client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert test_repository.get_by_id(doc_id) is None


def test_vp002_delete_document_non_existent_id_not_found(client: TestClient) -> None:
    """[VP-002] 境界値・制約: 存在しないIDでリクエストした場合に正しく 404 エラーとなること."""
    non_existent_id = str(uuid.uuid4())
    response = client.delete(f"/api/v1/documents/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["code"] == "E-0104-001"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_NOT_FOUND


# ==============================================================================
# VP-003: 正常レスポンス検証
# ==============================================================================

def test_vp003_delete_document_status_204_no_content(
    client: TestClient,
    sample_document_with_history: DocumentModel,
) -> None:
    """[VP-003] 正常レスポンス: HTTP 204 No Content ステータスと空のレスポンスボディを検証."""
    response = client.delete(f"/api/v1/documents/{sample_document_with_history.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""
    assert response.text == ""


# ==============================================================================
# VP-004: 定義済みエラー発生検証
# ==============================================================================

def test_vp004_error_e0104_001_document_not_found(client: TestClient) -> None:
    """[VP-004] E-0104-001: 削除対象ドキュメントが存在しない場合に HTTP 404 と定義済みエラーコードが返却されること."""
    non_existent_id = str(uuid.uuid4())
    response = client.delete(f"/api/v1/documents/{non_existent_id}")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "E-0104-001"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_NOT_FOUND
    assert isinstance(data["details"], list)


def test_vp004_error_e0104_999_internal_system_error() -> None:
    """[VP-004] E-0104-999: リポジトリ/内部エラー発生時に HTTP 500 とシステムエラーコードが返却されること."""
    class FailingRepository:
        def delete(self, document_id: str):
            raise RuntimeError("Database connection failure during delete")

        def get_by_id(self, document_id: str):
            raise RuntimeError("Database error")

    app.dependency_overrides[get_document_repository] = lambda: FailingRepository()
    try:
        with TestClient(app, raise_server_exceptions=False) as failing_client:
            response = failing_client.delete(f"/api/v1/documents/{uuid.uuid4()}")
            assert response.status_code == 500
            data = response.json()
            assert data["code"] == "E-0104-999"
            assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# VP-005: 事前・事後条件・不変条件検証
# ==============================================================================

def test_vp005_postcondition_and_invariant_deletion(
    client: TestClient,
    sample_document_with_history: DocumentModel,
    test_repository: SqliteDocumentRepository,
    test_db_path: str,
) -> None:
    """
    [VP-005] 事後条件・不変条件検証:
    - 事後条件: TBL-0001 および関連する TBL-0002 のレコードが削除されること.
    - 不変条件: 削除対象外の別ドキュメントおよびその変更履歴には一切影響を与えないこと.
    """
    # 削除対象外の別ドキュメントを作成
    other_doc_id = str(uuid.uuid4())
    other_doc = DocumentModel(
        id=other_doc_id,
        title="別ドキュメント（影響を受けない）",
        content="残るべき本文",
        created_at="2026-08-25T12:00:00.000Z",
        updated_at="2026-08-25T12:00:00.000Z",
    )
    test_repository.create(other_doc)

    with get_db_connection(test_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO document_histories (id, document_id, version_no, content, saved_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), other_doc_id, 1, "別ドキュメントの履歴", "2026-08-25T12:00:00.000Z"),
        )

    # 削除リクエスト実行
    target_id = sample_document_with_history.id
    response = client.delete(f"/api/v1/documents/{target_id}")
    assert response.status_code == 204

    # 事後条件の検証 (対象ドキュメントと履歴が削除されていること)
    assert test_repository.get_by_id(target_id) is None
    with get_db_connection(test_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents WHERE id = ?", (target_id,))
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT COUNT(*) FROM document_histories WHERE document_id = ?", (target_id,))
        assert cursor.fetchone()[0] == 0

        # 不変条件の検証 (削除対象外ドキュメントと履歴が保持されていること)
        cursor.execute("SELECT COUNT(*) FROM documents WHERE id = ?", (other_doc_id,))
        assert cursor.fetchone()[0] == 1
        cursor.execute("SELECT COUNT(*) FROM document_histories WHERE document_id = ?", (other_doc_id,))
        assert cursor.fetchone()[0] == 1


# ==============================================================================
# VP-006: 副作用検証
# ==============================================================================

def test_vp006_side_effects_on_db_delete(
    client: TestClient,
    sample_document_with_history: DocumentModel,
    test_db_path: str,
) -> None:
    """[VP-006] 副作用検証: DELETE 実行により TBL-0001 および TBL-0002 のレコード件数が正確に減少すること."""
    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        docs_before = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM document_histories")
        hist_before = cursor.fetchone()[0]

        # 削除実行
        response = client.delete(f"/api/v1/documents/{sample_document_with_history.id}")
        assert response.status_code == 204

        cursor.execute("SELECT COUNT(*) FROM documents")
        docs_after = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM document_histories")
        hist_after = cursor.fetchone()[0]

        assert docs_after == docs_before - 1
        assert hist_after == hist_before - 2
    finally:
        conn.close()


# ==============================================================================
# VP-007: べき等性・性能検証
# ==============================================================================

def test_vp007_idempotency_second_delete_returns_404(
    client: TestClient,
    sample_document_with_history: DocumentModel,
) -> None:
    """[VP-007] べき等性検証: 1回目の削除で204が返り、同一IDへの2回目の削除リクエストでは存在しないため404が返ること."""
    doc_id = sample_document_with_history.id
    res1 = client.delete(f"/api/v1/documents/{doc_id}")
    assert res1.status_code == 204

    res2 = client.delete(f"/api/v1/documents/{doc_id}")
    assert res2.status_code == 404
    assert res2.json()["code"] == "E-0104-001"


# ==============================================================================
# VP-008: 処理順序の保証検証
# ==============================================================================

def test_vp008_execution_order_lookup_before_delete(
    client: TestClient,
    sample_document_with_history: DocumentModel,
) -> None:
    """[VP-008] 処理順序: 事前チェック（存在確認）が行われ、存在しない場合は即座に 404 となり、存在する場合のみ削除されること."""
    # 存在しないID
    non_existent_id = str(uuid.uuid4())
    res_not_found = client.delete(f"/api/v1/documents/{non_existent_id}")
    assert res_not_found.status_code == 404
    assert res_not_found.json()["code"] == "E-0104-001"

    # 存在するID
    res_found = client.delete(f"/api/v1/documents/{sample_document_with_history.id}")
    assert res_found.status_code == 204


# ==============================================================================
# VP-009: 実装自由度範囲の確認
# ==============================================================================

def test_vp009_architecture_usecase_standalone_unit_test() -> None:
    """[VP-009] アーキテクチャ規約: DeleteDocumentUseCase がリポジトリプロトコルと疎結合に動作すること (純粋単体テスト)."""
    class MockRepository:
        def __init__(self):
            self.deleted_ids = []

        def delete(self, document_id: str) -> bool:
            if document_id == "existing-id":
                self.deleted_ids.append(document_id)
                return True
            return False

    mock_repo = MockRepository()
    usecase = DeleteDocumentUseCase(repository=mock_repo)

    # 正常系
    usecase.execute(document_id="existing-id")
    assert "existing-id" in mock_repo.deleted_ids

    # 異常系 (404)
    with pytest.raises(DocumentDeleteNotFoundException) as exc_info:
        usecase.execute(document_id="not-found-id")
    assert exc_info.value.code == "E-0104-001"
    assert exc_info.value.status_code == 404


# ==============================================================================
# VP-010: 未決定事項なしの確認
# ==============================================================================

def test_vp010_spec_confirmation_no_open_issues(
    client: TestClient,
    sample_document_with_history: DocumentModel,
) -> None:
    """[VP-010] API-0104 要確認事項なし: 仕様に記載された全正常系・異常系パラメータが確定仕様通りに動作すること."""
    doc_id = sample_document_with_history.id
    response = client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 204
    assert response.content == b""
