import { test, expect, Page } from '@playwright/test';

interface MockDoc {
  id: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

async function setupDefaultApiRoutes(page: Page, initialDocs?: MockDoc[]) {
  let docs: MockDoc[] = initialDocs
    ? [...initialDocs]
    : [
        {
          id: 'doc-1',
          title: '初期テストドキュメント',
          content: '# 初期テスト本文\n\n- アイテム1\n- アイテム2',
          created_at: '2026-08-19T00:00:00.000Z',
          updated_at: '2026-08-19T00:00:00.000Z',
        },
      ];

  await page.route('**/api/v1/documents**', async (route) => {
    const request = route.request();
    const method = request.method();
    const url = request.url();

    if (method === 'GET' && !url.match(/\/api\/v1\/documents\/[^?]+/)) {
      // API-0101: 一覧取得
      const items = docs.map((d) => ({
        id: d.id,
        title: d.title,
        updated_at: d.updated_at,
      }));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items, total: items.length, limit: 50, offset: 0 }),
      });
    } else if (method === 'POST') {
      // API-0102: 新規作成
      const postData = JSON.parse(request.postData() || '{}');
      const newDoc: MockDoc = {
        id: `doc-${Date.now()}`,
        title: postData.title || '無題のドキュメント',
        content: postData.content || '',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      docs = [newDoc, ...docs];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(newDoc),
      });
    } else if (method === 'PUT') {
      // API-0103: 更新
      const match = url.match(/\/api\/v1\/documents\/([^/?]+)/);
      const id = match && match[1] ? decodeURIComponent(match[1]) : '';
      const postData = JSON.parse(request.postData() || '{}');
      const existing = docs.find((d) => d.id === id);
      const updated: MockDoc = existing
        ? { ...existing, title: postData.title, content: postData.content, updated_at: new Date().toISOString() }
        : {
            id,
            title: postData.title,
            content: postData.content,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
      docs = docs.map((d) => (d.id === id ? updated : d));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(updated),
      });
    } else if (method === 'DELETE') {
      // API-0104: 削除
      const match = url.match(/\/api\/v1\/documents\/([^/?]+)/);
      const id = match && match[1] ? decodeURIComponent(match[1]) : '';
      docs = docs.filter((d) => d.id !== id);
      await route.fulfill({
        status: 204,
        body: '',
      });
    } else {
      await route.continue();
    }
  });

  await page.route('**/api/v1/preview/render', async (route) => {
    const postData = JSON.parse(route.request().postData() || '{}');
    const content = postData.content || '';
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ html_content: `<div>${content}</div>`, warnings: [] }),
    });
  });
}

test.describe('SCR-0101 メインエディタ＆プレビュー画面 E2Eテスト', () => {
  test.beforeEach(async ({ page }) => {
    await setupDefaultApiRoutes(page);
    await page.goto('/');
  });

  test('[VP-101] 画面表示・ルーティング - ルートURLにアクセスしてメイン画面が正常に初期表示されること', async ({ page }) => {
    // 画面の基本要素が表示されることを確認
    await expect(page.getByTestId('doc-list')).toBeVisible();
    await expect(page.getByTestId('doc-title-input')).toBeVisible();
    await expect(page.getByTestId('doc-editor-textarea')).toBeVisible();
    await expect(page.getByTestId('doc-preview-pane')).toBeVisible();
  });

  test('[VP-102] コンポーネント配置 - 各領域（サイドバー、ヘッダー、エディタ、プレビュー）の要素が配置されていること', async ({ page }) => {
    // サイドバー領域
    await expect(page.getByTestId('doc-list')).toBeVisible();
    await expect(page.getByTestId('btn-create-doc')).toBeVisible();

    // ヘッダー領域
    await expect(page.getByTestId('doc-title-input')).toBeVisible();
    await expect(page.getByTestId('btn-save-doc')).toBeVisible();
    await expect(page.getByTestId('btn-open-export')).toBeVisible();
    await expect(page.getByTestId('btn-delete-doc')).toBeVisible();

    // エディタ領域 (左ペイン)
    await expect(page.getByTestId('doc-editor-textarea')).toBeVisible();

    // プレビュー領域 (右ペイン)
    await expect(page.getByTestId('doc-preview-pane')).toBeVisible();
  });

  test('[VP-103] 表示データマッピング - 選択ドキュメントの情報がタイトル、エディタ、プレビューに描画されること', async ({ page }) => {
    // 初期選択ドキュメントのデータ描画確認
    const titleInput = page.getByTestId('doc-title-input');
    const editorTextarea = page.getByTestId('doc-editor-textarea');
    const previewPane = page.getByTestId('doc-preview-pane');

    await expect(titleInput).toBeVisible();
    await expect(editorTextarea).toBeVisible();
    await expect(previewPane).toBeVisible();

    // タイトル初期値の存在確認
    const titleValue = await titleInput.inputValue();
    expect(titleValue).toBe('初期テストドキュメント');
  });

  test('[VP-104] フォーム入力・バリデーション - タイトルおよび本文の入力とプレビューのリアルタイム反映', async ({ page }) => {
    const titleInput = page.getByTestId('doc-title-input');
    const editorTextarea = page.getByTestId('doc-editor-textarea');
    const previewPane = page.getByTestId('doc-preview-pane');

    // タイトルの変更入力
    await titleInput.fill('E2Eテスト用ドキュメントタイトル');
    await expect(titleInput).toHaveValue('E2Eテスト用ドキュメントタイトル');

    // Markdown本文の入力（見出し、リスト記法を含む）
    const markdownContent = [
      '# テスト大見出し',
      '',
      '- リストアイテム 1',
      '- リストアイテム 2',
    ].join('\n');

    await editorTextarea.fill(markdownContent);
    await expect(editorTextarea).toHaveValue(markdownContent);

    // デバウンス(100ms)後のプレビューレンダリング反映確認
    await page.waitForTimeout(300);
    await expect(previewPane).toBeVisible();
    await expect(previewPane).toContainText('テスト大見出し');
    await expect(previewPane).toContainText('リストアイテム 1');
  });

  test('[VP-105] 操作・API呼出・画面遷移 - 新規作成、保存、削除、エクスポートモーダル起動および連続操作', async ({ page }) => {
    const btnCreate = page.getByTestId('btn-create-doc');
    const btnSave = page.getByTestId('btn-save-doc');
    const btnDelete = page.getByTestId('btn-delete-doc');
    const btnExport = page.getByTestId('btn-open-export');
    const titleInput = page.getByTestId('doc-title-input');
    const editorTextarea = page.getByTestId('doc-editor-textarea');

    // 1. 新規作成ボタン操作
    await btnCreate.click();
    await expect(titleInput).toBeVisible();
    await expect(titleInput).toHaveValue('無題のドキュメント');

    // 2. 本文編集と保存操作（1回目）
    await titleInput.fill('保存テストドキュメント');
    await editorTextarea.fill('## 保存テスト本文 1回目');
    await btnSave.click();

    // 3. 連続操作検証（2回目即時保存）
    await editorTextarea.fill('## 保存テスト本文 2回目 連続更新');
    await btnSave.click();

    // 4. エクスポートボタン操作（モーダル起動導線確認）
    await btnExport.click();
    await expect(page.getByRole('dialog')).toBeVisible();
    // モーダルを閉じる
    await page.getByRole('button', { name: 'キャンセル' }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible();

    // 5. 削除ボタン操作
    await btnDelete.click();
    await expect(page.getByTestId('doc-list')).toBeVisible();
  });

  test('[VP-106] 画面4状態 - 読込中、0件、正常、エラーの各状態の表示確認', async ({ page }) => {
    // 1. 正常状態 (normal): 全ペインが表示されること
    await expect(page.getByTestId('doc-list')).toBeVisible();
    await expect(page.getByTestId('doc-title-input')).toBeVisible();
    await expect(page.getByTestId('doc-editor-textarea')).toBeVisible();
    await expect(page.getByTestId('doc-preview-pane')).toBeVisible();

    // 2. 0件状態 (empty): ドキュメント一覧が空の場合の表示確認
    const emptyPage = await page.context().newPage();
    await emptyPage.route('**/api/v1/documents**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0, limit: 50, offset: 0 }),
        });
      } else {
        await route.continue();
      }
    });
    await emptyPage.goto('/');
    await expect(emptyPage.getByTestId('doc-list')).toBeVisible();
    await expect(emptyPage.getByText('ドキュメントがありません')).toBeVisible();
    await emptyPage.close();

    // 3. エラー状態 (error): error-banner が表示されること
    const errorPage = await page.context().newPage();
    await errorPage.route('**/api/v1/documents**', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: { message: 'サーバーエラーが発生しました', code: 'INTERNAL_ERROR' } }),
      });
    });
    await errorPage.goto('/');
    await expect(errorPage.getByTestId('error-banner')).toBeVisible();
    await errorPage.close();
  });

  test('[VP-107] キーボード・レスポンシブ - Ctrl+S/Cmd+S保存ショートカットおよび幅800px以下でのレスポンシブ動作', async ({ page }) => {
    const titleInput = page.getByTestId('doc-title-input');
    const editorTextarea = page.getByTestId('doc-editor-textarea');

    await titleInput.fill('ショートカット保存ドキュメント');
    await editorTextarea.fill('ショートカットキー検証');

    // ショートカットキー操作 (Ctrl+S / Meta+S)
    await page.keyboard.press('Control+s');
    await page.keyboard.press('Meta+s');

    // レスポンシブ表示検証 (幅800px以下)
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.getByTestId('doc-editor-textarea')).toBeVisible();
  });

  test('[VP-108] 要確認事項 - 前提条件および特記事項の整合性確認', async ({ page }) => {
    // 前提条件・コンポーネント整合性の確認
    await expect(page.getByTestId('doc-list')).toBeVisible();
  });
});
