import { useEffect } from 'react';

/**
 * Ctrl+S / Cmd+S キーボードショートカットで保存操作を実行するカスタムフック (SCR-0101 §7)
 */
export function useKeyboardShortcut(onSave: () => void, enabled = true): void {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        onSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onSave, enabled]);
}
