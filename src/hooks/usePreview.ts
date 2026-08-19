import { useState, useEffect, useRef } from 'react';
import { parseMarkdown } from '../utils/markdown';

export interface UsePreviewResult {
  htmlContent: string;
  isRendering: boolean;
}

/**
 * 100msデバウンスでMarkdownプレビューHTMLをリアルタイム更新するカスタムフック (UC-0201, BR-0201-1)
 */
export function usePreview(markdown: string): UsePreviewResult {
  const [htmlContent, setHtmlContent] = useState<string>(() => parseMarkdown(markdown));
  const [isRendering, setIsRendering] = useState<boolean>(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setIsRendering(true);

    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(() => {
      try {
        const parsed = parseMarkdown(markdown);
        setHtmlContent(parsed);
      } finally {
        setIsRendering(false);
      }
    }, 100);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [markdown]);

  return { htmlContent, isRendering };
}
