from fastapi import APIRouter, Depends, status

from app.schemas.document import ErrorResponse
from app.schemas.preview import (
    PreviewRenderRequest,
    PreviewRenderResponse,
)
from app.usecases.render_preview import RenderPreviewUseCase

router = APIRouter(prefix="/preview", tags=["preview"])


def get_render_preview_usecase() -> RenderPreviewUseCase:
    """ユースケースインスタンスの依存性注入."""
    return RenderPreviewUseCase()


@router.post(
    "/render",
    response_model=PreviewRenderResponse,
    status_code=status.HTTP_200_OK,
    summary="プレビューレンダリング補助API",
    description="サーバー側でのMarkdown/HTML解析・検証を行い、変換後の安全なHTML文字列を返却する。",
    responses={
        status.HTTP_200_OK: {
            "model": PreviewRenderResponse,
            "description": "Markdownレンダリング成功",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "入力サイズ制限(2MB)超過 (E-0201-001)",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "内部エラー (E-0201-999)",
        },
    },
)
async def render_preview(
    request: PreviewRenderRequest,
    usecase: RenderPreviewUseCase = Depends(get_render_preview_usecase),
) -> PreviewRenderResponse:
    """
    API-0201 プレビューレンダリング補助エンドポイント.
    
    Markdown文字列を受け取り、安全なHTML文字列へ変換して返却する.
    """
    return usecase.execute(request=request)
