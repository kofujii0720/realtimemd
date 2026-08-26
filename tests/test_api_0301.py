import sqlite3
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.v1.api_0301 import get_export_document_usecase
from app.core.database import init_db
from app.core.errors import PdfExportFailedException
from app.core.messages import MessageKeys
from app.main import app
from app.schemas.document import MAX_CONTENT_BYTES
from app.schemas.export import ExportRequest
from app.services.export_service import ExportService, PurePdfGenerator
from app.usecases.export_document import ExportDocumentUseCase


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

def test_vp001_export_missing_content(client: TestClient) -> None:
    """[VP-001] content 項目が欠損（キーなし）している場合に 400 Bad Request (E-0301-002) となること."""
    response = client.post("/api/v1/export", json={"format": "pdf"})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0301-002"
    assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR
    assert isinstance(data["details"], list)


def test_vp001_export_null_content(client: TestClient) -> None:
    """[VP-001] content 項目に None / null が渡された場合に 400 Bad Request (E-0301-002) となること."""
    response = client.post("/api/v1/export", json={"content": None, "format": "pdf"})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0301-002"
    assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR


def test_vp001_export_missing_format(client: TestClient) -> None:
    """[VP-001] format 項目が欠損（キーなし）している場合に 400 Bad Request (E-0301-002) となること."""
    response = client.post("/api/v1/export", json={"content": "# Title"})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0301-002"
    assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR


def test_vp001_export_invalid_format_type(client: TestClient) -> None:
    """[VP-001] format 項目に数値等の非文字列型が渡された場合に 400 Bad Request (E-0301-002) となること."""
    response = client.post("/api/v1/export", json={"content": "# Title", "format": 123})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0301-002"
    assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR


def test_vp001_export_invalid_paper_size_type(client: TestClient) -> None:
    """[VP-001] paper_size 項目に数値等の非文字列型が渡された場合に 400 Bad Request (E-0301-002) となること."""
    response = client.post(
        "/api/v1/export",
        json={"content": "# Title", "format": "pdf", "paper_size": 123},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0301-002"
    assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR


# ==============================================================================
# VP-002: 境界値・制約チェック
# ==============================================================================

def test_vp002_export_empty_content(client: TestClient) -> None:
    """[VP-002] 境界値: 0バイト (空文字 "") で正常に 200 OK となりエクスポートされること."""
    response = client.post("/api/v1/export", json={"content": "", "format": "html"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<main class=\"markdown-body\">\n    \n  </main>" in response.text


def test_vp002_export_1byte_content(client: TestClient) -> None:
    """[VP-002] 境界値: 1バイト ("a") で正常に 200 OK となりエクスポートされること."""
    response = client.post("/api/v1/export", json={"content": "a", "format": "html"})
    assert response.status_code == 200
    assert "<p>a</p>" in response.text


def test_vp002_export_exact_2mb_boundary(client: TestClient) -> None:
    """[VP-002] 境界値: 2MB (2,097,152 bytes: 上限境界) で正常に 200 OK となること."""
    content_2mb = "a" * MAX_CONTENT_BYTES
    response = client.post(
        "/api/v1/export",
        json={"content": content_2mb, "format": "html"},
    )
    assert response.status_code == 200
    assert f"<p>{content_2mb}</p>" in response.text


def test_vp002_export_exceeds_2mb_boundary(client: TestClient) -> None:
    """[VP-002] 境界値: 2MB+1byte (2,097,153 bytes: 上限+1) で 400 Bad Request (E-0301-002) となること."""
    content_exceeded = "a" * (MAX_CONTENT_BYTES + 1)
    response = client.post(
        "/api/v1/export",
        json={"content": content_exceeded, "format": "html"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0301-002"
    assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR


def test_vp002_export_crlf_normalized(client: TestClient) -> None:
    """[VP-002] REQ-0003制約: 改行コード \\r\\n が \\n に自動正規化されてエクスポートされること."""
    crlf_content = "# Title\r\n\r\nParagraph 1.\r\nParagraph 2."
    response = client.post(
        "/api/v1/export",
        json={"content": crlf_content, "format": "html"},
    )
    assert response.status_code == 200
    assert "\r" not in response.text
    assert "<h1>Title</h1>" in response.text
    assert "<p>Paragraph 1. Paragraph 2.</p>" in response.text


def test_vp002_export_format_case_and_whitespace_insensitivity(client: TestClient) -> None:
    """[VP-002] 制約チェック: format の大文字や前後の空白 (' PDF ', ' Html ') が許容され正常処理されること."""
    res_pdf = client.post(
        "/api/v1/export",
        json={"content": "# PDF Test", "format": " PDF "},
    )
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"

    res_html = client.post(
        "/api/v1/export",
        json={"content": "# HTML Test", "format": " Html "},
    )
    assert res_html.status_code == 200
    assert res_html.headers["content-type"].startswith("text/html")


def test_vp002_export_paper_size_case_and_whitespace_insensitivity(client: TestClient) -> None:
    """[VP-002] 制約チェック: paper_size の小文字や前後の空白 (' a4 ', ' letter ') が許容され正常処理されること."""
    res_a4 = client.post(
        "/api/v1/export",
        json={"content": "# A4 Test", "format": "pdf", "paper_size": " a4 "},
    )
    assert res_a4.status_code == 200

    res_letter = client.post(
        "/api/v1/export",
        json={"content": "# Letter Test", "format": "pdf", "paper_size": " letter "},
    )
    assert res_letter.status_code == 200


# ==============================================================================
# VP-003: 正常レスポンス検証
# ==============================================================================

def test_vp003_export_html_success_structure(client: TestClient) -> None:
    """[VP-003] format='html' で 200 OK, Content-Type, Content-Disposition, HTML構造が返ること."""
    markdown = "# Hello HTML Export\n\nThis is exported as HTML."
    response = client.post(
        "/api/v1/export",
        json={"content": markdown, "format": "html"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["content-disposition"] == 'attachment; filename="document.html"'
    
    html_text = response.text
    assert "<!DOCTYPE html>" in html_text
    assert "<title>Exported Document</title>" in html_text
    assert '<main class="markdown-body">' in html_text
    assert "<h1>Hello HTML Export</h1>" in html_text
    assert "<p>This is exported as HTML.</p>" in html_text
    assert "@page" in html_text


def test_vp003_export_pdf_a4_success(client: TestClient) -> None:
    """[VP-003] format='pdf', paper_size='A4' で 200 OK, Content-Type, Content-Disposition, PDFバイナリが返ること."""
    markdown = "# Hello PDF A4\n\nThis is exported as A4 PDF."
    response = client.post(
        "/api/v1/export",
        json={"content": markdown, "format": "pdf", "paper_size": "A4"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'attachment; filename="document.pdf"'
    
    pdf_bytes = response.content
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF-")


def test_vp003_export_pdf_letter_success(client: TestClient) -> None:
    """[VP-003] format='pdf', paper_size='Letter' で 200 OK となりPDFバイナリが返ること."""
    markdown = "# Hello PDF Letter\n\nThis is exported as Letter PDF."
    response = client.post(
        "/api/v1/export",
        json={"content": markdown, "format": "pdf", "paper_size": "Letter"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


def test_vp003_export_pdf_default_paper_size(client: TestClient) -> None:
    """[VP-003] paper_size 省略時に既定値 'A4' として正常に PDF が生成されること."""
    markdown = "# Default Paper Size\n\nTesting default A4 parameter."
    response = client.post(
        "/api/v1/export",
        json={"content": markdown, "format": "pdf"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


def test_vp003_export_various_markdown_syntaxes(client: TestClient) -> None:
    """[VP-003] 見出し, 強調, リスト, 引用, コードブロック, テーブルの各構文が正常に出力されること."""
    complex_md = (
        "# Title 1\n\n"
        "## Subtitle 2\n\n"
        "**bold text** and *italic text*\n\n"
        "- item 1\n"
        "- item 2\n\n"
        "> blockquote quote\n\n"
        "```python\n"
        "print('export test')\n"
        "```\n\n"
        "| Head 1 | Head 2 |\n"
        "|---|---|\n"
        "| Val 1 | Val 2 |\n"
    )
    response = client.post(
        "/api/v1/export",
        json={"content": complex_md, "format": "html"},
    )
    assert response.status_code == 200
    res_text = response.text
    assert "<h1>Title 1</h1>" in res_text
    assert "<h2>Subtitle 2</h2>" in res_text
    assert "<strong>bold text</strong>" in res_text
    assert "<em>italic text</em>" in res_text
    assert "<ul><li>item 1</li><li>item 2</li></ul>" in res_text
    assert "<blockquote><p>blockquote quote</p></blockquote>" in res_text
    assert '<pre><code class="language-python">print(&#x27;export test&#x27;)</code></pre>' in res_text
    assert "<table><thead><tr><th>Head 1</th><th>Head 2</th></tr></thead><tbody><tr><td>Val 1</td><td>Val 2</td></tr></tbody></table>" in res_text


# ==============================================================================
# VP-004: 定義済みエラー発生検証
# ==============================================================================

def test_vp004_error_e0301_002_unsupported_format(client: TestClient) -> None:
    """[VP-004] E-0301-002: 未対応の出力フォーマット (format='docx') 指定時に 400 Bad Request となること."""
    response = client.post(
        "/api/v1/export",
        json={"content": "# Docx Export", "format": "docx"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0301-002"
    assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR
    assert isinstance(data["details"], list)


def test_vp004_error_e0301_002_unsupported_paper_size(client: TestClient) -> None:
    """[VP-004] E-0301-002: 未対応の用紙サイズ (paper_size='B5') 指定時に 400 Bad Request となること."""
    response = client.post(
        "/api/v1/export",
        json={"content": "# B5 Paper", "format": "pdf", "paper_size": "B5"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "E-0301-002"
    assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR


def test_vp004_error_e0301_001_pdf_export_failure() -> None:
    """[VP-004] E-0301-001: PDF生成処理中に例外が発生した場合に 500 (E-0301-001) となること."""
    class FailingExportService:
        @classmethod
        def export_pdf(cls, markdown_content: str, paper_size: str = "A4") -> bytes:
            raise PdfExportFailedException(details=[{"msg": "WeasyPrint engine crashed"}])

    custom_usecase = ExportDocumentUseCase(export_service=FailingExportService)
    app.dependency_overrides[get_export_document_usecase] = lambda: custom_usecase
    try:
        with TestClient(app, raise_server_exceptions=False) as failing_client:
            response = failing_client.post(
                "/api/v1/export",
                json={"content": "# Test", "format": "pdf"},
            )
            assert response.status_code == 500
            data = response.json()
            assert data["code"] == "E-0301-001"
            assert data["messageKey"] == MessageKeys.ERROR_EXPORT_PDF_FAILED
    finally:
        app.dependency_overrides.clear()


def test_vp004_error_e0301_999_internal_system_error() -> None:
    """[VP-004] E-0301-999: 予期せぬ内部例外発生時に 500 システムエラーが返却されること."""
    class CrashingUseCase:
        def execute(self, request: ExportRequest):
            raise RuntimeError("Unexpected internal crash in export usecase")

    app.dependency_overrides[get_export_document_usecase] = lambda: CrashingUseCase()
    try:
        with TestClient(app, raise_server_exceptions=False) as crashing_client:
            response = crashing_client.post(
                "/api/v1/export",
                json={"content": "# Test", "format": "html"},
            )
            assert response.status_code == 500
            data = response.json()
            assert data["code"] == "E-0301-999"
            assert data["messageKey"] == MessageKeys.ERROR_COMMON_SYSTEM_ERROR
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# VP-005: 事前・事後条件・不変条件検証
# ==============================================================================

def test_vp005_no_database_state_change(client: TestClient, test_db_path: str) -> None:
    """[VP-005] 事後条件: エクスポートAPI実行前後で DB (documents, document_histories テーブル) の状態が一切変更されないこと."""
    conn = sqlite3.connect(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        initial_doc_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM document_histories")
        initial_history_count = cursor.fetchone()[0]
    finally:
        conn.close()

    # エクスポートAPI実行 (HTML & PDF)
    res_html = client.post("/api/v1/export", json={"content": "# Test DB Unchanged", "format": "html"})
    assert res_html.status_code == 200

    res_pdf = client.post("/api/v1/export", json={"content": "# Test DB Unchanged", "format": "pdf"})
    assert res_pdf.status_code == 200

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
    """[VP-006] 副作用検証: 外部ストレージやファイル等の外部副作用が発生せず、クリーンな状態が保たれること."""
    files_before = set(tmp_path.iterdir())

    response = client.post(
        "/api/v1/export",
        json={"content": "# Side Effect Export Test", "format": "pdf"},
    )
    assert response.status_code == 200

    files_after = set(tmp_path.iterdir())
    assert files_before == files_after


# ==============================================================================
# VP-007: べき等性・性能検証
# ==============================================================================

def test_vp007_idempotent_export(client: TestClient) -> None:
    """[VP-007] べき等性: 同一のリクエストを複数回送信した場合、常に同一のステータス・ヘッダー・レスポンス内容が返却されること."""
    payload = {"content": "### Idempotent Export\n\n- line 1\n- line 2", "format": "html"}

    res1 = client.post("/api/v1/export", json=payload)
    res2 = client.post("/api/v1/export", json=payload)
    res3 = client.post("/api/v1/export", json=payload)

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res3.status_code == 200

    assert res1.headers["content-type"] == res2.headers["content-type"] == res3.headers["content-type"]
    assert res1.text == res2.text == res3.text


# ==============================================================================
# VP-008: 処理順序の保証検証
# ==============================================================================

def test_vp008_validation_before_export_execution(client: TestClient) -> None:
    """[VP-008] 処理順序: 入力バリデーションがエクスポートサービス呼び出しより先に実行され、不正データでサービスが実行されないこと."""
    mock_service = MagicMock(spec=ExportService)
    custom_usecase = ExportDocumentUseCase(export_service=mock_service)

    app.dependency_overrides[get_export_document_usecase] = lambda: custom_usecase
    try:
        # 不正な format を送信
        invalid_payload = {"content": "# Test", "format": "invalid_format"}
        response = client.post("/api/v1/export", json=invalid_payload)
        assert response.status_code == 400

        # ExportService のメソッドは呼び出されていないことを検証
        mock_service.export_pdf.assert_not_called()
        mock_service.export_html.assert_not_called()
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# VP-009: 実装自由度範囲の確認
# ==============================================================================

def test_vp009_usecase_direct_execution() -> None:
    """[VP-009] ユースケース単体テスト: ExportDocumentUseCase を直接実行してバイナリおよびメディアタイプが返ること."""
    usecase = ExportDocumentUseCase(export_service=ExportService)

    # HTML エクスポート
    req_html = ExportRequest(content="# Title HTML", format="html")
    data_html, media_type_html, filename_html = usecase.execute(request=req_html)
    assert isinstance(data_html, bytes)
    assert media_type_html == "text/html; charset=utf-8"
    assert filename_html == "document.html"
    assert b"<h1>Title HTML</h1>" in data_html

    # PDF エクスポート
    req_pdf = ExportRequest(content="# Title PDF", format="pdf", paper_size="A4")
    data_pdf, media_type_pdf, filename_pdf = usecase.execute(request=req_pdf)
    assert isinstance(data_pdf, bytes)
    assert media_type_pdf == "application/pdf"
    assert filename_pdf == "document.pdf"
    assert data_pdf.startswith(b"%PDF-")


def test_vp009_pure_pdf_generator_standalone() -> None:
    """[VP-009] PurePdfGenerator 単体テスト: 複数ページにまたがるMarkdownからPDFバイナリが生成されること."""
    long_markdown = "\n\n".join([f"## Section {i}\n\nLine text for paragraph {i}." for i in range(1, 40)])
    pdf_bytes = PurePdfGenerator.generate(markdown_text=long_markdown, paper_size="Letter")
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-1.4\n")
    assert b"/Count " in pdf_bytes


# ==============================================================================
# VP-010: 未決定事項なしの確認
# ==============================================================================

def test_vp010_spec_confirmation_no_open_issues(client: TestClient) -> None:
    """[VP-010] API-0301 要確認事項なし: 確定仕様に沿って Markdown から PDF および HTML がバイナリストリームとしてエクスポートされること."""
    spec_md = "# API-0301 Spec Complete\n\nNo pending questions or open issues."
    
    res_pdf = client.post("/api/v1/export", json={"content": spec_md, "format": "pdf"})
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b"%PDF-")

    res_html = client.post("/api/v1/export", json={"content": spec_md, "format": "html"})
    assert res_html.status_code == 200
    assert "<h1>API-0301 Spec Complete</h1>" in res_html.text
