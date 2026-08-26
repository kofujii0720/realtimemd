from typing import Optional, Tuple

from app.core.errors import InvalidExportFormatException
from app.schemas.export import ExportRequest
from app.services.export_service import ExportService


class ExportDocumentUseCase:
    """API-0301 ドキュメントエクスポートユースケース."""

    def __init__(self, export_service: type[ExportService] = ExportService) -> None:
        self.export_service = export_service

    def execute(self, request: ExportRequest) -> Tuple[bytes, str, str]:
        """
        Markdownテキストを指定されたフォーマット (PDF/HTML) に変換してバイナリデータを返却する.
        
        制約・規約:
        - 事前条件: 特になし (API-0301 3. 事前条件)
        - 事後条件: DB状態変更なし (API-0301 3. 事後条件)
        - 不変条件: 特になし (API-0301 3. 不変条件)
        - 副作用: なし (API-0301 4. 副作用)
        - べき等性: あり (API-0301 5. 非機能制約)
        - usecases層で直接 datetime.now() や new Date() を呼ばない (REQ-0003, coding-python.md, usecases.md)
        
        Returns:
            Tuple[bytes, str, str]: (バイナリデータ, Content-Type, ファイル名)
        """
        fmt = request.format.lower()
        if fmt == "pdf":
            paper_size = request.paper_size or "A4"
            pdf_bytes = self.export_service.export_pdf(
                markdown_content=request.content,
                paper_size=paper_size,
            )
            return pdf_bytes, "application/pdf", "document.pdf"
        elif fmt == "html":
            html_bytes = self.export_service.export_html(
                markdown_content=request.content
            )
            return html_bytes, "text/html; charset=utf-8", "document.html"
        else:
            raise InvalidExportFormatException(
                details=[{"msg": f"Unsupported export format '{request.format}'"}]
            )
