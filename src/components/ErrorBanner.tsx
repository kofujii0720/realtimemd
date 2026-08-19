import React from 'react';
import styles from './ErrorBanner.module.css';

interface ErrorBannerProps {
  message: string;
  onClose?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ message, onClose }) => {
  if (!message) return null;

  return (
    <div className={styles.banner} data-testid="error-banner" role="alert">
      <div className={styles.content}>
        <span className={styles.icon} aria-hidden="true">⚠️</span>
        <span className={styles.messageText}>{message}</span>
      </div>
      {onClose && (
        <button
          type="button"
          className={styles.closeBtn}
          onClick={onClose}
          aria-label="エラーを閉じる"
        >
          ×
        </button>
      )}
    </div>
  );
};
