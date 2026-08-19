import jaMessages from '../locales/ja.json';

export type MessageKey = keyof typeof jaMessages;

/**
 * MSG-0001 に定義されたメッセージキーからローカライズされたテキストを取得する
 */
export function getMessage(key: MessageKey | string, defaultMsg?: string): string {
  if (key in jaMessages) {
    return jaMessages[key as MessageKey];
  }
  return defaultMsg ?? key;
}
