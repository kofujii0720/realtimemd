export type ExportFormat = 'pdf' | 'html';
export type PaperSize = 'A4' | 'Letter';
export type MarginOption = 'normal' | 'none' | 'narrow';

export interface ExportOptions {
  format: ExportFormat;
  paperSize: PaperSize;
  margin?: MarginOption;
}

export interface ExportRequest {
  content: string;
  format: ExportFormat;
  paper_size?: PaperSize;
}

export type ExportState = 'idle' | 'loading' | 'error' | 'success';
