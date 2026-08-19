/**
 * ドキュメントヘッダー（一覧用）
 */
export interface DocumentHeader {
  id: string;
  title: string;
  updated_at: string;
}

/**
 * ドキュメント詳細
 */
export interface DocumentDetail {
  id: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

/**
 * ドキュメント一覧レスポンス (API-0101)
 */
export interface DocumentListResponse {
  total: number;
  items: DocumentHeader[];
}

/**
 * 新規作成リクエスト (API-0102)
 */
export interface CreateDocumentRequest {
  title?: string;
  content?: string;
}

/**
 * 新規作成レスポンス (API-0102)
 */
export interface CreateDocumentResponse {
  id: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

/**
 * 更新リクエスト (API-0103)
 */
export interface UpdateDocumentRequest {
  title: string;
  content: string;
  is_explicit_save?: boolean;
}

/**
 * 更新レスポンス (API-0103)
 */
export interface UpdateDocumentResponse {
  id: string;
  title: string;
  content: string;
  updated_at: string;
}

/**
 * プレビューレンダリングリクエスト (API-0201)
 */
export interface PreviewRenderRequest {
  content: string;
}

/**
 * プレビューレンダリングレスポンス (API-0201)
 */
export interface PreviewRenderResponse {
  html_content: string;
}

/**
 * APIエラー構造
 */
export interface ApiErrorDetail {
  code?: string;
  message?: string;
  message_key?: string;
  detail?: string | { code?: string; message_key?: string; message?: string };
}
