import React from 'react';
import styles from './Header.module.css';

interface HeaderProps {
  title: string;
  isSaving: boolean;
  hasSelectedDoc: boolean;
  infoMessage: string | null;
  onTitleChange: (newTitle: string) => void;
  onSave: () => void;
  onOpenExport: () => void;
  onDelete: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  isSaving,
  hasSelectedDoc,
  infoMessage,
  onTitleChange,
  onSave,
  onOpenExport,
  onDelete,
}) => {
  return (
    <header className={styles.header}>
      <div className={styles.titleContainer}>
        <input
          type="text"
          className={styles.titleInput}
          data-testid="doc-title-input"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder="無題のドキュメント"
          maxLength={255}
          disabled={!hasSelectedDoc}
          aria-label="ドキュメントタイトル"
        />
        {infoMessage && <span className={styles.infoBadge}>{infoMessage}</span>}
      </div>

      <div className={styles.actions}>
        <button
          type="button"
          className={`${styles.btn} ${styles.btnSave}`}
          data-testid="btn-save-doc"
          onClick={onSave}
          disabled={!hasSelectedDoc || isSaving}
          title="保存 (Ctrl+S / Cmd+S)"
        >
          {isSaving ? '保存中...' : '💾 保存'}
        </button>

        <button
          type="button"
          className={`${styles.btn} ${styles.btnExport}`}
          data-testid="btn-open-export"
          onClick={onOpenExport}
          disabled={!hasSelectedDoc}
          title="エクスポート"
        >
          📤 エクスポート
        </button>

        <button
          type="button"
          className={`${styles.btn} ${styles.btnDelete}`}
          data-testid="btn-delete-doc"
          onClick={onDelete}
          disabled={!hasSelectedDoc}
          title="ドキュメントを削除"
        >
          🗑️ 削除
        </button>
      </div>
    </header>
  );
};
