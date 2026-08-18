import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from app.api.v1.api_0103 import get_document_repository
from app.core.database import init_db
from app.core.messages import MessageKeys
from app.main import app
from app.models.tbl_0001 import DocumentModel
from app.repositories.document_repository import SqliteDocumentRepository
from app.schemas.document import (
    MAX_CONTENT_BYTES,
    MAX_TITLE_LENGTH,
    DocumentUpdateRequest,
)
from app.usecases.create_document import format_iso8601_utc
from app.usecases.update_document import UpdateDocumentUseCase


@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    """テスト用 SQLite データベースファイルパス."""
    db_file = tmp_path / "test_realtimemd_0103.db"
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
def existing_document(test_repository: SqliteDocumentRepository) -> DocumentModel:
    """初期テスト用ドキュメント."""
    doc_id = str(uuid.uuid4())
    created_at = "2026-08-18T10:00:00.000Z"
    doc = DocumentModel(
        id=doc_id,
        title="初期タイトル",
        content="初期本文",
        created_at=created_at,
        updated_at=created_at,
    )
    return test_repository.create(doc)


# ==============================================================================
# VP-001: 入力必須・型チェック
# ==============================================================================

def test_vp001_update_missing_required_fields(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-001] 必須項目 (title, content) が欠損している場合に 400 エラーとなること."""
    # title 欠損
    res_no_title = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"content": "更新本文"},
    )
    assert res_no_title.status_code == 400
    assert res_no_title.json()["code"] == "E-0103-003"
    assert res_no_title.json()["messageKey"] == MessageKeys.ERROR_DOC_TITLE_REQUIRED

    # content 欠損
    res_no_content = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "更新タイトル"},
    )
    assert res_no_content.status_code == 400
    assert res_no_content.json()["code"] == "E-0103-002"
    assert res_no_content.json()["messageKey"] == MessageKeys.ERROR_DOC_SIZE_EXCEEDED


def test_vp001_update_type_coercion(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-001] 数値等の非文字列型が入力された場合に文字列として正常に扱われること."""
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": 99999, "content": 12345},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "99999"
    assert data["content"] == "12345"


def test_vp001_update_is_explicit_save_default_false(
    client: TestClient,
    existing_document: DocumentModel,
    test_db_path: str,
) -> None:
    """[VP-001] is_explicit_save 省略時にデフォルト値 false として扱われ、履歴が作成されないこと."""
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "更新後タイトル", "content": "更新後本文"},
    )
    assert response.status_code == 200

    # 履歴テーブル (document_histories) にレコードが追加されていないこと
    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM document_histories WHERE document_id = ?", (existing_document.id,))
        count = cursor.fetchone()[0]
        assert count == 0
    finally:
        conn.close()


# ==============================================================================
# VP-002: 境界値・制約チェック
# ==============================================================================

def test_vp002_update_title_boundaries(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-002] タイトル境界値: 1文字(下限)、255文字(上限境界)が正常に受け入れられること."""
    # 1文字
    res_1 = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "a", "content": "本文"},
    )
    assert res_1.status_code == 200
    assert res_1.json()["title"] == "a"

    # 255文字 (上限境界)
    title_255 = "t" * MAX_TITLE_LENGTH
    res_255 = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": title_255, "content": "本文"},
    )
    assert res_255.status_code == 200
    assert res_255.json()["title"] == title_255


def test_vp002_update_title_exceeds_or_empty(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-002] タイトル境界値: 0文字(空文字)、空白のみ、256文字(上限+1)でバリデーションエラーとなること."""
    # 0文字（空文字）
    res_empty = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "", "content": "本文"},
    )
    assert res_empty.status_code == 400
    assert res_empty.json()["code"] == "E-0103-003"
    assert res_empty.json()["messageKey"] == MessageKeys.ERROR_DOC_TITLE_REQUIRED

    # 空白のみ
    res_spaces = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "   ", "content": "本文"},
    )
    assert res_spaces.status_code == 400
    assert res_spaces.json()["code"] == "E-0103-003"

    # 256文字 (上限+1)
    title_256 = "t" * (MAX_TITLE_LENGTH + 1)
    res_256 = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": title_256, "content": "本文"},
    )
    assert res_256.status_code == 400
    assert res_256.json()["code"] == "E-0103-003"


def test_vp002_update_content_boundaries(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-002] 本文境界値: 0byte, 1byte, 2MB(2,097,152 bytes: 上限境界)が正常に受け入れられること."""
    # 0byte
    res_0 = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "タイトル", "content": ""},
    )
    assert res_0.status_code == 200
    assert res_0.json()["content"] == ""

    # 1byte
    res_1 = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "タイトル", "content": "c"},
    )
    assert res_1.status_code == 200
    assert res_1.json()["content"] == "c"

    # 2MB (2,097,152 bytes)
    content_2mb = "c" * MAX_CONTENT_BYTES
    res_2mb = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "タイトル", "content": content_2mb},
    )
    assert res_2mb.status_code == 200
    assert len(res_2mb.json()["content"].encode("utf-8")) == MAX_CONTENT_BYTES


def test_vp002_update_content_exceeds_2mb(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-002] 本文境界値: 2MB+1byte (2,097,153 bytes: 上限+1) でバリデーションエラーとなること."""
    content_exceeded = "c" * (MAX_CONTENT_BYTES + 1)
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "タイトル", "content": content_exceeded},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0103-002"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_SIZE_EXCEEDED


def test_vp002_update_crlf_normalized_to_lf(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-002] REQ-0003制約: 改行コード \\r\\n が \\n に自動正規化されること."""
    crlf_content = "# Updated\r\n\r\nLine 1.\r\nLine 2."
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "タイトル", "content": crlf_content},
    )
    assert response.status_code == 200
    data = response.json()
    assert "\r\n" not in data["content"]
    assert data["content"] == "# Updated\n\nLine 1.\nLine 2."


# ==============================================================================
# VP-003: 正常レスポンス検証
# ==============================================================================

def test_vp003_update_document_status_200_and_schema(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-003] HTTP 200 OK ステータスとレスポンスボディ構造 (id, title, content, updated_at) の検証."""
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "更新テストタイトル", "content": "## 更新本文"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == existing_document.id
    assert data["title"] == "更新テストタイトル"
    assert data["content"] == "## 更新本文"
    assert "updated_at" in data
    assert isinstance(data["updated_at"], str)


def test_vp003_update_without_explicit_save(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-003] is_explicit_save=False で正常に更新されること."""
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "自動保存タイトル", "content": "自動保存本文", "is_explicit_save": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "自動保存タイトル"
    assert data["content"] == "自動保存本文"


def test_vp003_update_with_explicit_save(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-003] is_explicit_save=True で正常に更新されること."""
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "明示保存タイトル", "content": "明示保存本文", "is_explicit_save": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "明示保存タイトル"
    assert data["content"] == "明示保存本文"


# ==============================================================================
# VP-004: 定義済みエラー発生検証
# ==============================================================================

def test_vp004_error_e0103_001_not_found(client: TestClient) -> None:
    """[VP-004] E-0103-001: 対象ドキュメントが存在しない場合に HTTP 404 と定義済みエラーコードが返却されること."""
    non_existent_id = str(uuid.uuid4())
    response = client.put(
        f"/api/v1/documents/{non_existent_id}",
        json={"title": "存在しない", "content": "本文"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "E-0103-001"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_NOT_FOUND
    assert isinstance(data["details"], list)


def test_vp004_error_e0103_002_size_exceeded(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-004] E-0103-002: 本文サイズ制限(2MB)超過時に HTTP 400 と定義済みエラーコードが返却されること."""
    large_content = "文" * (MAX_CONTENT_BYTES // 3 + 10)  # UTF-8 で 3バイト文字
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "タイトル", "content": large_content},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0103-002"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_SIZE_EXCEEDED
    assert isinstance(data["details"], list)


def test_vp004_error_e0103_003_title_required(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-004] E-0103-003: タイトル未入力・空文字・255文字超過時に HTTP 400 と定義済みエラーコードが返却されること."""
    # 空文字
    res_empty = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "", "content": "本文"},
    )
    assert res_empty.status_code == 400
    assert res_empty.json()["code"] == "E-0103-003"
    assert res_empty.json()["messageKey"] == MessageKeys.ERROR_DOC_TITLE_REQUIRED

    # 256文字
    res_long = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "標" * 256, "content": "本文"},
    )
    assert res_long.status_code == 400
    assert res_long.json()["code"] == "E-0103-003"
    assert res_long.json()["messageKey"] == MessageKeys.ERROR_DOC_TITLE_REQUIRED


def test_vp004_error_e0103_999_internal_system_error(existing_document: DocumentModel) -> None:
    """[VP-004] E-0103-999: 内部エラー発生時に HTTP 500 とシステムエラーコードが返却されること."""
    class FailingRepository:
        def get_by_id(self, document_id: str):
            return existing_document

        def update_with_history(self, document: DocumentModel, is_explicit_save: bool, saved_at: str):
            raise RuntimeError("Database connection failure")

    app.dependency_overrides[get_document_repository] = lambda: FailingRepository()
    try:
        with TestClient(app, raise_server_exceptions=False) as failing_client:
            response = failing_client.put(
                f"/api/v1/documents/{existing_document.id}",
                json={"title": "テスト", "content": "本文"},
            )
            assert response.status_code == 500
            data = response.json()
            assert data["code"] == "E-0103-999"
            assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# VP-005: 事前・事後条件・不変条件検証
# ==============================================================================

def test_vp005_postcondition_updated_at_and_content_updated(
    client: TestClient,
    existing_document: DocumentModel,
    test_repository: SqliteDocumentRepository,
) -> None:
    """[VP-005] 事後条件: TBL-0001.updated_at が現在時刻に更新され、title, content が反映されること."""
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "更新完了タイトル", "content": "更新完了本文"},
    )
    assert response.status_code == 200
    res_data = response.json()

    # DB から再取得して検証
    updated = test_repository.get_by_id(existing_document.id)
    assert updated is not None
    assert updated.title == "更新完了タイトル"
    assert updated.content == "更新完了本文"
    assert updated.updated_at == res_data["updated_at"]
    assert updated.updated_at != existing_document.updated_at


def test_vp005_postcondition_history_record_created_with_version(
    client: TestClient,
    existing_document: DocumentModel,
    test_db_path: str,
) -> None:
    """[VP-005] 事後条件: is_explicit_save=True の場合、TBL-0002 に履歴が追加され version_no がインクリメントされること."""
    # 1回目の明示保存 (version_no = 1)
    res1 = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "明示保存v1", "content": "本文v1", "is_explicit_save": True},
    )
    assert res1.status_code == 200

    # 2回目の明示保存 (version_no = 2)
    res2 = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "明示保存v2", "content": "本文v2", "is_explicit_save": True},
    )
    assert res2.status_code == 200

    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT version_no, content, saved_at
            FROM document_histories
            WHERE document_id = ?
            ORDER BY version_no ASC
            """,
            (existing_document.id,),
        )
        histories = cursor.fetchall()
        assert len(histories) == 2
        assert histories[0][0] == 1
        assert histories[0][1] == "本文v1"
        assert histories[1][0] == 2
        assert histories[1][1] == "本文v2"
    finally:
        conn.close()


def test_vp005_invariant_created_at_not_modified(
    client: TestClient,
    existing_document: DocumentModel,
    test_repository: SqliteDocumentRepository,
) -> None:
    """[VP-005] 不変条件: TBL-0001.created_at は更新によって変更されないこと."""
    original_created_at = existing_document.created_at

    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "変更タイトル", "content": "変更本文"},
    )
    assert response.status_code == 200

    updated = test_repository.get_by_id(existing_document.id)
    assert updated is not None
    assert updated.created_at == original_created_at


def test_vp005_updated_at_iso8601_utc_format(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-005] updated_at が ISO8601 UTC 形式 (YYYY-MM-DDTHH:mm:ss.sssZ) であること."""
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "日時テスト", "content": "日時本文"},
    )
    assert response.status_code == 200
    updated_at = response.json()["updated_at"]

    assert updated_at.endswith("Z")
    assert "T" in updated_at

    dt_str = updated_at[:-1] + "+00:00"
    parsed_dt = datetime.fromisoformat(dt_str)
    assert parsed_dt.tzinfo is not None


# ==============================================================================
# VP-006: 副作用検証
# ==============================================================================

def test_vp006_side_effect_db_update_without_history_when_explicit_save_false(
    client: TestClient,
    existing_document: DocumentModel,
    test_db_path: str,
) -> None:
    """[VP-006] 副作用検証: is_explicit_save=False の場合、TBL-0001 は更新されるが TBL-0002 には履歴が挿入されないこと."""
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "副作用検証（自動）", "content": "本文（自動）", "is_explicit_save": False},
    )
    assert response.status_code == 200

    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT title, content FROM documents WHERE id = ?", (existing_document.id,))
        doc_row = cursor.fetchone()
        assert doc_row[0] == "副作用検証（自動）"
        assert doc_row[1] == "本文（自動）"

        cursor.execute("SELECT COUNT(*) FROM document_histories WHERE document_id = ?", (existing_document.id,))
        hist_count = cursor.fetchone()[0]
        assert hist_count == 0
    finally:
        conn.close()


def test_vp006_side_effect_db_update_with_history_when_explicit_save_true(
    client: TestClient,
    existing_document: DocumentModel,
    test_db_path: str,
) -> None:
    """[VP-006] 副作用検証: is_explicit_save=True の場合、TBL-0001 の更新と TBL-0002 への履歴追加が同時に行われること."""
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "副作用検証（明示）", "content": "本文（明示）", "is_explicit_save": True},
    )
    assert response.status_code == 200

    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT title, content FROM documents WHERE id = ?", (existing_document.id,))
        doc_row = cursor.fetchone()
        assert doc_row[0] == "副作用検証（明示）"
        assert doc_row[1] == "本文（明示）"

        cursor.execute(
            "SELECT version_no, content FROM document_histories WHERE document_id = ?",
            (existing_document.id,),
        )
        hist_row = cursor.fetchone()
        assert hist_row is not None
        assert hist_row[0] == 1
        assert hist_row[1] == "本文（明示）"
    finally:
        conn.close()


# ==============================================================================
# VP-007: べき等性・性能検証
# ==============================================================================

def test_vp007_idempotency_multiple_updates_without_explicit_save(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-007] べき等性検証: is_explicit_save=False の同一リクエストを複数回実行した場合、同一の内容で更新されること."""
    payload = {"title": "べき等テスト", "content": "べき等本文", "is_explicit_save": False}
    res1 = client.put(f"/api/v1/documents/{existing_document.id}", json=payload)
    res2 = client.put(f"/api/v1/documents/{existing_document.id}", json=payload)

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json()["id"] == res2.json()["id"]
    assert res1.json()["title"] == res2.json()["title"]
    assert res1.json()["content"] == res2.json()["content"]


# ==============================================================================
# VP-008: 処理順序の保証検証
# ==============================================================================

def test_vp008_execution_order_no_db_changes_on_validation_failure(
    client: TestClient,
    existing_document: DocumentModel,
    test_db_path: str,
) -> None:
    """[VP-008] 処理順序: バリデーションエラー発生時は TBL-0001 の更新および TBL-0002 の履歴追加が行われないこと."""
    invalid_payload = {"title": "t" * 300, "content": "本文", "is_explicit_save": True}
    response = client.put(f"/api/v1/documents/{existing_document.id}", json=invalid_payload)
    assert response.status_code == 400

    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT title, content FROM documents WHERE id = ?", (existing_document.id,))
        row = cursor.fetchone()
        assert row[0] == "初期タイトル"
        assert row[1] == "初期本文"

        cursor.execute("SELECT COUNT(*) FROM document_histories WHERE document_id = ?", (existing_document.id,))
        count = cursor.fetchone()[0]
        assert count == 0
    finally:
        conn.close()


def test_vp008_execution_order_no_history_when_doc_not_found(
    client: TestClient,
    test_db_path: str,
) -> None:
    """[VP-008] 処理順序: 存在しない document_id の場合は 404 となり履歴も作成されないこと."""
    non_existent_id = str(uuid.uuid4())
    payload = {"title": "新規タイトル", "content": "本文", "is_explicit_save": True}
    response = client.put(f"/api/v1/documents/{non_existent_id}", json=payload)
    assert response.status_code == 404

    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM document_histories WHERE document_id = ?", (non_existent_id,))
        count = cursor.fetchone()[0]
        assert count == 0
    finally:
        conn.close()


# ==============================================================================
# VP-009: 実装自由度範囲の確認
# ==============================================================================

def test_vp009_architecture_usecase_receives_now_and_repository(
    test_repository: SqliteDocumentRepository,
    existing_document: DocumentModel,
) -> None:
    """[VP-009] アーキテクチャ規約: ユースケース層が引数 now とリポジトリを受け取って動作すること (純粋単体テスト)."""
    usecase = UpdateDocumentUseCase(repository=test_repository)
    fixed_now = datetime(2026, 8, 18, 15, 30, 0, 456000, tzinfo=timezone.utc)
    request = DocumentUpdateRequest(
        title="ユースケース直接実行",
        content="直接実行本文",
        is_explicit_save=True,
    )

    result = usecase.execute(
        document_id=existing_document.id,
        request=request,
        now=fixed_now,
    )

    assert result.id == existing_document.id
    assert result.title == "ユースケース直接実行"
    assert result.content == "直接実行本文"
    assert result.updated_at == "2026-08-18T15:30:00.456Z"


# ==============================================================================
# VP-010: 未決定事項なしの確認
# ==============================================================================

def test_vp010_spec_confirmation_no_open_issues(
    client: TestClient,
    existing_document: DocumentModel,
) -> None:
    """[VP-010] API-0103 要確認事項なし: 仕様に記載された全正常系・異常系パラメータが確定仕様通りに動作すること."""
    response = client.put(
        f"/api/v1/documents/{existing_document.id}",
        json={"title": "仕様確認ドキュメント更新", "content": "# Updated Content", "is_explicit_save": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == existing_document.id
    assert data["title"] == "仕様確認ドキュメント更新"
    assert data["content"] == "# Updated Content"
    assert "updated_at" in data
