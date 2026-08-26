import React, { useState } from 'react';
import { ExportModal } from '../components/ExportModal';
import type { ExportOptions } from '../types/export';

export interface Scr0301ExportModalPageProps {
  isOpen?: boolean;
  documentTitle?: string;
  documentContent?: string;
  initialOptions?: Partial<ExportOptions>;
  onClose?: () => void;
  onSuccess?: () => void;
}

/**
 * SCR-0301 エクスポート設定モーダル画面
 *
 * ドキュメントのPDF/HTMLエクスポート条件（出力形式、用紙サイズ等）を設定し、ダウンロード処理を実行する。
 */
export const Scr0301ExportModalPage: React.FC<Scr0301ExportModalPageProps> = ({
  isOpen = true,
  documentTitle = '無題のドキュメント',
  documentContent = '',
  initialOptions,
  onClose,
  onSuccess,
}) => {
  const [internalOpen, setInternalOpen] = useState(isOpen);

  const handleClose = () => {
    setInternalOpen(false);
    onClose?.();
  };

  const handleSuccess = () => {
    setInternalOpen(false);
    onSuccess?.();
  };

  return (
    <ExportModal
      isOpen={onClose ? isOpen : internalOpen}
      onClose={handleClose}
      documentTitle={documentTitle}
      documentContent={documentContent}
      initialOptions={initialOptions}
      onSuccess={handleSuccess}
    />
  );
};

export default Scr0301ExportModalPage;
