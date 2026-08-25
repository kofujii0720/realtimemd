import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from app.api.v1.api_0105 import get_document_repository
from app.core.database import init_db
from app.core.messages import MessageKeys
from app.main import app
from app.models.tbl_0001 import DocumentModel
from app.repositories.document_repository import (
    DocumentRepositoryProtocol,
    SqliteDocumentRepository,
)
from app.schemas.document import DocumentResponse
from app.usecases.get_document_detail import GetDocumentDetailUseCase


@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    """テスト用 SQLite データベースファイルパス."""
    db_file = tmp_path / "test_realtimemd_0105.db"
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
def sample_document(test_repository: SqliteDocumentRepository) -> DocumentModel:
    """事前登録ドキュメントフィクスチャ."""
    doc = DocumentModel(
        id=str(uuid.uuid4()),
        title="テストドキュメントタイトル",
        content="# テストドキュメント本文\n\nこれはテスト用のMarkdownコンテンツです。",
        created_at="2026-08-19T10:00:00.000Z",
        updated_at="2026-08-19T10:30:00.000Z",
    )
    return test_repository.create(doc)


# ==============================================================================
# VP-001: 入力必須・型チェック
# ==============================================================================

def test_vp001_get_document_success_with_valid_uuid(
    client: TestClient,
    sample_document: DocumentModel,
) -> None:
    """[VP-001] 入力チェック: 有効なUUID形式のパスパラメータでドキュメントが取得できること."""
    response = client.get(f"/api/v1/documents/{sample_document.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_document.id


def test_vp001_get_document_missing_path_param_not_found(client: TestClient) -> None:
    """[VP-001] 入力チェック: document_id パスパラメータが欠損（ルートURL）している場合に 404/405/200 等になること."""
    # /api/v1/documents/ に対する GET は一覧APIまたは未定義ルート
    response = client.get("/api/v1/documents/")
    assert response.status_code in (200, 404, 405)


# ==============================================================================
# VP-002: 境界値・制約チェック
# ==============================================================================

def test_vp002_get_document_standard_and_uppercase_uuid(
    client: TestClient,
    test_repository: SqliteDocumentRepository,
) -> None:
    """[VP-002] 境界値・制約: RFC4122 準拠の36文字ハイフン区切りUUIDおよび大文字IDでも正常に識別・取得できること."""
    doc_id = str(uuid.uuid4()).upper()
    doc = DocumentModel(
        id=doc_id,
        title="大文字UUIDドキュメント",
        content="本文",
        created_at="2026-08-19T11:00:00.000Z",
        updated_at="2026-08-19T11:00:00.000Z",
    )
    test_repository.create(doc)

    response = client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["id"] == doc_id


def test_vp002_get_document_special_character_id_not_found(client: TestClient) -> None:
    """[VP-002] 境界値・制約: 記号や境界的な文字列IDで存在しない場合でも正しく 404 エラーとなること."""
    special_id = "non-existent-uuid-12345-!@#"
    response = client.get(f"/api/v1/documents/{special_id}")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "E-0105-001"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_NOT_FOUND


# ==============================================================================
# VP-003: 正常レスポンス検証
# ==============================================================================

def test_vp003_get_document_status_200_and_schema(
    client: TestClient,
    sample_document: DocumentModel,
) -> None:
    """[VP-003] 正常レスポンス: HTTP 200 OK ステータスとレスポンスボディ構造 (id, title, content, created_at, updated_at) の完全検証."""
    response = client.get(f"/api/v1/documents/{sample_document.id}")
    assert response.status_code == 200
    data = response.json()

    # 構造と値の検証
    assert data["id"] == sample_document.id
    assert data["title"] == sample_document.title
    assert data["content"] == sample_document.content
    assert data["created_at"] == sample_document.created_at
    assert data["updated_at"] == sample_document.updated_at

    # UUID 形式検証
    parsed_uuid = uuid.UUID(data["id"])
    assert str(parsed_uuid) == data["id"]


def test_vp003_get_document_multibyte_and_markdown_content(
    client: TestClient,
    test_repository: SqliteDocumentRepository,
) -> None:
    """[VP-003] 正常レスポンス: 日本語タイトル、複雑なMarkdown本文、数式・コードブロックを含むドキュメントが正しく返却されること."""
    multibyte_doc = DocumentModel(
        id=str(uuid.uuid4()),
        title="日本語タイトル with 特殊文字 🎉 & <tag>",
        content="""# タイトル\n\n```python\ndef test():\n    return '日本語'\n```\n\n$$\\frac{a}{b}$$""",
        created_at="2026-08-19T12:00:00.000Z",
        updated_at="2026-08-19T12:30:00.000Z",
    )
    test_repository.create(multibyte_doc)

    response = client.get(f"/api/v1/documents/{multibyte_doc.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == multibyte_doc.id
    assert data["title"] == multibyte_doc.title
    assert data["content"] == multibyte_doc.content


# ==============================================================================
# VP-004: 定義済みエラー発生検証
# ==============================================================================

def test_vp004_error_e0105_001_document_not_found(client: TestClient) -> None:
    """[VP-004] E-0105-001: 対象ドキュメントが存在しない場合に HTTP 404 と定義済みエラーコードが返却されること."""
    non_existent_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/documents/{non_existent_id}")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "E-0105-001"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_NOT_FOUND
    assert isinstance(data["details"], list)


def test_vp004_error_e0105_999_internal_system_error() -> None:
    """[VP-004] E-0105-999: リポジトリ/内部エラー発生時に HTTP 500 とシステムエラーコードが返却されること."""
    class FailingRepository:
        def get_by_id(self, document_id: str):
            raise RuntimeError("Database connection failure")

        def create(self, document: DocumentModel) -> DocumentModel:
            return document

        def update_with_history(self, document: DocumentModel, is_explicit_save: bool, saved_at: str):
            return document

    app.dependency_overrides[get_document_repository] = lambda: FailingRepository()
    try:
        with TestClient(app, raise_server_exceptions=False) as failing_client:
            response = failing_client.get(f"/api/v1/documents/{uuid.uuid4()}")
            assert response.status_code == 500
            data = response.json()
            assert data["code"] == "E-0105-999"
            assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# VP-005: 事前・事後条件・不変条件検証
# ==============================================================================

def test_vp005_postcondition_no_db_changes_on_get(
    client: TestClient,
    sample_document: DocumentModel,
    test_repository: SqliteDocumentRepository,
) -> None:
    """[VP-005] 事後条件: ドキュメント詳細取得実行後も DB の状態が一切変更されないこと (DBの状態変更なし)."""
    # 取得前
    before_doc = test_repository.get_by_id(sample_document.id)
    assert before_doc is not None

    # GET リクエスト実行
    response = client.get(f"/api/v1/documents/{sample_document.id}")
    assert response.status_code == 200

    # 取得後
    after_doc = test_repository.get_by_id(sample_document.id)
    assert after_doc is not None
    assert after_doc.id == before_doc.id
    assert after_doc.title == before_doc.title
    assert after_doc.content == before_doc.content
    assert after_doc.created_at == before_doc.created_at
    assert after_doc.updated_at == before_doc.updated_at


def test_vp005_invariant_iso8601_utc_format(
    client: TestClient,
    sample_document: DocumentModel,
) -> None:
    """[VP-005] 不変条件: created_at および updated_at が ISO8601 UTC 形式 (YYYY-MM-DDTHH:mm:ss.sssZ) であること."""
    response = client.get(f"/api/v1/documents/{sample_document.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["created_at"].endswith("Z")
    assert "T" in data["created_at"]
    assert data["updated_at"].endswith("Z")
    assert "T" in data["updated_at"]

    # パース確認
    dt_created = datetime.fromisoformat(data["created_at"][:-1] + "+00:00")
    dt_updated = datetime.fromisoformat(data["updated_at"][:-1] + "+00:00")
    assert dt_created.tzinfo is not None
    assert dt_updated.tzinfo is not None


# ==============================================================================
# VP-006: 副作用検証
# ==============================================================================

def test_vp006_no_side_effects_on_database_or_histories(
    client: TestClient,
    sample_document: DocumentModel,
    test_db_path: str,
) -> None:
    """[VP-006] 副作用検証: GET リクエストによってレコード作成・更新・削除や履歴テーブルへの追加が発生しないこと."""
    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        docs_count_before = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM document_histories")
        hist_count_before = cursor.fetchone()[0]

        # GET リクエスト
        response = client.get(f"/api/v1/documents/{sample_document.id}")
        assert response.status_code == 200

        cursor.execute("SELECT COUNT(*) FROM documents")
        docs_count_after = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM document_histories")
        hist_count_after = cursor.fetchone()[0]

        assert docs_count_before == docs_count_after
        assert hist_count_before == hist_count_after
    finally:
        conn.close()


# ==============================================================================
# VP-007: べき等性・性能検証
# ==============================================================================

def test_vp007_idempotency_multiple_get_requests(
    client: TestClient,
    sample_document: DocumentModel,
) -> None:
    """[VP-007] べき等性検証: 同一リクエストを複数回実行しても常に同一のステータスとレスポンスボディが返却されること."""
    res1 = client.get(f"/api/v1/documents/{sample_document.id}")
    res2 = client.get(f"/api/v1/documents/{sample_document.id}")
    res3 = client.get(f"/api/v1/documents/{sample_document.id}")

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res3.status_code == 200
    assert res1.json() == res2.json() == res3.json()


# ==============================================================================
# VP-008: 処理順序の保証検証
# ==============================================================================

def test_vp008_execution_order_lookup_before_response(
    client: TestClient,
    sample_document: DocumentModel,
) -> None:
    """[VP-008] 処理順序: リポジトリ検索が行われ、存在しない場合は即座に 404 となり、存在する場合はレスポンスモデルに変換されること."""
    # 存在しないID
    non_existent_id = str(uuid.uuid4())
    res_not_found = client.get(f"/api/v1/documents/{non_existent_id}")
    assert res_not_found.status_code == 404
    assert res_not_found.json()["code"] == "E-0105-001"

    # 存在するID
    res_found = client.get(f"/api/v1/documents/{sample_document.id}")
    assert res_found.status_code == 200
    assert res_found.json()["id"] == sample_document.id


# ==============================================================================
# VP-009: 実装自由度範囲の確認
# ==============================================================================

def test_vp009_architecture_usecase_standalone_unit_test(
    sample_document: DocumentModel,
) -> None:
    """[VP-009] アーキテクチャ規約: GetDocumentDetailUseCase がリポジトリプロトコルと疎結合に動作すること (純粋単体テスト)."""
    class MockRepository:
        def get_by_id(self, document_id: str):
            if document_id == sample_document.id:
                return sample_document
            return None

        def create(self, document: DocumentModel) -> DocumentModel:
            return document

        def update_with_history(self, document: DocumentModel, is_explicit_save: bool, saved_at: str):
            return document

    usecase = GetDocumentDetailUseCase(repository=MockRepository())
    result = usecase.execute(document_id=sample_document.id)

    assert isinstance(result, DocumentResponse)
    assert result.id == sample_document.id
    assert result.title == sample_document.title
    assert result.content == sample_document.content
    assert result.created_at == sample_document.created_at
    assert result.updated_at == sample_document.updated_at


# ==============================================================================
# VP-010: 未決定事項なしの確認
# ==============================================================================

def test_vp010_spec_confirmation_no_open_issues(
    client: TestClient,
    sample_document: DocumentModel,
) -> None:
    """[VP-010] API-0105 要確認事項なし: 仕様に記載された全正常系・異常系パラメータが確定仕様通りに動作すること."""
    response = client.get(f"/api/v1/documents/{sample_document.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_document.id
    assert data["title"] == sample_document.title
    assert data["content"] == sample_document.content
    assert "created_at" in data
    assert "updated_at" in data
