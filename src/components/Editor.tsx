import React from 'react';
import styles from './Editor.module.css';

interface EditorProps {
  content: string;
  disabled?: boolean;
  onChange: (newContent: string) => void;
}

export const Editor: React.FC<EditorProps> = ({ content, disabled = false, onChange }) => {
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    // REQ-0003: \r\n を \n へ正規化
    const normalized = e.target.value.replace(/\r\n/g, '\n');
    onChange(normalized);
  };

  return (
    <div className={styles.editorContainer}>
      <div className={styles.editorHeader}>
        <span className={styles.paneLabel}>Markdown エディタ</span>
        <span className={styles.charCount}>
          {content.length} 文字 ({Math.round(new Blob([content]).size / 1024)} KB / 2048 KB)
        </span>
      </div>
      <textarea
        className={styles.textarea}
        data-testid="doc-editor-textarea"
        value={content}
        onChange={handleChange}
        disabled={disabled}
        placeholder="# Markdownを入力してください..."
        spellCheck={false}
        aria-label="Markdown本文入力エリア"
      />
    </div>
  );
};
