import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from app.api.v1.api_0102 import get_document_repository
from app.core.database import init_db
from app.core.messages import MessageKeys
from app.main import app
from app.models.tbl_0001 import DocumentModel
from app.repositories.document_repository import SqliteDocumentRepository
from app.schemas.document import (
    DEFAULT_CONTENT,
    DEFAULT_TITLE,
    MAX_CONTENT_BYTES,
    MAX_TITLE_LENGTH,
    DocumentCreateRequest,
)
from app.usecases.create_document import CreateDocumentUseCase, format_iso8601_utc


@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    """テスト用 SQLite データベースファイルパス."""
    db_file = tmp_path / "test_realtimemd.db"
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


# ==============================================================================
# VP-001: 入力必須・型チェック
# ==============================================================================

def test_vp001_create_document_default_values_when_empty_payload(client: TestClient) -> None:
    """[VP-001] 入力項目が空（省略時）にデフォルト値が正しく設定されること."""
    response = client.post("/api/v1/documents", json={})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == DEFAULT_TITLE
    assert data["content"] == DEFAULT_CONTENT
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_vp001_create_document_type_coercion(client: TestClient) -> None:
    """[VP-001] 数値等の非文字列型が入力された場合に文字列として正常に扱われること."""
    response = client.post("/api/v1/documents", json={"title": 12345, "content": 67890})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "12345"
    assert data["content"] == "67890"


# ==============================================================================
# VP-002: 境界値・制約チェック
# ==============================================================================

def test_vp002_create_document_title_boundaries(client: TestClient) -> None:
    """[VP-002] タイトル境界値: 0文字(空文字)、1文字、255文字(上限境界)が正常に受け入れられること."""
    # 0文字（空文字）
    res_empty = client.post("/api/v1/documents", json={"title": "", "content": "test"})
    assert res_empty.status_code == 201
    assert res_empty.json()["title"] == ""

    # 1文字
    res_1 = client.post("/api/v1/documents", json={"title": "a", "content": "test"})
    assert res_1.status_code == 201
    assert res_1.json()["title"] == "a"

    # 255文字 (上限境界)
    title_255 = "a" * MAX_TITLE_LENGTH
    res_255 = client.post("/api/v1/documents", json={"title": title_255, "content": "test"})
    assert res_255.status_code == 201
    assert res_255.json()["title"] == title_255


def test_vp002_create_document_title_exceeds_255_chars(client: TestClient) -> None:
    """[VP-002] タイトル境界値: 256文字 (上限+1) でバリデーションエラーとなること."""
    title_256 = "a" * (MAX_TITLE_LENGTH + 1)
    response = client.post("/api/v1/documents", json={"title": title_256})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0102-002"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_TITLE_REQUIRED


def test_vp002_create_document_content_boundaries(client: TestClient) -> None:
    """[VP-002] 本文境界値: 0byte, 1byte, 2MB(2,097,152 bytes: 上限境界)が正常に受け入れられること."""
    # 0byte
    res_0 = client.post("/api/v1/documents", json={"content": ""})
    assert res_0.status_code == 201
    assert res_0.json()["content"] == ""

    # 1byte
    res_1 = client.post("/api/v1/documents", json={"content": "x"})
    assert res_1.status_code == 201
    assert res_1.json()["content"] == "x"

    # 2MB (2,097,152 bytes)
    content_2mb = "a" * MAX_CONTENT_BYTES
    res_2mb = client.post("/api/v1/documents", json={"content": content_2mb})
    assert res_2mb.status_code == 201
    assert len(res_2mb.json()["content"].encode("utf-8")) == MAX_CONTENT_BYTES


def test_vp002_create_document_content_exceeds_2mb(client: TestClient) -> None:
    """[VP-002] 本文境界値: 2MB+1byte (2,097,153 bytes: 上限+1) でバリデーションエラーとなること."""
    content_exceeded = "a" * (MAX_CONTENT_BYTES + 1)
    response = client.post("/api/v1/documents", json={"content": content_exceeded})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0102-001"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_SIZE_EXCEEDED


def test_vp002_create_document_crlf_normalized_to_lf(client: TestClient) -> None:
    """[VP-002] REQ-0003制約: 改行コード \\r\\n が \\n に自動正規化されること."""
    crlf_content = "# Title\r\n\r\nFirst line.\r\nSecond line."
    response = client.post("/api/v1/documents", json={"content": crlf_content})
    assert response.status_code == 201
    data = response.json()
    assert "\r\n" not in data["content"]
    assert data["content"] == "# Title\n\nFirst line.\nSecond line."


# ==============================================================================
# VP-003: 正常レスポンス検証
# ==============================================================================

def test_vp003_create_document_status_201_and_schema(client: TestClient) -> None:
    """[VP-003] HTTP 201 Created ステータスとレスポンスボディ構造 (UUIDv4, title, content, created_at, updated_at) の検証."""
    response = client.post(
        "/api/v1/documents",
        json={"title": "テスト設計書", "content": "## 概要\nテスト本文です。"},
    )
    assert response.status_code == 201
    data = response.json()

    # UUIDv4 形式チェック
    val_uuid = uuid.UUID(data["id"], version=4)
    assert str(val_uuid) == data["id"]

    assert data["title"] == "テスト設計書"
    assert data["content"] == "## 概要\nテスト本文です。"
    assert isinstance(data["created_at"], str)
    assert isinstance(data["updated_at"], str)


def test_vp003_create_document_custom_values(client: TestClient) -> None:
    """[VP-003] 指定したカスタムタイトルと本文がそのままレスポンスに反映されること."""
    custom_title = "カスタムドキュメント"
    custom_content = "```python\nprint('hello')\n```"
    response = client.post(
        "/api/v1/documents",
        json={"title": custom_title, "content": custom_content},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == custom_title
    assert data["content"] == custom_content


# ==============================================================================
# VP-004: 定義済みエラー発生検証
# ==============================================================================

def test_vp004_error_e0102_001_content_size_exceeded(client: TestClient) -> None:
    """[VP-004] E-0102-001: 本文サイズ制限(2MB)超過時に HTTP 400 と定義済みエラーコードが返却されること."""
    large_content = "あ" * (MAX_CONTENT_BYTES // 3 + 10)  # UTF-8 で 3バイト文字
    response = client.post("/api/v1/documents", json={"content": large_content})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0102-001"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_SIZE_EXCEEDED
    assert isinstance(data["details"], list)


def test_vp004_error_e0102_002_title_length_exceeded(client: TestClient) -> None:
    """[VP-004] E-0102-002: タイトル文字数制限(255文字)超過時に HTTP 400 と定義済みエラーコードが返却されること."""
    long_title = "標題" * 128  # 256文字
    response = client.post("/api/v1/documents", json={"title": long_title})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0102-002"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_TITLE_REQUIRED
    assert isinstance(data["details"], list)


def test_vp004_error_e0102_999_internal_system_error() -> None:
    """[VP-004] E-0102-999: 内部エラー発生時に HTTP 500 とシステムエラーコードが返却されること."""
    class FailingRepository:
        def create(self, document: DocumentModel) -> DocumentModel:
            raise RuntimeError("Database connection failed")

        def get_by_id(self, document_id: str):
            return None

    app.dependency_overrides[get_document_repository] = lambda: FailingRepository()
    try:
        with TestClient(app, raise_server_exceptions=False) as failing_client:
            response = failing_client.post("/api/v1/documents", json={"title": "test"})
            assert response.status_code == 500
            data = response.json()
            assert data["code"] == "E-0102-999"
            assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# VP-005: 事前・事後条件・不変条件検証
# ==============================================================================

def test_vp005_postcondition_record_inserted_in_tbl0001(
    client: TestClient,
    test_repository: SqliteDocumentRepository,
) -> None:
    """[VP-005] 事後条件: TBL-0001 に新規レコードが1件追加されること."""
    response = client.post(
        "/api/v1/documents",
        json={"title": "永続化確認", "content": "本文データ"},
    )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    # リポジトリ経由で DB から取得して検証
    saved = test_repository.get_by_id(doc_id)
    assert saved is not None
    assert saved.id == doc_id
    assert saved.title == "永続化確認"
    assert saved.content == "本文データ"
    assert saved.created_at == response.json()["created_at"]
    assert saved.updated_at == response.json()["updated_at"]


def test_vp005_invariant_created_at_equals_updated_at_iso8601_utc(client: TestClient) -> None:
    """[VP-005] 不変条件: created_at と updated_at が同値であり、ISO8601 UTC形式 (YYYY-MM-DDTHH:mm:ss.sssZ) であること."""
    response = client.post("/api/v1/documents", json={})
    assert response.status_code == 201
    data = response.json()

    assert data["created_at"] == data["updated_at"]
    # ISO8601 UTC フォーマット確認 (例: 2026-08-18T07:09:00.000Z)
    assert data["created_at"].endswith("Z")
    assert "T" in data["created_at"]

    # パース可能であることを確認
    dt_str = data["created_at"][:-1] + "+00:00"
    parsed_dt = datetime.fromisoformat(dt_str)
    assert parsed_dt.tzinfo is not None


# ==============================================================================
# VP-006: 副作用検証
# ==============================================================================

def test_vp006_side_effect_db_persistence(
    client: TestClient,
    test_db_path: str,
) -> None:
    """[VP-006] 副作用検証: DB への INSERT が実行され、SQLite 直接クエリでレコードが存在すること."""
    response = client.post(
        "/api/v1/documents",
        json={"title": "副作用検証タイトル", "content": "副作用検証本文"},
    )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    # SQLite コネクションを直接開いて検証
    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, content FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == doc_id
        assert row[1] == "副作用検証タイトル"
        assert row[2] == "副作用検証本文"
    finally:
        conn.close()


# ==============================================================================
# VP-007: べき等性・性能検証
# ==============================================================================

def test_vp007_non_idempotent_multiple_creates(client: TestClient) -> None:
    """[VP-007] 非べき等性: 同一リクエストを2回送信した場合、異なるIDで2つのドキュメントが作成されること."""
    payload = {"title": "同一リクエスト", "content": "同一本文"}
    res1 = client.post("/api/v1/documents", json=payload)
    res2 = client.post("/api/v1/documents", json=payload)

    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res1.json()["id"] != res2.json()["id"]


# ==============================================================================
# VP-008: 処理順序の保証検証
# ==============================================================================

def test_vp008_execution_order_validation_before_db_insert(
    client: TestClient,
    test_db_path: str,
) -> None:
    """[VP-008] 処理順序: バリデーションエラー発生時は DB への挿入が行われないこと."""
    # バリデーションエラーになるリクエスト
    invalid_payload = {"title": "a" * 300}
    response = client.post("/api/v1/documents", json=invalid_payload)
    assert response.status_code == 400

    # DB にレコードが追加されていないことを確認
    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        assert count == 0
    finally:
        conn.close()


# ==============================================================================
# VP-009: 実装自由度範囲の確認
# ==============================================================================

def test_vp009_architecture_usecase_receives_now_and_repository(
    test_repository: SqliteDocumentRepository,
) -> None:
    """[VP-009] アーキテクチャ規約: ユースケース層が引数 now とリポジトリを受け取って動作すること (純粋単体テスト)."""
    usecase = CreateDocumentUseCase(repository=test_repository)
    fixed_now = datetime(2026, 8, 18, 12, 0, 0, 123000, tzinfo=timezone.utc)
    request = DocumentCreateRequest(title="ドメイン規約テスト", content="本文")

    result = usecase.execute(request=request, now=fixed_now)

    assert result.title == "ドメイン規約テスト"
    assert result.content == "本文"
    assert result.created_at == "2026-08-18T12:00:00.123Z"
    assert result.updated_at == "2026-08-18T12:00:00.123Z"


# ==============================================================================
# VP-010: 未決定事項なしの確認
# ==============================================================================

def test_vp010_spec_confirmation_no_open_issues(client: TestClient) -> None:
    """[VP-010] API-0102 要確認事項なし: 仕様に記載された全正常系・異常系パラメータが確定仕様通りに動作すること."""
    response = client.post(
        "/api/v1/documents",
        json={"title": "仕様確認ドキュメント", "content": "# Markdown Content"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "仕様確認ドキュメント"
    assert data["content"] == "# Markdown Content"
    assert data["created_at"] == data["updated_at"]
