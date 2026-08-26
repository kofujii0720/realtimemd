from fastapi import APIRouter, Depends, Response, status

from app.schemas.document import ErrorResponse
from app.schemas.export import ExportRequest
from app.usecases.export_document import ExportDocumentUseCase

router = APIRouter(prefix="/export", tags=["export"])


def get_export_document_usecase() -> ExportDocumentUseCase:
    """ユースケースインスタンスの依存性注入."""
    return ExportDocumentUseCase()


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="ドキュメントエクスポートAPI",
    description="Markdown本文および出力オプション（PDF/HTML、用紙サイズ等）を受け取り、高精度なPDFバイナリまたはHTMLファイルを生成・返却する。",
    responses={
        status.HTTP_200_OK: {
            "description": "エクスポートファイルバイナリ (application/pdf または text/html)",
            "content": {
                "application/pdf": {},
                "text/html": {},
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "不正な出力フォーマット指定 (E-0301-002)",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "PDF生成処理失敗 (E-0301-001) / 内部エラー (E-0301-999)",
        },
    },
)
async def export_document(
    request: ExportRequest,
    usecase: ExportDocumentUseCase = Depends(get_export_document_usecase),
) -> Response:
    """
    API-0301 ドキュメントエクスポートエンドポイント.
    
    Markdown文字列およびフォーマット・用紙サイズ指定を受け取り、PDFまたはHTMLのバイナリストリームを返却する.
    """
    data, media_type, filename = usecase.execute(request=request)
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
