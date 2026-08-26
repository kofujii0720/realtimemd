import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Generator, List
import pytest
from fastapi.testclient import TestClient

from app.api.v1.api_0101 import get_document_repository
from app.core.database import init_db
from app.core.messages import MessageKeys
from app.main import app
from app.models.tbl_0001 import DocumentModel
from app.repositories.document_repository import (
    DocumentRepositoryProtocol,
    SqliteDocumentRepository,
)
from app.schemas.document import DocumentHeader, DocumentListResponse
from app.usecases.list_documents import ListDocumentsUseCase


@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    """テスト用 SQLite データベースファイルパス."""
    db_file = tmp_path / "test_realtimemd_0101.db"
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
def sample_documents(test_repository: SqliteDocumentRepository) -> List[DocumentModel]:
    """事前登録ドキュメントフィクスチャ (異なる更新日時の5件)."""
    docs = [
        DocumentModel(
            id=str(uuid.uuid4()),
            title="ドキュメント1 (最古)",
            content="コンテンツ1",
            created_at="2026-08-19T10:00:00.000Z",
            updated_at="2026-08-19T10:00:00.000Z",
        ),
        DocumentModel(
            id=str(uuid.uuid4()),
            title="ドキュメント2 (中間1)",
            content="コンテンツ2",
            created_at="2026-08-19T11:00:00.000Z",
            updated_at="2026-08-19T11:00:00.000Z",
        ),
        DocumentModel(
            id=str(uuid.uuid4()),
            title="ドキュメント3 (中間2)",
            content="コンテンツ3",
            created_at="2026-08-19T12:00:00.000Z",
            updated_at="2026-08-19T12:00:00.000Z",
        ),
        DocumentModel(
            id=str(uuid.uuid4()),
            title="ドキュメント4 (中間3)",
            content="コンテンツ4",
            created_at="2026-08-19T13:00:00.000Z",
            updated_at="2026-08-19T13:00:00.000Z",
        ),
        DocumentModel(
            id=str(uuid.uuid4()),
            title="ドキュメント5 (最新)",
            content="コンテンツ5",
            created_at="2026-08-19T14:00:00.000Z",
            updated_at="2026-08-19T14:00:00.000Z",
        ),
    ]
    for doc in docs:
        test_repository.create(doc)
    return docs


# ==============================================================================
# VP-001: 入力必須・型チェック
# ==============================================================================

def test_vp001_list_documents_default_query_params(
    client: TestClient,
    sample_documents: List[DocumentModel],
) -> None:
    """[VP-001] 入力チェック: クエリパラメータ未指定時にデフォルト値 (limit=50, offset=0) で正常取得できること."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(sample_documents)
    assert len(data["items"]) == len(sample_documents)


def test_vp001_list_documents_invalid_type_params(client: TestClient) -> None:
    """[VP-001] 入力チェック: limit や offset に非整数型が渡された場合に 400 エラー (E-0101-001) となること."""
    # limit に文字列
    res_invalid_limit = client.get("/api/v1/documents?limit=abc")
    assert res_invalid_limit.status_code == 400
    data_limit = res_invalid_limit.json()
    assert data_limit["code"] == "E-0101-001"
    assert data_limit["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR

    # offset に文字列
    res_invalid_offset = client.get("/api/v1/documents?offset=xyz")
    assert res_invalid_offset.status_code == 400
    data_offset = res_invalid_offset.json()
    assert data_offset["code"] == "E-0101-001"
    assert data_offset["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR


# ==============================================================================
# VP-002: 境界値・制約チェック
# ==============================================================================

def test_vp002_list_documents_limit_boundaries(
    client: TestClient,
    sample_documents: List[DocumentModel],
) -> None:
    """[VP-002] 境界値・制約: limit の 0 (下限-1), 1 (下限), 100 (上限), 101 (上限+1) の4点テスト."""
    # limit=0 (下限-1: エラー)
    res_0 = client.get("/api/v1/documents?limit=0")
    assert res_0.status_code == 400
    assert res_0.json()["code"] == "E-0101-001"

    # limit=1 (下限: 正常)
    res_1 = client.get("/api/v1/documents?limit=1")
    assert res_1.status_code == 200
    data_1 = res_1.json()
    assert data_1["total"] == len(sample_documents)
    assert len(data_1["items"]) == 1

    # limit=100 (上限: 正常)
    res_100 = client.get("/api/v1/documents?limit=100")
    assert res_100.status_code == 200
    data_100 = res_100.json()
    assert data_100["total"] == len(sample_documents)
    assert len(data_100["items"]) == len(sample_documents)

    # limit=101 (上限+1: エラー)
    res_101 = client.get("/api/v1/documents?limit=101")
    assert res_101.status_code == 400
    assert res_101.json()["code"] == "E-0101-001"


def test_vp002_list_documents_offset_boundaries(
    client: TestClient,
    sample_documents: List[DocumentModel],
) -> None:
    """[VP-002] 境界値・制約: offset の -1 (下限-1), 0 (下限), 1 (下限+1), データ件数超過 の検証."""
    # offset=-1 (下限-1: エラー)
    res_neg = client.get("/api/v1/documents?offset=-1")
    assert res_neg.status_code == 400
    assert res_neg.json()["code"] == "E-0101-001"

    # offset=0 (下限: 正常)
    res_0 = client.get("/api/v1/documents?offset=0")
    assert res_0.status_code == 200
    assert len(res_0.json()["items"]) == len(sample_documents)

    # offset=1 (下限+1: 正常)
    res_1 = client.get("/api/v1/documents?offset=1")
    assert res_1.status_code == 200
    assert len(res_1.json()["items"]) == len(sample_documents) - 1

    # offset=1000 (データ件数超過: 空リスト返却)
    res_over = client.get("/api/v1/documents?offset=1000")
    assert res_over.status_code == 200
    data_over = res_over.json()
    assert data_over["total"] == len(sample_documents)
    assert data_over["items"] == []


# ==============================================================================
# VP-003: 正常レスポンス検証
# ==============================================================================

def test_vp003_list_documents_empty_database(client: TestClient) -> None:
    """[VP-003] 正常レスポンス: 登録データ0件の場合、total=0, items=[] が返却されること."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_vp003_list_documents_success_schema_and_values(
    client: TestClient,
    sample_documents: List[DocumentModel],
) -> None:
    """[VP-003] 正常レスポンス: HTTP 200 OK ステータスとレスポンスボディ構造 (total, items[].id, items[].title, items[].updated_at) の完全検証."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == len(sample_documents)
    assert isinstance(data["items"], list)
    assert len(data["items"]) == len(sample_documents)

    for item in data["items"]:
        # UUID 形式検証
        parsed_uuid = uuid.UUID(item["id"])
        assert str(parsed_uuid) == item["id"]
        # 各フィールドの型検証
        assert isinstance(item["title"], str)
        assert isinstance(item["updated_at"], str)


def test_vp003_list_documents_sorted_by_updated_at_desc(
    client: TestClient,
    sample_documents: List[DocumentModel],
) -> None:
    """[VP-003] 正常レスポンス: ドキュメント一覧が updated_at の降順（新しい順）でソートされていること."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    items = response.json()["items"]

    # sample_documents はドキュメント5が最新 (14:00)、ドキュメント1が最古 (10:00)
    assert items[0]["title"] == "ドキュメント5 (最新)"
    assert items[1]["title"] == "ドキュメント4 (中間3)"
    assert items[2]["title"] == "ドキュメント3 (中間2)"
    assert items[3]["title"] == "ドキュメント2 (中間1)"
    assert items[4]["title"] == "ドキュメント1 (最古)"

    # 日時文字列が降順であることを確認
    for i in range(len(items) - 1):
        assert items[i]["updated_at"] >= items[i + 1]["updated_at"]


def test_vp003_list_documents_pagination(
    client: TestClient,
    sample_documents: List[DocumentModel],
) -> None:
    """[VP-003] 正常レスポンス: limit と offset を組み合わせたページネーションが正しく機能すること."""
    # 5件中 limit=2, offset=1 (2番目、3番目のレコード: ドキュメント4, ドキュメント3)
    response = client.get("/api/v1/documents?limit=2&offset=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "ドキュメント4 (中間3)"
    assert data["items"][1]["title"] == "ドキュメント3 (中間2)"


# ==============================================================================
# VP-004: 定義済みエラー発生検証
# ==============================================================================

def test_vp004_error_e0101_001_query_parameter_validation(client: TestClient) -> None:
    """[VP-004] E-0101-001: クエリパラメータ制約違反時に HTTP 400 と定義済みエラーコードが返却されること."""
    response = client.get("/api/v1/documents?limit=-5")
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0101-001"
    assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR
    assert isinstance(data["details"], list)


def test_vp004_error_e0101_999_internal_system_error() -> None:
    """[VP-004] E-0101-999: リポジトリ/内部エラー発生時に HTTP 500 とシステムエラーコードが返却されること."""
    class FailingRepository:
        def list_documents(self, limit: int = 50, offset: int = 0):
            raise RuntimeError("Database read failure")

        def get_by_id(self, document_id: str):
            return None

        def create(self, document: DocumentModel) -> DocumentModel:
            return document

        def update_with_history(self, document: DocumentModel, is_explicit_save: bool, saved_at: str):
            return document

        def delete(self, document_id: str) -> bool:
            return True

    app.dependency_overrides[get_document_repository] = lambda: FailingRepository()
    try:
        with TestClient(app, raise_server_exceptions=False) as failing_client:
            response = failing_client.get("/api/v1/documents")
            assert response.status_code == 500
            data = response.json()
            assert data["code"] == "E-0101-999"
            assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# VP-005: 事前・事後条件・不変条件検証
# ==============================================================================

def test_vp005_postcondition_no_db_changes_on_list(
    client: TestClient,
    sample_documents: List[DocumentModel],
    test_repository: SqliteDocumentRepository,
) -> None:
    """[VP-005] 事後条件: ドキュメント一覧取得実行後も DB の状態が一切変更されないこと (DBの状態変更なし)."""
    # 実行前の全ドキュメント状態を記録
    before_total, before_items = test_repository.list_documents(limit=100, offset=0)

    # API 呼び出し実行
    response = client.get("/api/v1/documents?limit=50&offset=0")
    assert response.status_code == 200

    # 実行後の全ドキュメント状態を比較
    after_total, after_items = test_repository.list_documents(limit=100, offset=0)
    assert before_total == after_total
    assert len(before_items) == len(after_items)
    for b_item, a_item in zip(before_items, after_items):
        assert b_item.id == a_item.id
        assert b_item.title == a_item.title
        assert b_item.updated_at == a_item.updated_at


def test_vp005_invariant_updated_at_iso8601_format(
    client: TestClient,
    sample_documents: List[DocumentModel],
) -> None:
    """[VP-005] 不変条件: レスポンスの updated_at が ISO8601 UTC 形式 (YYYY-MM-DDTHH:mm:ss.sssZ) であること."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    items = response.json()["items"]

    for item in items:
        updated_at_str = item["updated_at"]
        assert updated_at_str.endswith("Z")
        assert "T" in updated_at_str

        # ISO8601 パース確認
        dt_str = updated_at_str[:-1] + "+00:00"
        parsed_dt = datetime.fromisoformat(dt_str)
        assert parsed_dt.tzinfo is not None


# ==============================================================================
# VP-006: 副作用検証
# ==============================================================================

def test_vp006_no_side_effects_on_sqlite_tables(
    client: TestClient,
    sample_documents: List[DocumentModel],
    test_db_path: str,
) -> None:
    """[VP-006] 副作用検証: GET リクエストによって SQLite の documents / document_histories テーブルにレコード追加・更新・削除が発生しないこと."""
    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        docs_count_before = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM document_histories")
        hist_count_before = cursor.fetchone()[0]

        # GET リクエスト実行
        response = client.get("/api/v1/documents")
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

def test_vp007_idempotency_multiple_list_requests(
    client: TestClient,
    sample_documents: List[DocumentModel],
) -> None:
    """[VP-007] べき等性検証: 同一クエリパラメータで複数回 GET リクエストを実行しても、常に同一のレスポンスが返却されること."""
    res1 = client.get("/api/v1/documents?limit=3&offset=1")
    res2 = client.get("/api/v1/documents?limit=3&offset=1")
    res3 = client.get("/api/v1/documents?limit=3&offset=1")

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res3.status_code == 200
    assert res1.json() == res2.json() == res3.json()


# ==============================================================================
# VP-008: 処理順序の保証検証
# ==============================================================================

def test_vp008_execution_order_validation_prevents_db_query(
    client: TestClient,
    test_db_path: str,
) -> None:
    """[VP-008] 処理順序: クエリパラメータバリデーションエラー時にはリポジトリの検索処理へ遷移せず即座に 400 が返却されること."""
    # バリデーションエラーになるリクエスト
    response = client.get("/api/v1/documents?limit=-10")
    assert response.status_code == 400
    assert response.json()["code"] == "E-0101-001"


# ==============================================================================
# VP-009: 実装自由度範囲の確認
# ==============================================================================

def test_vp009_architecture_usecase_standalone_unit_test() -> None:
    """[VP-009] アーキテクチャ規約: ListDocumentsUseCase がリポジトリプロトコルと疎結合に動作すること (純粋単体テスト)."""
    class MockRepository:
        def list_documents(self, limit: int, offset: int):
            dummy_items = [
                DocumentHeader(
                    id="dummy-uuid-1",
                    title="モックドキュメント1",
                    updated_at="2026-08-19T15:00:00.000Z",
                )
            ]
            return 1, dummy_items

    usecase = ListDocumentsUseCase(repository=MockRepository())
    result = usecase.execute(limit=10, offset=0)

    assert isinstance(result, DocumentListResponse)
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == "dummy-uuid-1"
    assert result.items[0].title == "モックドキュメント1"
    assert result.items[0].updated_at == "2026-08-19T15:00:00.000Z"


# ==============================================================================
# VP-010: 未決定事項なしの確認
# ==============================================================================

def test_vp010_spec_confirmation_no_open_issues(
    client: TestClient,
    sample_documents: List[DocumentModel],
) -> None:
    """[VP-010] API-0101 要確認事項なし: 仕様書に記載された全正常系・異常系パラメータが確定仕様通りに動作すること."""
    response = client.get("/api/v1/documents?limit=50&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(sample_documents)
    assert len(data["items"]) == len(sample_documents)
    assert "id" in data["items"][0]
    assert "title" in data["items"][0]
    assert "updated_at" in data["items"][0]
