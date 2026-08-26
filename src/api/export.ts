import type { ExportRequest } from '../types/export';
import { ApiError } from './documents';
import { getMessage } from '../utils/messages';

export interface ExportResult {
  blob: Blob;
  filename: string;
  mediaType: string;
}

/**
 * ドキュメントエクスポートAPI (API-0301)
 */
export async function exportDocumentApi(req: ExportRequest): Promise<ExportResult> {
  const contentBytes = new Blob([req.content]).size;
  if (contentBytes > 2 * 1024 * 1024) {
    throw new ApiError(getMessage('error.document.sizeExceeded'), 400, 'error.document.sizeExceeded');
  }

  try {
    const res = await fetch('/api/v1/export', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: req.content,
        format: req.format,
        paper_size: req.format === 'pdf' ? (req.paper_size ?? 'A4') : undefined,
      }),
    });

    if (!res.ok) {
      let errorData: unknown;
      try {
        errorData = await res.json();
      } catch {
        errorData = null;
      }

      let messageKey: string | undefined;
      let code: string | undefined;
      let messageText: string | undefined;

      if (errorData && typeof errorData === 'object') {
        const errObj = errorData as Record<string, unknown>;
        if (typeof errObj.message_key === 'string') {
          messageKey = errObj.message_key;
        } else if (typeof errObj.detail === 'object' && errObj.detail !== null) {
          const detailObj = errObj.detail as Record<string, unknown>;
          if (typeof detailObj.message_key === 'string') {
            messageKey = detailObj.message_key;
          }
          if (typeof detailObj.code === 'string') {
            code = detailObj.code;
          }
          if (typeof detailObj.message === 'string') {
            messageText = detailObj.message;
          }
        } else if (typeof errObj.detail === 'string') {
          messageText = errObj.detail;
        }
        if (typeof errObj.code === 'string') {
          code = errObj.code;
        }
      }

      const defaultMsg =
        req.format === 'pdf'
          ? getMessage('error.export.pdfFailed')
          : getMessage('error.common.systemError');
      const resolvedMessage = messageKey
        ? getMessage(messageKey, defaultMsg)
        : (messageText ?? defaultMsg);
      throw new ApiError(resolvedMessage, res.status, messageKey, code);
    }

    const blob = await res.blob();
    const disposition = res.headers.get('Content-Disposition') || '';
    let filename = `document.${req.format}`;
    const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
    if (filenameMatch && filenameMatch[1]) {
      filename = filenameMatch[1];
    }

    return {
      blob,
      filename,
      mediaType: req.format === 'pdf' ? 'application/pdf' : 'text/html',
    };
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      getMessage(req.format === 'pdf' ? 'error.export.pdfFailed' : 'error.common.systemError'),
      500,
      req.format === 'pdf' ? 'error.export.pdfFailed' : 'error.common.systemError'
    );
  }
}

/**
 * Blobデータをブラウザからダウンロードさせるユーティリティ
 */
export function triggerFileDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
