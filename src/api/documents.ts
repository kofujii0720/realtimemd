import type {
  DocumentDetail,
  DocumentListResponse,
  CreateDocumentRequest,
  CreateDocumentResponse,
  UpdateDocumentRequest,
  UpdateDocumentResponse,
  PreviewRenderRequest,
  PreviewRenderResponse,
} from '../types/document';
import { getMessage } from '../utils/messages';

export class ApiError extends Error {
  public code?: string;
  public messageKey?: string;
  public status: number;

  constructor(message: string, status: number, messageKey?: string, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.messageKey = messageKey;
    this.code = code;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
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

    const resolvedMessage = messageKey
      ? getMessage(messageKey, messageText ?? getMessage('error.common.systemError'))
      : (messageText ?? getMessage('error.common.systemError'));

    throw new ApiError(resolvedMessage, response.status, messageKey, code);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

/**
 * ドキュメント一覧取得 (API-0101)
 */
export async function getDocumentList(limit = 50, offset = 0): Promise<DocumentListResponse> {
  try {
    const res = await fetch(`/api/v1/documents?limit=${limit}&offset=${offset}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    return await handleResponse<DocumentListResponse>(res);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(getMessage('error.common.systemError'), 500, 'error.common.systemError');
  }
}

/**
 * ドキュメント詳細取得 (API-0105)
 */
export async function getDocumentDetail(id: string): Promise<DocumentDetail> {
  try {
    const res = await fetch(`/api/v1/documents/${encodeURIComponent(id)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    return await handleResponse<DocumentDetail>(res);
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 404) {
        throw new ApiError(
          getMessage('error.document.notFound'),
          404,
          'error.document.notFound',
          err.code ?? 'E-0105-001'
        );
      }
      throw err;
    }
    throw new ApiError(getMessage('error.common.systemError'), 500, 'error.common.systemError');
  }
}

/**
 * 新規ドキュメント作成 (API-0102)
 */
export async function createDocument(req: CreateDocumentRequest = {}): Promise<CreateDocumentResponse> {
  const contentBytes = new Blob([req.content ?? '']).size;
  if (contentBytes > 2 * 1024 * 1024) {
    throw new ApiError(getMessage('error.document.sizeExceeded'), 400, 'error.document.sizeExceeded');
  }
  if (req.title !== undefined && req.title.length > 255) {
    throw new ApiError(getMessage('error.document.titleRequired'), 400, 'error.document.titleRequired');
  }

  try {
    const res = await fetch('/api/v1/documents', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        title: req.title ?? '無題のドキュメント',
        content: req.content ?? '',
      }),
    });
    return await handleResponse<CreateDocumentResponse>(res);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(getMessage('error.common.systemError'), 500, 'error.common.systemError');
  }
}

/**
 * ドキュメント更新 (API-0103)
 */
export async function updateDocument(
  id: string,
  req: UpdateDocumentRequest
): Promise<UpdateDocumentResponse> {
  if (!req.title || req.title.trim() === '' || req.title.length > 255) {
    throw new ApiError(getMessage('error.document.titleRequired'), 400, 'error.document.titleRequired');
  }

  const contentBytes = new Blob([req.content]).size;
  if (contentBytes > 2 * 1024 * 1024) {
    throw new ApiError(getMessage('error.document.sizeExceeded'), 400, 'error.document.sizeExceeded');
  }

  try {
    const res = await fetch(`/api/v1/documents/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        title: req.title,
        content: req.content,
        is_explicit_save: req.is_explicit_save ?? false,
      }),
    });
    return await handleResponse<UpdateDocumentResponse>(res);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(getMessage('error.common.systemError'), 500, 'error.common.systemError');
  }
}

/**
 * ドキュメント削除 (API-0104)
 */
export async function deleteDocument(id: string): Promise<void> {
  try {
    const res = await fetch(`/api/v1/documents/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    });
    await handleResponse<void>(res);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(getMessage('error.common.systemError'), 500, 'error.common.systemError');
  }
}

/**
 * プレビューレンダリング補助 (API-0201)
 */
export async function renderPreviewApi(req: PreviewRenderRequest): Promise<PreviewRenderResponse> {
  const contentBytes = new Blob([req.content]).size;
  if (contentBytes > 2 * 1024 * 1024) {
    throw new ApiError(getMessage('error.document.sizeExceeded'), 400, 'error.document.sizeExceeded');
  }

  try {
    const res = await fetch('/api/v1/preview/render', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ content: req.content }),
    });
    return await handleResponse<PreviewRenderResponse>(res);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(getMessage('error.common.systemError'), 500, 'error.common.systemError');
  }
}
