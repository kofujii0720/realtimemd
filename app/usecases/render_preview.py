from app.core.errors import PreviewRenderSizeExceededException
from app.schemas.document import MAX_CONTENT_BYTES
from app.schemas.preview import PreviewRenderRequest, PreviewRenderResponse
from app.services.markdown_renderer import MarkdownRenderer


class RenderPreviewUseCase:
    """API-0201 プレビューレンダリング補助ユースケース."""

    def __init__(self, renderer: MarkdownRenderer = MarkdownRenderer) -> None:
        self.renderer = renderer

    def execute(self, request: PreviewRenderRequest) -> PreviewRenderResponse:
        """
        Markdownテキストをパースし、安全なHTML文字列へ変換する.
        
        制約・規約:
        - 事前条件: 特になし (API-0201 3. 事前条件)
        - 事後条件: DB状態変更なし (API-0201 3. 事後条件)
        - 不変条件: 特になし (API-0201 3. 不変条件)
        - 副作用: なし (API-0201 4. 副作用)
        - べき等性: あり (API-0201 5. 非機能制約)
        """
        content = request.content

        # 改行コード正規化 (REQ-0003: \r\n -> \n)
        normalized_content = content.replace("\r\n", "\n")

        # 本文サイズバリデーション (最大2MB)
        if len(normalized_content.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise PreviewRenderSizeExceededException(
                details=[{"msg": f"Content size exceeds maximum of {MAX_CONTENT_BYTES} bytes."}]
            )

        # MarkdownからHTMLへの安全なレンダリング
        html_content = self.renderer.render(normalized_content)

        return PreviewRenderResponse(html_content=html_content)
