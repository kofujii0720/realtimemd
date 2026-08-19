import React from 'react';
import { LoadingSpinner } from './LoadingSpinner';
import styles from './Preview.module.css';

interface PreviewProps {
  htmlContent: string;
  isLoading?: boolean;
}

export const Preview: React.FC<PreviewProps> = ({ htmlContent, isLoading = false }) => {
  return (
    <div className={styles.previewContainer}>
      <div className={styles.previewHeader}>
        <span className={styles.paneLabel}>プレビュー</span>
        {isLoading && <span className={styles.renderingBadge}>更新中...</span>}
      </div>
      <div className={styles.previewContent} data-testid="doc-preview-pane">
        {isLoading && !htmlContent ? (
          <LoadingSpinner />
        ) : (
          <div
            className={styles.markdownBody}
            dangerouslySetInnerHTML={{ __html: htmlContent }}
          />
        )}
      </div>
    </div>
  );
};
