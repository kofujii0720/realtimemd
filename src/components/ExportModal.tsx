import React from 'react';
import type { ExportFormat, PaperSize, MarginOption, ExportOptions } from '../types/export';
import { useExport } from '../hooks/useExport';
import styles from './ExportModal.module.css';

export interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentTitle: string;
  documentContent?: string;
  initialOptions?: Partial<ExportOptions>;
  onSuccess?: () => void;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  documentTitle,
  documentContent = '',
  initialOptions,
  onSuccess,
}) => {
  const {
    format,
    setFormat,
    paperSize,
    setPaperSize,
    margin,
    setMargin,
    isLoading,
    errorMessage,
    handleExport,
  } = useExport({
    isOpen,
    content: documentContent,
    documentTitle,
    initialOptions,
    onClose,
    onSuccess,
  });

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
            disabled={isLoading}
          >
            ×
          </button>
        </div>

        <div className={styles.modalBody}>
          {errorMessage && (
            <div
              className={styles.errorAlert}
              role="alert"
              data-testid="export-error-alert"
            >
              <span className={styles.errorIcon}>⚠️</span>
              <span className={styles.errorMessage}>{errorMessage}</span>
            </div>
          )}

          <p className={styles.targetDoc}>
            対象ドキュメント: <strong>{documentTitle || '無題のドキュメント'}</strong>
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              void handleExport();
            }}
          >
            {/* 出力フォーマット (SCR-0301) */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>出力フォーマット</label>
              <div
                className={styles.radioGroup}
                data-testid="export-format-radio"
                role="radiogroup"
                aria-label="出力フォーマット"
              >
                <label className={`${styles.radioLabel} ${format === 'pdf' ? styles.radioSelected : ''}`}>
                  <input
                    type="radio"
                    name="export-format"
                    value="pdf"
                    checked={format === 'pdf'}
                    onChange={(e) => setFormat(e.target.value as ExportFormat)}
                    disabled={isLoading}
                    className={styles.radioInput}
                    data-testid="export-format-pdf"
                  />
                  <span>📄 PDF</span>
                </label>
                <label className={`${styles.radioLabel} ${format === 'html' ? styles.radioSelected : ''}`}>
                  <input
                    type="radio"
                    name="export-format"
                    value="html"
                    checked={format === 'html'}
                    onChange={(e) => setFormat(e.target.value as ExportFormat)}
                    disabled={isLoading}
                    className={styles.radioInput}
                    data-testid="export-format-html"
                  />
                  <span>🌐 HTML</span>
                </label>
              </div>
            </div>

            {/* 用紙サイズ (PDF選択時のみ表示) (SCR-0301) */}
            {format === 'pdf' && (
              <div className={styles.formGroup}>
                <label htmlFor="export-paper-select" className={styles.formLabel}>
                  用紙サイズ
                </label>
                <select
                  id="export-paper-select"
                  className={styles.selectInput}
                  data-testid="export-paper-select"
                  value={paperSize}
                  onChange={(e) => setPaperSize(e.target.value as PaperSize)}
                  disabled={isLoading}
                >
                  <option value="A4">A4 (210 × 297 mm)</option>
                  <option value="Letter">Letter (8.5 × 11 in)</option>
                </select>
              </div>
            )}

            {/* マージン設定 */}
            <div className={styles.formGroup}>
              <label htmlFor="export-margin-select" className={styles.formLabel}>
                余白 (マージン)
              </label>
              <select
                id="export-margin-select"
                className={styles.selectInput}
                data-testid="export-margin-select"
                value={margin}
                onChange={(e) => setMargin(e.target.value as MarginOption)}
                disabled={isLoading}
              >
                <option value="normal">標準</option>
                <option value="narrow">狭い</option>
                <option value="none">なし</option>
              </select>
            </div>

            <div className={styles.modalFooter}>
              <button
                type="button"
                className={styles.cancelBtn}
                data-testid="btn-cancel-export"
                onClick={onClose}
                disabled={isLoading}
              >
                キャンセル
              </button>

              <button
                type="submit"
                className={styles.submitBtn}
                data-testid="btn-submit-export"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span
                    className={styles.loadingSpinner}
                    data-testid="export-processing-spinner"
                  >
                    <span className={styles.spinnerIcon} aria-hidden="true" />
                    ダウンロード中...
                  </span>
                ) : (
                  'ダウンロード'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
