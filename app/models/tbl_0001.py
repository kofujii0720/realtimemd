from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentModel:
    """TBL-0001 ドキュメントテーブル対応データモデル."""

    id: str
    title: str
    content: str
    created_at: str
    updated_at: str
