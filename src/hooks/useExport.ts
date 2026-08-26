import { useState, useCallback, useEffect } from 'react';
import type { ExportFormat, PaperSize, MarginOption, ExportOptions } from '../types/export';
import { exportDocumentApi, triggerFileDownload } from '../api/export';
import { ApiError } from '../api/documents';
import { getMessage } from '../utils/messages';

export interface UseExportProps {
  isOpen: boolean;
  content: string;
  documentTitle: string;
  initialOptions?: Partial<ExportOptions>;
  onClose: () => void;
  onSuccess?: () => void;
}

export function useExport({
  isOpen,
  content,
  documentTitle,
  initialOptions,
  onClose,
  onSuccess,
}: UseExportProps) {
  // 0件状態: 設定可能なオプション項目が指定なし状態の場合、デフォルト設定を自動適用表示する (SCR-0301)
  const defaultFormat: ExportFormat = 'pdf';
  const defaultPaperSize: PaperSize = 'A4';
  const defaultMargin: MarginOption = 'normal';

  const [format, setFormat] = useState<ExportFormat>(initialOptions?.format ?? defaultFormat);
  const [paperSize, setPaperSize] = useState<PaperSize>(initialOptions?.paperSize ?? defaultPaperSize);
  const [margin, setMargin] = useState<MarginOption>(initialOptions?.margin ?? defaultMargin);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // モーダルオープン時または初期設定変更時にリセット
  useEffect(() => {
    if (isOpen) {
      setFormat(initialOptions?.format ?? defaultFormat);
      setPaperSize(initialOptions?.paperSize ?? defaultPaperSize);
      setMargin(initialOptions?.margin ?? defaultMargin);
      setIsLoading(false);
      setErrorMessage(null);
    }
  }, [isOpen, initialOptions]);

  // Escキー押下でモーダルを閉じる (SCR-0301 非機能・アクセシビリティ)
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleExport = useCallback(async () => {
    if (isLoading) return;
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const result = await exportDocumentApi({
        content,
        format,
        paper_size: format === 'pdf' ? paperSize : undefined,
      });

      const sanitizedTitle = (documentTitle.trim() || 'document').replace(/[\\/:*?"<>|]/g, '_');
      const filename = `${sanitizedTitle}.${format}`;

      triggerFileDownload(result.blob, filename);
      onClose();
      onSuccess?.();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(getMessage('error.common.systemError'));
      }
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, content, format, paperSize, documentTitle, onClose, onSuccess]);

  return {
    format,
    setFormat,
    paperSize,
    setPaperSize,
    margin,
    setMargin,
    isLoading,
    errorMessage,
    setErrorMessage,
    handleExport,
  };
}
