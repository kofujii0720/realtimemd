import { test, expect, Page } from '@playwright/test';

interface MockDoc {
  id: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

async function setupDefaultApiRoutes(
  page: Page,
  options?: {
    exportDelayMs?: number;
    exportFail?: boolean;
    exportFailCode?: string;
    exportFailMessage?: string;
  }
) {
  const docs: MockDoc[] = [
    {
      id: 'doc-export-test',
      title: 'エクスポートテスト用ドキュメント',
      content: '# タイトル\n\nエクスポートテスト本文です。',
      created_at: '2026-08-26T00:00:00.000Z',
      updated_at: '2026-08-26T00:00:00.000Z',
    },
  ];

  await page.route('**/api/v1/documents**', async (route) => {
    const request = route.request();
    const method = request.method();
    const url = request.url();

    if (method === 'GET' && !url.match(/\/api\/v1\/documents\/[^?]+/)) {
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
    } else if (method === 'GET') {
      const match = url.match(/\/api\/v1\/documents\/([^/?]+)/);
      const id = match && match[1] ? decodeURIComponent(match[1]) : '';
      const doc = docs.find((d) => d.id === id);
      if (doc) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(doc),
        });
      } else {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({
            code: 'E-0105-001',
            message_key: 'error.document.notFound',
            detail: '指定されたドキュメントが見つかりません。',
          }),
        });
      }
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

  await page.route('**/api/v1/export', async (route) => {
    if (options?.exportDelayMs) {
      await new Promise((resolve) => setTimeout(resolve, options.exportDelayMs));
    }

    if (options?.exportFail) {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          code: options.exportFailCode || 'E-0301-001',
          message_key: 'error.export.pdfFailed',
          detail: options.exportFailMessage || 'PDFの生成に失敗しました。',
        }),
      });
      return;
    }

    const postData = JSON.parse(route.request().postData() || '{}');
    const format = postData.format || 'pdf';

    if (format === 'html') {
      await route.fulfill({
        status: 200,
        contentType: 'text/html; charset=utf-8',
        body: `<!DOCTYPE html><html><head><title>Export</title></head><body>${postData.content}</body></html>`,
      });
    } else {
      // PDF binary mock
      await route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        body: Buffer.from('%PDF-1.4 mock pdf content'),
      });
    }
  });
}

test.describe('SCR-0301 エクスポート設定モーダル E2Eテスト', () => {
  test.beforeEach(async ({ page }) => {
    await setupDefaultApiRoutes(page);
    await page.goto('/');
  });

  test('[VP-101] 画面表示・ルーティング - メイン画面のエクスポートボタンからエクスポート設定モーダルが正常に表示されること', async ({ page }) => {
    // メイン画面のエクスポートボタンをクリックしてモーダルを開く
    await page.getByTestId('btn-open-export').click();

    // モーダルおよび主要コンポーネントが表示されることを確認
    await expect(page.getByTestId('export-format-radio')).toBeVisible();
    await expect(page.getByTestId('btn-submit-export')).toBeVisible();
    await expect(page.getByTestId('btn-cancel-export')).toBeVisible();
  });

  test('[VP-102] コンポーネント配置 - ヘッダー、入力領域、フッターの各要素が正しく配置されていること', async ({ page }) => {
    await page.getByTestId('btn-open-export').click();

    // 入力領域
    await expect(page.getByTestId('export-format-radio')).toBeVisible();
    await expect(page.getByTestId('export-format-pdf')).toBeVisible();
    await expect(page.getByTestId('export-format-html')).toBeVisible();
    await expect(page.getByTestId('export-paper-select')).toBeVisible();

    // フッター領域
    await expect(page.getByTestId('btn-cancel-export')).toBeVisible();
    await expect(page.getByTestId('btn-submit-export')).toBeVisible();
  });

  test('[VP-103] 表示データマッピング - 初期選択状態およびフォーマット切り替えによる用紙サイズの表示・非表示マッピング', async ({ page }) => {
    await page.getByTestId('btn-open-export').click();

    // PDF選択時: 用紙サイズセレクトが表示される
    await expect(page.getByTestId('export-format-pdf')).toBeChecked();
    await expect(page.getByTestId('export-paper-select')).toBeVisible();

    // HTML選択時: 用紙サイズセレクトが非表示になる (SCR-0301 表示条件)
    await page.getByTestId('export-format-html').check();
    await expect(page.getByTestId('export-format-html')).toBeChecked();
    await expect(page.getByTestId('export-paper-select')).not.toBeVisible();

    // 再度PDF選択時: 用紙サイズセレクトが再表示される
    await page.getByTestId('export-format-pdf').check();
    await expect(page.getByTestId('export-paper-select')).toBeVisible();
  });

  test('[VP-104] フォーム入力・バリデーション - 出力フォーマットおよび用紙サイズの選択変更', async ({ page }) => {
    await page.getByTestId('btn-open-export').click();

    // 用紙サイズを Letter に変更
    const paperSelect = page.getByTestId('export-paper-select');
    await paperSelect.selectOption('Letter');
    await expect(paperSelect).toHaveValue('Letter');

    // 用紙サイズを A4 に戻す
    await paperSelect.selectOption('A4');
    await expect(paperSelect).toHaveValue('A4');

    // フォーマットを HTML に変更
    await page.getByTestId('export-format-html').check();
    await expect(page.getByTestId('export-format-html')).toBeChecked();
  });

  test('[VP-105] 操作・API呼出・画面遷移 - ダウンロード実行、キャンセル、連続操作、中断・再開シナリオ', async ({ page }) => {
    // 1. ダウンロード実行シナリオ (PDF)
    await page.getByTestId('btn-open-export').click();
    await expect(page.getByTestId('export-format-radio')).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await page.getByTestId('btn-submit-export').click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.pdf');

    // 成功後、モーダルが閉じること
    await expect(page.getByTestId('export-format-radio')).not.toBeVisible();

    // 2. 中断・再開シナリオ (キャンセル操作)
    await page.getByTestId('btn-open-export').click();
    await expect(page.getByTestId('export-format-radio')).toBeVisible();
    await page.getByTestId('btn-cancel-export').click();
    await expect(page.getByTestId('export-format-radio')).not.toBeVisible();

    // 3. 2回連続操作シナリオ (再度開いてHTMLダウンロード)
    await page.getByTestId('btn-open-export').click();
    await page.getByTestId('export-format-html').check();

    const htmlDownloadPromise = page.waitForEvent('download');
    await page.getByTestId('btn-submit-export').click();
    const htmlDownload = await htmlDownloadPromise;
    expect(htmlDownload.suggestedFilename()).toContain('.html');
    await expect(page.getByTestId('export-format-radio')).not.toBeVisible();
  });

  test('[VP-106] 画面4状態 - 読込中、0件、正常、エラーの各状態の表示確認', async ({ page }) => {
    // 1. 正常状態 (normal): モーダルが正常に表示されること
    await page.getByTestId('btn-open-export').click();
    await expect(page.getByTestId('export-format-radio')).toBeVisible();
    await expect(page.getByTestId('btn-submit-export')).toBeVisible();

    // 2. 0件状態 (empty/default): オプション指定なしでデフォルト値（PDF, A4）が自動適用されていること
    await expect(page.getByTestId('export-format-pdf')).toBeChecked();
    await expect(page.getByTestId('export-paper-select')).toHaveValue('A4');
    await page.getByTestId('btn-cancel-export').click();

    // 3. 読込中状態 (loading): ダウンロード処理中にスピナーが表示されること
    const slowPage = await page.context().newPage();
    await setupDefaultApiRoutes(slowPage, { exportDelayMs: 1500 });
    await slowPage.goto('/');
    await slowPage.getByTestId('btn-open-export').click();
    await slowPage.getByTestId('btn-submit-export').click();
    await expect(slowPage.getByTestId('export-processing-spinner')).toBeVisible();
    await slowPage.close();

    // 4. エラー状態 (error): 生成失敗時に警告アラートメッセージが表示されること
    const errorPage = await page.context().newPage();
    await setupDefaultApiRoutes(errorPage, { exportFail: true });
    await errorPage.goto('/');
    await errorPage.getByTestId('btn-open-export').click();
    await errorPage.getByTestId('btn-submit-export').click();
    await expect(errorPage.getByTestId('export-error-alert')).toBeVisible();
    await errorPage.close();
  });

  test('[VP-107] キーボード・レスポンシブ - Escキー押下によるモーダルクローズおよびレスポンシブ動作', async ({ page }) => {
    await page.getByTestId('btn-open-export').click();
    await expect(page.getByTestId('export-format-radio')).toBeVisible();

    // Escキー押下でモーダルを閉じる (SCR-0301 非機能・アクセシビリティ)
    await page.keyboard.press('Escape');
    await expect(page.getByTestId('export-format-radio')).not.toBeVisible();

    // レスポンシブ表示検証 (幅768px)
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.getByTestId('btn-open-export').click();
    await expect(page.getByTestId('export-format-radio')).toBeVisible();
    await expect(page.getByTestId('btn-submit-export')).toBeVisible();
    await page.getByTestId('btn-cancel-export').click();
  });

  test('[VP-108] 要確認事項 - 前提条件および特記事項の整合性確認', async ({ page }) => {
    // 前提条件: ドキュメント選択状態でエクスポートモーダルが起動できること
    await page.getByTestId('btn-open-export').click();
    await expect(page.getByTestId('export-format-radio')).toBeVisible();
    await page.getByTestId('btn-cancel-export').click();
  });
});
