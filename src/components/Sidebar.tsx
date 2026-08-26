import React from 'react';
import type { DocumentHeader } from '../types/document';
import { LoadingSpinner } from './LoadingSpinner';
import { getMessage } from '../utils/messages';
import styles from './Sidebar.module.css';

interface SidebarProps {
  documents: DocumentHeader[];
  selectedDocId?: string;
  isLoading: boolean;
  onSelectDocument: (id: string) => void;
  onCreateDocument: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  documents,
  selectedDocId,
  isLoading,
  onSelectDocument,
  onCreateDocument,
}) => {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.sidebarHeader}>
        <h2 className={styles.logoTitle}>Realtime Markdown</h2>
        <button
          type="button"
          className={styles.createBtn}
          data-testid="btn-create-doc"
          onClick={onCreateDocument}
          title="新規ドキュメントを作成"
        >
          ＋ 新規作成
        </button>
      </div>

      <div className={styles.listContainer} data-testid="doc-list">
        {isLoading ? (
          <LoadingSpinner />
        ) : documents.length === 0 ? (
          <div className={styles.emptyState}>
            <p className={styles.emptyText}>{getMessage('label.status.empty')}</p>
            <button
              type="button"
              className={styles.emptyCreateBtn}
              onClick={onCreateDocument}
            >
              ＋ 新しいドキュメントを作成
            </button>
          </div>
        ) : (
          <ul className={styles.docList}>
            {documents.map((doc) => {
              const isSelected = doc.id === selectedDocId;
              return (
                <li
                  key={doc.id}
                  className={`${styles.docItem} ${isSelected ? styles.active : ''}`}
                  data-testid="doc-item"
                  onClick={() => onSelectDocument(doc.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      onSelectDocument(doc.id);
                    }
                  }}
                >
                  <div className={styles.docTitle}>{doc.title || '無題のドキュメント'}</div>
                  <div className={styles.docDate}>
                    {new Date(doc.updated_at).toLocaleString('ja-JP')}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
};
