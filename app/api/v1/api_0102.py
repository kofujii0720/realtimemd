from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status

from app.core.errors import DocumentSizeExceededException, DocumentTitleRequiredException, SystemErrorException
from app.repositories.document_repository import (
    DocumentRepositoryProtocol,
    SqliteDocumentRepository,
)
from app.schemas.document import (
    DocumentCreateRequest,
    DocumentResponse,
    ErrorResponse,
)
from app.usecases.create_document import CreateDocumentUseCase

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_repository() -> DocumentRepositoryProtocol:
    """リポジトリインスタンスの依存性注入."""
    return SqliteDocumentRepository()


def get_create_document_usecase(
    repo: DocumentRepositoryProtocol = Depends(get_document_repository),
) -> CreateDocumentUseCase:
    """ユースケースインスタンスの依存性注入."""
    return CreateDocumentUseCase(repository=repo)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ドキュメント新規作成API",
    description="新しい空のMarkdownドキュメントレコードを作成し、初期化されたドキュメント情報を返却する。",
    responses={
        status.HTTP_201_CREATED: {
            "model": DocumentResponse,
            "description": "ドキュメント新規作成成功",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "バリデーションエラー (E-0102-001: 本文サイズ超過, E-0102-002: タイトル文字数超過)",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "内部エラー (E-0102-999)",
        },
    },
)
async def create_document(
    request: DocumentCreateRequest = DocumentCreateRequest(),
    usecase: CreateDocumentUseCase = Depends(get_create_document_usecase),
) -> DocumentResponse:
    """
    API-0102 ドキュメント新規作成エンドポイント.
    
    ルーター層で現在時刻を取得し、ユースケース層へ引数 now として渡す.
    """
    # ルーター層で現在時刻を生成してユースケースへ渡す
    now = datetime.now(timezone.utc)
    return usecase.execute(request=request, now=now)
