import React from 'react';
import styles from './LoadingSpinner.module.css';

interface LoadingSpinnerProps {
  message?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ message }) => {
  return (
    <div className={styles.spinnerContainer} data-testid="doc-loading-spinner">
      <div className={styles.spinner} />
      {message && <p className={styles.spinnerMessage}>{message}</p>}
    </div>
  );
};
