import { useEffect, useRef } from 'react';

/**
 * 1.5秒（1500ms）無操作で自動下書き保存を実行するカスタムフック (REQ-0003, BR-0101-1)
 */
export function useAutoSave(
  content: string,
  title: string,
  onSave: (isExplicit: boolean) => Promise<boolean>,
  enabled = true
): void {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const initialMountRef = useRef(true);
  const lastSavedRef = useRef<{ title: string; content: string }>({ title, content });

  useEffect(() => {
    // 初回マウント時はスキップ
    if (initialMountRef.current) {
      initialMountRef.current = false;
      lastSavedRef.current = { title, content };
      return;
    }

    if (!enabled) return;

    // 前回の保存内容と同一ならスキップ
    if (lastSavedRef.current.title === title && lastSavedRef.current.content === content) {
      return;
    }

    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(() => {
      void (async () => {
        const success = await onSave(false);
        if (success) {
          lastSavedRef.current = { title, content };
        }
      })();
    }, 1500);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [content, title, onSave, enabled]);
}
