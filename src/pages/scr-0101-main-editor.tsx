import React, { useState, useEffect } from 'react';
import { useDocuments } from '../hooks/useDocuments';
import { usePreview } from '../hooks/usePreview';
import { useAutoSave } from '../hooks/useAutoSave';
import { useKeyboardShortcut } from '../hooks/useKeyboardShortcut';
import { Sidebar } from '../components/Sidebar';
import { Header } from '../components/Header';
import { Editor } from '../components/Editor';
import { Preview } from '../components/Preview';
import { ErrorBanner } from '../components/ErrorBanner';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ExportModal } from '../components/ExportModal';
import styles from './MainEditor.module.css';

export const MainEditorPage: React.FC = () => {
  const {
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
  } = useDocuments();

  const currentContent = selectedDoc?.content ?? '';
  const currentTitle = selectedDoc?.title ?? '無題のドキュメント';

  // 100ms デバウンスプレビュー
  const { htmlContent, isRendering } = usePreview(currentContent);

  // 1.5秒 自動保存
  useAutoSave(
    currentContent,
    currentTitle,
    handleSaveDocument,
    state === 'normal' && !!selectedDoc
  );

  // Ctrl+S / Cmd+S 明示保存ショートカット
  useKeyboardShortcut(() => {
    void handleSaveDocument(true);
  }, state === 'normal' && !!selectedDoc);

  // エクスポートモーダル状態
  const [isExportOpen, setIsExportOpen] = useState(false);

  // レスポンシブ対応 (800px以下でのタブ切替)
  const [activeTab, setActiveTab] = useState<'editor' | 'preview'>('editor');
  const [isMobile, setIsMobile] = useState<boolean>(
    typeof window !== 'undefined' ? window.innerWidth <= 800 : false
  );

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 800);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className={styles.appContainer}>
      {errorMessage && (
        <ErrorBanner message={errorMessage} onClose={clearError} />
      )}

      <div className={styles.mainLayout}>
        <Sidebar
          documents={documents}
          selectedDocId={selectedDoc?.id}
          isLoading={state === 'loading'}
          onSelectDocument={selectDocument}
          onCreateDocument={() => void handleCreateDocument()}
        />

        <div className={styles.contentArea}>
          <Header
            title={currentTitle}
            isSaving={isSaving}
            hasSelectedDoc={!!selectedDoc}
            infoMessage={infoMessage}
            onTitleChange={updateTitle}
            onSave={() => void handleSaveDocument(true)}
            onOpenExport={() => setIsExportOpen(true)}
            onDelete={() => void handleDeleteDocument()}
          />

          {isMobile && selectedDoc && (
            <div className={styles.mobileTabs}>
              <button
                type="button"
                className={`${styles.tabBtn} ${activeTab === 'editor' ? styles.activeTab : ''}`}
                onClick={() => setActiveTab('editor')}
              >
                エディタ
              </button>
              <button
                type="button"
                className={`${styles.tabBtn} ${activeTab === 'preview' ? styles.activeTab : ''}`}
                onClick={() => setActiveTab('preview')}
              >
                プレビュー
              </button>
            </div>
          )}

          <div className={styles.paneContainer}>
            {state === 'loading' ? (
              <LoadingSpinner message="読み込み中..." />
            ) : !selectedDoc ? (
              <div className={styles.emptyPrompt}>
                <p>ドキュメントが選択されていません。</p>
                <button
                  type="button"
                  className={styles.promptCreateBtn}
                  data-testid="btn-create-doc"
                  onClick={() => void handleCreateDocument()}
                >
                  ＋ 新規ドキュメントを作成
                </button>
              </div>
            ) : (
              <div className={styles.splitView}>
                <div
                  className={`${styles.editorPane} ${
                    isMobile && activeTab !== 'editor' ? styles.hiddenPane : ''
                  }`}
                >
                  <Editor
                    content={currentContent}
                    onChange={updateContent}
                  />
                </div>

                <div
                  className={`${styles.previewPane} ${
                    isMobile && activeTab !== 'preview' ? styles.hiddenPane : ''
                  }`}
                >
                  <Preview
                    htmlContent={htmlContent}
                    isLoading={isRendering}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        documentTitle={currentTitle}
      />
    </div>
  );
};

export default MainEditorPage;
