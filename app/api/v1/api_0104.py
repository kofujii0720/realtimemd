from fastapi import APIRouter, Depends, Path, Response, status

from app.core.errors import (
    AppException,
    DocumentDeleteNotFoundException,
    SystemErrorException,
)
from app.core.messages import MessageKeys
from app.repositories.document_repository import (
    DocumentRepositoryProtocol,
    SqliteDocumentRepository,
)
from app.schemas.document import ErrorResponse
from app.usecases.delete_document import DeleteDocumentUseCase

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_repository() -> DocumentRepositoryProtocol:
    """リポジトリインスタンスの依存性注入."""
    return SqliteDocumentRepository()


def get_delete_document_usecase(
    repo: DocumentRepositoryProtocol = Depends(get_document_repository),
) -> DeleteDocumentUseCase:
    """ユースケースインスタンスの依存性注入."""
    return DeleteDocumentUseCase(repository=repo)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="ドキュメント削除API",
    description="指定したドキュメントおよび関連する変更履歴データをデータベースから削除する。",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "ドキュメント削除成功（レスポンスボディなし）",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "対象ドキュメントが存在しない (E-0104-001)",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "内部エラー (E-0104-999)",
        },
    },
)
async def delete_document(
    document_id: str = Path(..., description="削除対象ドキュメントID (UUID)"),
    usecase: DeleteDocumentUseCase = Depends(get_delete_document_usecase),
) -> Response:
    """
    API-0104 ドキュメント削除エンドポイント.

    指定された document_id に対応するドキュメントおよび関連する変更履歴を削除し、204 No Content を返却する.
    """
    usecase.execute(document_id=document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
