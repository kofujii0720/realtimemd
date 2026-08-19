from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentHistoryModel:
    """TBL-0002 ドキュメント変更履歴テーブル対応データモデル."""

    id: str
    document_id: str
    version_no: int
    content: str
    saved_at: str
