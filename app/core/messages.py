from typing import Final


class MessageKeys:
    """MSG-0001 メッセージ辞書のキー定義正本."""

    # エラー
    ERROR_DOC_NOT_FOUND: Final[str] = "error.document.notFound"
    ERROR_DOC_SIZE_EXCEEDED: Final[str] = "error.document.sizeExceeded"
    ERROR_DOC_TITLE_REQUIRED: Final[str] = "error.document.titleRequired"
    ERROR_EXPORT_PDF_FAILED: Final[str] = "error.export.pdfFailed"
    ERROR_COMMON_SYSTEM_ERROR: Final[str] = "error.common.systemError"

    # 通知・情報
    INFO_DOC_SAVED: Final[str] = "info.document.saved"
    INFO_DOC_AUTOSAVED: Final[str] = "info.document.autoSaved"

    # ラベル
    LABEL_STATUS_EMPTY: Final[str] = "label.status.empty"
