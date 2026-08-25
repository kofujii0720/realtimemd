from typing import List, Tuple
from fastapi import APIRouter, Depends, status

from app.core.errors import AppException
from app.core.messages import MessageKeys
from app.repositories.document_repository import (
    DocumentRepositoryProtocol,
    SqliteDocumentRepository,
)
from app.schemas.document import (
    DocumentHeader,
    DocumentListQueryParams,
    DocumentListResponse,
    ErrorResponse,
)
from app.usecases.list_documents import ListDocumentsUseCase

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_repository() -> DocumentRepositoryProtocol:
    """リポジトリインスタンスの依存性注入."""
    return SqliteDocumentRepository()


def get_list_documents_usecase(
    repo: DocumentRepositoryProtocol = Depends(get_document_repository),
) -> ListDocumentsUseCase:
    """ユースケースインスタンスの依存性注入."""
    return ListDocumentsUseCase(repository=repo)


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="ドキュメント一覧取得API",
    description="登録されている全ドキュメントのメタデータ一覧（ID, タイトル, 更新日時）を更新日時降順で取得する。",
    responses={
        status.HTTP_200_OK: {
            "model": DocumentListResponse,
            "description": "ドキュメント一覧取得成功",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "クエリパラメータ制約違反 (E-0101-001)",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "内部エラー (E-0101-999)",
        },
    },
)
async def list_documents(
    params: DocumentListQueryParams = Depends(),
    usecase: ListDocumentsUseCase = Depends(get_list_documents_usecase),
) -> DocumentListResponse:
    """
    API-0101 ドキュメント一覧取得エンドポイント.

    登録されているドキュメントのメタデータ一覧を更新日時降順で返却する.
    """
    return usecase.execute(limit=params.limit, offset=params.offset)
