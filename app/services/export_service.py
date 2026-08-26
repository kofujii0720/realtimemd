import html
import io
import re
from typing import List, Optional, Tuple

from app.core.errors import PdfExportFailedException
from app.services.markdown_renderer import MarkdownRenderer

# 共通CSSスタイル定義 (BR-0301-1: Preview.module.css と整合)
COMMON_EXPORT_CSS = """
@page {
  margin: 20mm;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 11pt;
  line-height: 1.7;
  color: #1e293b;
  background-color: #ffffff;
  margin: 0;
  padding: 0;
}
.markdown-body {
  max-width: 100%;
}
.markdown-body h1 {
  font-size: 1.8rem;
  font-weight: 700;
  margin-top: 0;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e2e8f0;
}
.markdown-body h2 {
  font-size: 1.4rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid #e2e8f0;
}
.markdown-body h3 {
  font-size: 1.2rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}
.markdown-body p {
  margin-top: 0;
  margin-bottom: 1rem;
}
.markdown-body ul,
.markdown-body ol {
  margin-top: 0;
  margin-bottom: 1rem;
  padding-left: 1.5rem;
}
.markdown-body li {
  margin-bottom: 0.25rem;
}
.markdown-body blockquote {
  margin: 0 0 1rem;
  padding: 0.5rem 1rem;
  color: #64748b;
  border-left: 4px solid #cbd5e1;
  background-color: #f8fafc;
}
.markdown-body pre {
  background-color: #0f172a;
  color: #f8fafc;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0 0 1rem;
  font-size: 0.85em;
  page-break-inside: avoid;
}
.markdown-body code {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  font-size: 0.875em;
  background-color: #f1f5f9;
  padding: 0.2em 0.4em;
  border-radius: 4px;
  color: #0f172a;
}
.markdown-body pre code {
  background-color: transparent;
  padding: 0;
  color: inherit;
}
.markdown-body hr {
  border: 0;
  height: 1px;
  background: #e2e8f0;
  margin: 1.5rem 0;
}
.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 1rem;
}
.markdown-body th,
.markdown-body td {
  border: 1px solid #e2e8f0;
  padding: 0.5rem 0.75rem;
  text-align: left;
}
.markdown-body th {
  background-color: #f8fafc;
  font-weight: 600;
}
.markdown-body a {
  color: #2563eb;
  text-decoration: underline;
}
.markdown-body strong {
  font-weight: 600;
}
"""


class PurePdfGenerator:
    """
    Pure Python による PDF 1.4 バイナリ生成器.
    
    WeasyPrint等の外部Cライブラリが利用できない環境下でも安全かつ確実にPDFバイナリを出力するフォールバック生成器.
    """

    PAGE_SIZES = {
        "A4": (595.28, 841.89),
        "Letter": (612.0, 792.0),
    }

    @classmethod
    def _escape_pdf_string(cls, text: str) -> str:
        """PDF文字列リテラル用のエスケープおよび安全なASCIIエンコード."""
        escaped = []
        for char in text:
            code = ord(char)
            if char == "\\":
                escaped.append("\\\\")
            elif char == "(":
                escaped.append("\\(")
            elif char == ")":
                escaped.append("\\)")
            elif 32 <= code <= 126:
                escaped.append(char)
            elif char == "\t":
                escaped.append("    ")
            else:
                # 非ASCII文字は安全に8進数エスケープまたは文字表現
                # 標準フォントで描画可能な範囲外の場合は代替表記
                try:
                    latin_bytes = char.encode("latin-1")
                    for b in latin_bytes:
                        escaped.append(f"\\{b:03o}")
                except UnicodeEncodeError:
                    escaped.append("?")
        return "".join(escaped)

    @classmethod
    def generate(cls, markdown_text: str, paper_size: str = "A4") -> bytes:
        """MarkdownテキストからPDF 1.4バイナリを生成する."""
        width, height = cls.PAGE_SIZES.get(paper_size, cls.PAGE_SIZES["A4"])

        margin_left = 50.0
        margin_top = 50.0
        margin_bottom = 50.0
        content_height = height - margin_top - margin_bottom

        # Markdownを行ごとに簡易レイアウト
        lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        pages_content: List[List[Tuple[str, int, str]]] = []  # [(font_tag, font_size, text)]
        current_page: List[Tuple[str, int, str]] = []
        current_y = height - margin_top

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                current_y -= 14
                if current_y < margin_bottom:
                    pages_content.append(current_page)
                    current_page = []
                    current_y = height - margin_top
                continue

            # 見出し・通常行の判定
            if line.startswith("# "):
                font_tag = "/F2"  # Bold
                font_size = 18
                line_height = 24
                display_text = line[2:].strip()
            elif line.startswith("## "):
                font_tag = "/F2"  # Bold
                font_size = 14
                line_height = 20
                display_text = line[3:].strip()
            elif line.startswith("### "):
                font_tag = "/F2"  # Bold
                font_size = 12
                line_height = 16
                display_text = line[4:].strip()
            elif line.startswith("```"):
                font_tag = "/F3"  # Courier
                font_size = 10
                line_height = 13
                display_text = line
            elif line.startswith("> "):
                font_tag = "/F4"  # Oblique
                font_size = 10
                line_height = 14
                display_text = "  | " + line[2:].strip()
            elif line.startswith("- ") or line.startswith("* "):
                font_tag = "/F1"  # Regular
                font_size = 11
                line_height = 15
                display_text = "  • " + line[2:].strip()
            else:
                font_tag = "/F1"  # Regular
                font_size = 11
                line_height = 15
                display_text = line

            # 改ページ判定
            if current_y - line_height < margin_bottom:
                pages_content.append(current_page)
                current_page = []
                current_y = height - margin_top

            current_page.append((font_tag, font_size, display_text))
            current_y -= line_height

        if current_page or not pages_content:
            pages_content.append(current_page)

        # PDF オブジェクトの構築
        objects: List[bytes] = []
        # 1: Catalog
        # 2: Pages
        # 3: Font F1 (Helvetica)
        # 4: Font F2 (Helvetica-Bold)
        # 5: Font F3 (Courier)
        # 6: Font F4 (Helvetica-Oblique)

        num_pages = len(pages_content)
        # ページオブジェクトの番号は 7 + i * 2, コンテンツストリームは 8 + i * 2
        page_obj_ids = [7 + i * 2 for i in range(num_pages)]

        # Object 1: Catalog
        catalog_obj = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        objects.append(catalog_obj)

        # Object 2: Pages
        kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
        pages_obj = f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>\nendobj\n".encode("utf-8")
        objects.append(pages_obj)

        # Object 3-6: Fonts
        f1_obj = b"3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        f2_obj = b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n"
        f3_obj = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n"
        f4_obj = b"6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>\nendobj\n"
        objects.extend([f1_obj, f2_obj, f3_obj, f4_obj])

        for i, p_items in enumerate(pages_content):
            page_id = 7 + i * 2
            content_id = 8 + i * 2

            # Page Object
            p_obj = (
                f"{page_id} 0 obj\n"
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.2f} {height:.2f}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R /F4 6 0 R >> >> "
                f"/Contents {content_id} 0 R >>\nendobj\n"
            ).encode("utf-8")
            objects.append(p_obj)

            # Stream Content
            stream_cmds = ["BT"]
            c_y = height - margin_top
            for f_tag, f_size, text in p_items:
                esc_text = cls._escape_pdf_string(text)
                stream_cmds.append(f"{f_tag} {f_size} Tf")
                stream_cmds.append(f"1 0 0 1 {margin_left:.2f} {c_y:.2f} Tm")
                stream_cmds.append(f"({esc_text}) Tj")
                # 行送り
                lh = 24 if f_size >= 18 else (20 if f_size >= 14 else (16 if f_size >= 12 else 15))
                c_y -= lh
            stream_cmds.append("ET")

            stream_data = "\n".join(stream_cmds).encode("latin-1", errors="replace")
            stream_obj = (
                f"{content_id} 0 obj\n<< /Length {len(stream_data)} >>\nstream\n"
            ).encode("utf-8") + stream_data + b"\nendstream\nendobj\n"
            objects.append(stream_obj)

        # PDFファイルのシリアライズとxref作成
        out = io.BytesIO()
        out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        offsets = []
        for obj in objects:
            offsets.append(out.tell())
            out.write(obj)

        startxref = out.tell()
        total_objects = len(objects) + 1  # 0番含む

        out.write(f"xref\n0 {total_objects}\n".encode("utf-8"))
        out.write(b"0000000000 65535 f \n")
        for offset in offsets:
            out.write(f"{offset:010d} 00000 n \n".encode("utf-8"))

        trailer = (
            f"trailer\n<< /Size {total_objects} /Root 1 0 R >>\n"
            f"startxref\n{startxref}\n%%EOF\n"
        ).encode("utf-8")
        out.write(trailer)

        return out.getvalue()


class ExportService:
    """
    ドキュメントエクスポートサービス (API-0301).
    
    Markdownから共通CSSを適用したHTMLおよびPDFバイナリを生成する.
    """

    @classmethod
    def build_html_document(
        cls,
        html_body: str,
        title: str = "Document",
        paper_size: str = "A4",
    ) -> str:
        """BR-0301-1 に基づく画面共通CSSを埋め込んだ完全なHTML文書を構築する."""
        page_size_css = f"@page {{ size: {paper_size}; margin: 20mm; }}"
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <style>
    {page_size_css}
    {COMMON_EXPORT_CSS}
  </style>
</head>
<body>
  <main class="markdown-body">
    {html_body}
  </main>
</body>
</html>
"""

    @classmethod
    def export_html(cls, markdown_content: str) -> bytes:
        """Markdown本文をHTML文書バイナリ (UTF-8) としてエクスポートする."""
        html_body = MarkdownRenderer.render(markdown_content)
        full_html = cls.build_html_document(html_body=html_body, title="Exported Document")
        return full_html.encode("utf-8")

    @classmethod
    def export_pdf(cls, markdown_content: str, paper_size: str = "A4") -> bytes:
        """
        Markdown本文をPDFバイナリとしてエクスポートする.
        
        WeasyPrint利用可能時はWeasyPrintを使用し、未導入環境ではPurePythonフォールバックを使用する.
        失敗時は E-0301-001 (PdfExportFailedException) をスローする.
        """
        try:
            # WeasyPrint が利用可能であれば優先して使用
            try:
                from weasyprint import HTML  # type: ignore
                html_body = MarkdownRenderer.render(markdown_content)
                full_html = cls.build_html_document(
                    html_body=html_body,
                    title="Exported Document",
                    paper_size=paper_size,
                )
                pdf_bytes = HTML(string=full_html).write_pdf()
                if isinstance(pdf_bytes, bytes) and len(pdf_bytes) > 0:
                    return pdf_bytes
            except ImportError:
                pass

            # Pure Python フォールバック生成
            return PurePdfGenerator.generate(
                markdown_text=markdown_content,
                paper_size=paper_size,
            )
        except Exception as e:
            raise PdfExportFailedException(
                details=[{"msg": f"Failed to generate PDF: {str(e)}"}]
            ) from e
