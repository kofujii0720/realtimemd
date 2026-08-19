import { useState, useEffect, useCallback, useRef } from 'react';
import type { DocumentHeader, DocumentDetail } from '../types/document';
import {
  getDocumentList,
  createDocument,
  updateDocument,
  deleteDocument,
  ApiError,
} from '../api/documents';
import { getMessage } from '../utils/messages';

export type ScreenState = 'loading' | 'empty' | 'normal' | 'error';

export interface UseDocumentsResult {
  documents: DocumentHeader[];
  selectedDoc: DocumentDetail | null;
  state: ScreenState;
  errorMessage: string | null;
  infoMessage: string | null;
  isSaving: boolean;
  selectDocument: (id: string) => void;
  handleCreateDocument: () => Promise<void>;
  handleSaveDocument: (isExplicit?: boolean) => Promise<boolean>;
  handleDeleteDocument: () => Promise<void>;
  updateTitle: (newTitle: string) => void;
  updateContent: (newContent: string) => void;
  clearError: () => void;
}

export function useDocuments(): UseDocumentsResult {
  const [documents, setDocuments] = useState<DocumentHeader[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentDetail | null>(null);
  const [state, setState] = useState<ScreenState>('loading');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // コンテンツキャッシュ (API-0101はメタデータのみのため)
  const contentCacheRef = useRef<Map<string, DocumentDetail>>(new Map());

  const clearError = useCallback(() => {
    setErrorMessage(null);
  }, []);

  // 初期ドキュメント一覧ロード
  const loadDocuments = useCallback(async () => {
    setState('loading');
    setErrorMessage(null);
    try {
      const data = await getDocumentList();
      setDocuments(data.items);

      if (data.items.length === 0) {
        setSelectedDoc(null);
        setState('empty');
      } else {
        const firstDoc = data.items[0];
        if (firstDoc) {
          const cached = contentCacheRef.current.get(firstDoc.id);
          if (cached) {
            setSelectedDoc(cached);
          } else {
            const initialDetail: DocumentDetail = {
              id: firstDoc.id,
              title: firstDoc.title,
              content: '',
              created_at: firstDoc.updated_at,
              updated_at: firstDoc.updated_at,
            };
            contentCacheRef.current.set(firstDoc.id, initialDetail);
            setSelectedDoc(initialDetail);
          }
        }
        setState('normal');
      }
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : getMessage('error.common.systemError');
      setErrorMessage(msg);
      setState('error');
    }
  }, []);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  // ドキュメント選択
  const selectDocument = useCallback(
    (id: string) => {
      const docHeader = documents.find((d) => d.id === id);
      if (!docHeader) return;

      const cached = contentCacheRef.current.get(id);
      if (cached) {
        setSelectedDoc(cached);
      } else {
        const newDetail: DocumentDetail = {
          id: docHeader.id,
          title: docHeader.title,
          content: '',
          created_at: docHeader.updated_at,
          updated_at: docHeader.updated_at,
        };
        contentCacheRef.current.set(id, newDetail);
        setSelectedDoc(newDetail);
      }
      setErrorMessage(null);
    },
    [documents]
  );

  // タイトル更新（ローカルステート）
  const updateTitle = useCallback((newTitle: string) => {
    setSelectedDoc((prev) => {
      if (!prev) return null;
      const updated = { ...prev, title: newTitle };
      contentCacheRef.current.set(prev.id, updated);
      return updated;
    });
  }, []);

  // 本文更新（ローカルステート）
  const updateContent = useCallback((newContent: string) => {
    setSelectedDoc((prev) => {
      if (!prev) return null;
      const updated = { ...prev, content: newContent };
      contentCacheRef.current.set(prev.id, updated);
      return updated;
    });
  }, []);

  // 新規ドキュメント作成 (API-0102)
  const handleCreateDocument = useCallback(async () => {
    setErrorMessage(null);
    try {
      const created = await createDocument({
        title: '無題のドキュメント',
        content: '',
      });

      const newHeader: DocumentHeader = {
        id: created.id,
        title: created.title,
        updated_at: created.updated_at,
      };

      contentCacheRef.current.set(created.id, created);
      setDocuments((prev) => [newHeader, ...prev]);
      setSelectedDoc(created);
      setState('normal');
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : getMessage('error.common.systemError');
      setErrorMessage(msg);
    }
  }, []);

  // ドキュメント保存 (API-0103)
  const handleSaveDocument = useCallback(
    async (isExplicit = true): Promise<boolean> => {
      if (!selectedDoc) return false;

      // バリデーション
      if (!selectedDoc.title || selectedDoc.title.trim() === '') {
        setErrorMessage(getMessage('error.document.titleRequired'));
        return false;
      }

      const contentBytes = new Blob([selectedDoc.content]).size;
      if (contentBytes > 2 * 1024 * 1024) {
        setErrorMessage(getMessage('error.document.sizeExceeded'));
        return false;
      }

      setIsSaving(true);
      setErrorMessage(null);
      try {
        const updated = await updateDocument(selectedDoc.id, {
          title: selectedDoc.title,
          content: selectedDoc.content,
          is_explicit_save: isExplicit,
        });

        const updatedDetail: DocumentDetail = {
          id: updated.id,
          title: updated.title,
          content: updated.content,
          created_at: selectedDoc.created_at,
          updated_at: updated.updated_at,
        };

        contentCacheRef.current.set(updated.id, updatedDetail);
        setSelectedDoc(updatedDetail);

        // 一覧のヘッダーも更新
        setDocuments((prev) =>
          prev.map((d) =>
            d.id === updated.id
              ? { ...d, title: updated.title, updated_at: updated.updated_at }
              : d
          )
        );

        const infoKey = isExplicit ? 'info.document.saved' : 'info.document.autoSaved';
        setInfoMessage(getMessage(infoKey));

        setTimeout(() => {
          setInfoMessage(null);
        }, 3000);

        return true;
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : getMessage('error.common.systemError');
        setErrorMessage(msg);
        return false;
      } finally {
        setIsSaving(false);
      }
    },
    [selectedDoc]
  );

  // ドキュメント削除 (API-0104)
  const handleDeleteDocument = useCallback(async () => {
    if (!selectedDoc) return;
    setErrorMessage(null);

    try {
      await deleteDocument(selectedDoc.id);
      contentCacheRef.current.delete(selectedDoc.id);

      const nextDocs = documents.filter((d) => d.id !== selectedDoc.id);
      setDocuments(nextDocs);

      if (nextDocs.length === 0) {
        setSelectedDoc(null);
        setState('empty');
      } else {
        const nextSelected = nextDocs[0];
        if (nextSelected) {
          const cached = contentCacheRef.current.get(nextSelected.id);
          if (cached) {
            setSelectedDoc(cached);
          } else {
            const detail: DocumentDetail = {
              id: nextSelected.id,
              title: nextSelected.title,
              content: '',
              created_at: nextSelected.updated_at,
              updated_at: nextSelected.updated_at,
            };
            contentCacheRef.current.set(nextSelected.id, detail);
            setSelectedDoc(detail);
          }
        }
        setState('normal');
      }
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : getMessage('error.common.systemError');
      setErrorMessage(msg);
    }
  }, [selectedDoc, documents]);

  return {
    documents,
    selectedDoc,
    state,
    errorMessage,
    infoMessage,
    isSaving,
    selectDocument,
    handleCreateDocument,
    handleSaveDocument,
    handleDeleteDocument,
    updateTitle,
    updateContent,
    clearError,
  };
}
