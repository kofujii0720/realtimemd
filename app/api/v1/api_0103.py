from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Path, status

from app.core.errors import (
    DocumentNotFoundException,
    DocumentUpdateSizeExceededException,
    DocumentUpdateTitleRequiredException,
    SystemErrorException,
)
from app.repositories.document_repository import (
    DocumentRepositoryProtocol,
    SqliteDocumentRepository,
)
from app.schemas.document import (
    DocumentUpdateRequest,
    DocumentUpdateResponse,
    ErrorResponse,
)
from app.usecases.update_document import UpdateDocumentUseCase

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_repository() -> DocumentRepositoryProtocol:
    """リポジトリインスタンスの依存性注入."""
    return SqliteDocumentRepository()


def get_update_document_usecase(
    repo: DocumentRepositoryProtocol = Depends(get_document_repository),
) -> UpdateDocumentUseCase:
    """ユースケースインスタンスの依存性注入."""
    return UpdateDocumentUseCase(repository=repo)


@router.put(
    "/{document_id}",
    response_model=DocumentUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="ドキュメント更新API",
    description="指定したドキュメントのタイトル・本文を更新する。明示保存フラグ (is_explicit_save=true) 時は変更履歴 (TBL-0002) にレコードを追加する。",
    responses={
        status.HTTP_200_OK: {
            "model": DocumentUpdateResponse,
            "description": "ドキュメント更新成功",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "バリデーションエラー (E-0103-002: 本文サイズ制限超過, E-0103-003: タイトル未入力・空)",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "ドキュメント未検出 (E-0103-001)",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "内部エラー (E-0103-999)",
        },
    },
)
async def update_document(
    document_id: str = Path(..., description="ドキュメントID (UUID)"),
    request: DocumentUpdateRequest = ...,
    usecase: UpdateDocumentUseCase = Depends(get_update_document_usecase),
) -> DocumentUpdateResponse:
    """
    API-0103 ドキュメント更新エンドポイント.
    
    ルーター層で現在時刻を取得し、ユースケース層へ引数 now として渡す.
    """
    now = datetime.now(timezone.utc)
    return usecase.execute(document_id=document_id, request=request, now=now)
