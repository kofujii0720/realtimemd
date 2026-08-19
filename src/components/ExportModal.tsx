import React from 'react';
import styles from './ExportModal.module.css';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentTitle: string;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  documentTitle,
}) => {
  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div
        className={styles.modal}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="export-modal-title"
      >
        <div className={styles.modalHeader}>
          <h3 id="export-modal-title" className={styles.modalTitle}>
            ドキュメントのエクスポート
          </h3>
          <button
            type="button"
            className={styles.closeBtn}
            onClick={onClose}
            aria-label="閉じる"
          >
            ×
          </button>
        </div>
        <div className={styles.modalBody}>
          <p className={styles.targetDoc}>
            対象: <strong>{documentTitle || '無題のドキュメント'}</strong>
          </p>
          <div className={styles.exportOptions}>
            <button
              type="button"
              className={styles.optionBtn}
              onClick={() => {
                alert('PDFエクスポート (SCR-0301)');
                onClose();
              }}
            >
              📄 PDFとしてエクスポート
            </button>
            <button
              type="button"
              className={styles.optionBtn}
              onClick={() => {
                alert('HTMLエクスポート (SCR-0301)');
                onClose();
              }}
            >
              🌐 HTMLとしてエクスポート
            </button>
          </div>
        </div>
        <div className={styles.modalFooter}>
          <button type="button" className={styles.cancelBtn} onClick={onClose}>
            キャンセル
          </button>
        </div>
      </div>
    </div>
  );
};
