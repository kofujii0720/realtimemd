from fastapi import APIRouter, Depends, Path, status

from app.core.errors import DocumentDetailNotFoundException, SystemErrorException
from app.repositories.document_repository import (
    DocumentRepositoryProtocol,
    SqliteDocumentRepository,
)
from app.schemas.document import DocumentResponse, ErrorResponse
from app.usecases.get_document_detail import GetDocumentDetailUseCase

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_repository() -> DocumentRepositoryProtocol:
    """リポジトリインスタンスの依存性注入."""
    return SqliteDocumentRepository()


def get_get_document_detail_usecase(
    repo: DocumentRepositoryProtocol = Depends(get_document_repository),
) -> GetDocumentDetailUseCase:
    """ユースケースインスタンスの依存性注入."""
    return GetDocumentDetailUseCase(repository=repo)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="ドキュメント詳細取得API",
    description="指定したドキュメントIDの詳細データ（ID, タイトル, 本文, 作成日時, 最終更新日時）を取得する。",
    responses={
        status.HTTP_200_OK: {
            "model": DocumentResponse,
            "description": "ドキュメント詳細取得成功",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "対象ドキュメントが存在しない (E-0105-001)",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "内部エラー (E-0105-999)",
        },
    },
)
async def get_document_detail(
    document_id: str = Path(..., description="取得対象ドキュメントID (UUID)"),
    usecase: GetDocumentDetailUseCase = Depends(get_get_document_detail_usecase),
) -> DocumentResponse:
    """
    API-0105 ドキュメント詳細取得エンドポイント.

    指定された document_id に対応するドキュメントの詳細データを返却する.
    """
    return usecase.execute(document_id=document_id)
