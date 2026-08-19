import sqlite3
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.v1.api_0201 import get_render_preview_usecase
from app.core.database import init_db
from app.core.messages import MessageKeys
from app.main import app
from app.schemas.document import MAX_CONTENT_BYTES
from app.schemas.preview import PreviewRenderRequest
from app.services.markdown_renderer import MarkdownRenderer
from app.usecases.render_preview import RenderPreviewUseCase


@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    """テスト用 SQLite データベースファイルパス."""
    db_file = tmp_path / "test_realtimemd.db"
    init_db(str(db_file))
    return str(db_file)


@pytest.fixture
def client(test_db_path: str) -> Generator[TestClient, None, None]:
    """FastAPI テストクライアント."""
    with TestClient(app) as test_client:
        yield test_client


# ==============================================================================
# VP-001: 入力必須・型チェック
# ==============================================================================

def test_vp001_preview_render_missing_content(client: TestClient) -> None:
    """[VP-001] content 項目が欠損（空ペイロード）している場合に 400 Bad Request となること."""
    response = client.post("/api/v1/preview/render", json={})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0201-001"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_SIZE_EXCEEDED
    assert isinstance(data["details"], list)


def test_vp001_preview_render_null_content(client: TestClient) -> None:
    """[VP-001] content 項目に None / null が渡された場合に 400 Bad Request となること."""
    response = client.post("/api/v1/preview/render", json={"content": None})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0201-001"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_SIZE_EXCEEDED


def test_vp001_preview_render_non_string_content(client: TestClient) -> None:
    """[VP-001] content 項目に数値等の非文字列型が渡された場合に文字列として正常に扱われ変換されること."""
    response = client.post("/api/v1/preview/render", json={"content": 123456})
    assert response.status_code == 200
    data = response.json()
    assert "<p>123456</p>" in data["html_content"]


# ==============================================================================
# VP-002: 境界値・制約チェック
# ==============================================================================

def test_vp002_preview_render_empty_content(client: TestClient) -> None:
    """[VP-002] 境界値: 0バイト (空文字 "") で正常に 200 OK となり空HTMLが返ること."""
    response = client.post("/api/v1/preview/render", json={"content": ""})
    assert response.status_code == 200
    assert response.json()["html_content"] == ""


def test_vp002_preview_render_1byte_content(client: TestClient) -> None:
    """[VP-002] 境界値: 1バイト ("a") で正常に 200 OK となりHTML変換されること."""
    response = client.post("/api/v1/preview/render", json={"content": "a"})
    assert response.status_code == 200
    assert response.json()["html_content"] == "<p>a</p>"


def test_vp002_preview_render_exact_2mb_boundary(client: TestClient) -> None:
    """[VP-002] 境界値: 2MB (2,097,152 bytes: 上限境界) で正常に 200 OK となること."""
    content_2mb = "a" * MAX_CONTENT_BYTES
    response = client.post("/api/v1/preview/render", json={"content": content_2mb})
    assert response.status_code == 200
    data = response.json()
    assert "html_content" in data
    assert f"<p>{content_2mb}</p>" == data["html_content"]


def test_vp002_preview_render_exceeds_2mb_boundary(client: TestClient) -> None:
    """[VP-002] 境界値: 2MB+1byte (2,097,153 bytes: 上限+1) で 400 Bad Request (E-0201-001) となること."""
    content_exceeded = "a" * (MAX_CONTENT_BYTES + 1)
    response = client.post("/api/v1/preview/render", json={"content": content_exceeded})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0201-001"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_SIZE_EXCEEDED


def test_vp002_preview_render_crlf_normalized(client: TestClient) -> None:
    """[VP-002] REQ-0003制約: 改行コード \\r\\n が \\n に自動正規化されてレンダリングされること."""
    crlf_content = "# Header\r\n\r\nParagraph line 1.\r\nParagraph line 2."
    response = client.post("/api/v1/preview/render", json={"content": crlf_content})
    assert response.status_code == 200
    data = response.json()
    assert "\r" not in data["html_content"]
    assert "<h1>Header</h1>" in data["html_content"]
    assert "<p>Paragraph line 1. Paragraph line 2.</p>" in data["html_content"]


# ==============================================================================
# VP-003: 正常レスポンス検証
# ==============================================================================

def test_vp003_preview_render_success_response_structure(client: TestClient) -> None:
    """[VP-003] HTTP 200 OK ステータスとレスポンス構造 (html_content) の検証."""
    sample_md = "# Title\n\nThis is a sample document."
    response = client.post("/api/v1/preview/render", json={"content": sample_md})
    assert response.status_code == 200
    data = response.json()
    assert list(data.keys()) == ["html_content"]
    assert isinstance(data["html_content"], str)
    assert "<h1>Title</h1>" in data["html_content"]
    assert "<p>This is a sample document.</p>" in data["html_content"]


def test_vp003_preview_render_various_markdown_syntaxes(client: TestClient) -> None:
    """[VP-003] 見出し, 強調, リスト, 引用, コードブロック, テーブルの各構文が正常にHTML化されること."""
    complex_md = (
        "## Section 1\n\n"
        "**bold text** and *italic text* and ~~deleted text~~\n\n"
        "- item 1\n"
        "- item 2\n\n"
        "1. step 1\n"
        "2. step 2\n\n"
        "> quoted note\n\n"
        "```python\n"
        "print('hello')\n"
        "```\n\n"
        "| ID | Name |\n"
        "|---|---|\n"
        "| 1 | Alice |\n"
    )
    response = client.post("/api/v1/preview/render", json={"content": complex_md})
    assert response.status_code == 200
    html_res = response.json()["html_content"]
    assert "<h2>Section 1</h2>" in html_res
    assert "<strong>bold text</strong>" in html_res
    assert "<em>italic text</em>" in html_res
    assert "<del>deleted text</del>" in html_res
    assert "<ul><li>item 1</li><li>item 2</li></ul>" in html_res
    assert "<ol><li>step 1</li><li>step 2</li></ol>" in html_res
    assert "<blockquote><p>quoted note</p></blockquote>" in html_res
    assert '<pre><code class="language-python">print(&#x27;hello&#x27;)</code></pre>' in html_res
    assert "<table><thead><tr><th>ID</th><th>Name</th></tr></thead><tbody><tr><td>1</td><td>Alice</td></tr></tbody></table>" in html_res


# ==============================================================================
# VP-004: 定義済みエラー発生検証
# ==============================================================================

def test_vp004_error_e0201_001_size_exceeded_details(client: TestClient) -> None:
    """[VP-004] E-0201-001: マルチバイト文字等で 2MB 超過時のエラーコードとメッセージキー検証."""
    # 3バイト文字（あ）で 2MB (2,097,152 bytes) 超過データを作成
    mb_content = "あ" * ((MAX_CONTENT_BYTES // 3) + 10)
    response = client.post("/api/v1/preview/render", json={"content": mb_content})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0201-001"
    assert data["messageKey"] == MessageKeys.ERROR_DOC_SIZE_EXCEEDED
    assert isinstance(data["details"], list)
    assert len(data["details"]) > 0


def test_vp004_error_e0201_999_internal_system_error() -> None:
    """[VP-004] E-0201-999: レンダリング処理中に予期せぬ例外が発生した場合に 500 システムエラーが返却されること."""
    class FailingUseCase:
        def execute(self, request: PreviewRenderRequest):
            raise RuntimeError("Renderer unexpected crash")

    app.dependency_overrides[get_render_preview_usecase] = lambda: FailingUseCase()
    try:
        with TestClient(app, raise_server_exceptions=False) as failing_client:
            response = failing_client.post(
                "/api/v1/preview/render",
                json={"content": "test markdown"},
            )
            assert response.status_code == 500
            data = response.json()
            assert data["code"] == "E-0201-999"
            assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# VP-005: 事前・事後条件・不変条件検証
# ==============================================================================

def test_vp005_no_database_state_change(
    client: TestClient,
    test_db_path: str,
) -> None:
    """[VP-005] 事後条件: API実行前後で DB (documents, document_histories テーブル) の状態が一切変更されないこと."""
    # 実行前のレコード数確認
    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        initial_doc_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM document_histories")
        initial_history_count = cursor.fetchone()[0]
    finally:
        conn.close()

    # レンダリングAPI実行
    response = client.post(
        "/api/v1/preview/render",
        json={"content": "# DB Unchanged Check\n\nNo persistence should occur."},
    )
    assert response.status_code == 200

    # 実行後のレコード数確認
    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        after_doc_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM document_histories")
        after_history_count = cursor.fetchone()[0]
        assert after_doc_count == initial_doc_count
        assert after_history_count == initial_history_count
    finally:
        conn.close()


# ==============================================================================
# VP-006: 副作用検証
# ==============================================================================

def test_vp006_no_side_effects(client: TestClient, tmp_path: Path) -> None:
    """[VP-006] 副作用検証: 外部ストレージやファイル等の外部副作用が発生しないこと."""
    files_before = set(tmp_path.iterdir())

    response = client.post(
        "/api/v1/preview/render",
        json={"content": "# Side Effect Test"},
    )
    assert response.status_code == 200

    files_after = set(tmp_path.iterdir())
    assert files_before == files_after


# ==============================================================================
# VP-007: べき等性・性能検証
# ==============================================================================

def test_vp007_idempotent_render(client: TestClient) -> None:
    """[VP-007] べき等性: 同一のリクエストを複数回送信した場合、常に同一の HTML 文字列が返却されること."""
    payload = {"content": "### Idempotent Test\n\n- item 1\n- item 2"}

    res1 = client.post("/api/v1/preview/render", json=payload)
    res2 = client.post("/api/v1/preview/render", json=payload)
    res3 = client.post("/api/v1/preview/render", json=payload)

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res3.status_code == 200

    assert res1.json()["html_content"] == res2.json()["html_content"] == res3.json()["html_content"]


# ==============================================================================
# VP-008: 処理順序の保証検証
# ==============================================================================

def test_vp008_validation_before_rendering(client: TestClient) -> None:
    """[VP-008] 処理順序: サイズバリデーションがレンダラー処理より先に実行され、不正データでレンダラーが実行されないこと."""
    mock_renderer = MagicMock(spec=MarkdownRenderer)
    custom_usecase = RenderPreviewUseCase(renderer=mock_renderer)

    app.dependency_overrides[get_render_preview_usecase] = lambda: custom_usecase
    try:
        # 2MB超過ペイロードを送信
        invalid_payload = {"content": "a" * (MAX_CONTENT_BYTES + 10)}
        response = client.post("/api/v1/preview/render", json=invalid_payload)
        assert response.status_code == 400

        # レンダラーの render メソッドは呼び出されていないことを検証
        mock_renderer.render.assert_not_called()
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# VP-009: 実装自由度範囲の確認
# ==============================================================================

def test_vp009_usecase_direct_execution() -> None:
    """[VP-009] ユースケース単体テスト: レンダラーを直接注入してユースケース単体で安全に変換できること."""
    usecase = RenderPreviewUseCase(renderer=MarkdownRenderer)
    request = PreviewRenderRequest(content="*hello world*")
    result = usecase.execute(request=request)

    assert result.html_content == "<p><em>hello world</em></p>"


def test_vp009_xss_sanitization_security(client: TestClient) -> None:
    """[VP-009] セキュリティ検証: XSSスクリプトや javascript: スキームがサニタイズされて安全に出力されること."""
    unsafe_md = (
        '<script>alert("XSS")</script>\n\n'
        "[malicious link](javascript:alert(1))\n\n"
        "![malicious img](javascript:alert(2))"
    )
    response = client.post("/api/v1/preview/render", json={"content": unsafe_md})
    assert response.status_code == 200
    html_res = response.json()["html_content"]

    # 生の <script> タグが出力されずエスケープされていること
    assert "<script>" not in html_res
    assert "&lt;script&gt;" in html_res

    # javascript: スキームが # にサニタイズされていること
    assert 'href="javascript:' not in html_res
    assert 'href="#"' in html_res
    assert 'src="javascript:' not in html_res
    assert 'src="#"' in html_res


# ==============================================================================
# VP-010: 未決定事項なしの確認
# ==============================================================================

def test_vp010_spec_confirmation_no_open_issues(client: TestClient) -> None:
    """[VP-010] API-0201 要確認事項なし: 確定仕様に沿って Markdown から安全な HTML が返却されること."""
    spec_md = "# API-0201 Document\n\nPreview rendering confirmation."
    response = client.post("/api/v1/preview/render", json={"content": spec_md})
    assert response.status_code == 200
    data = response.json()
    assert data["html_content"] == "<h1>API-0201 Document</h1>\n<p>Preview rendering confirmation.</p>"
