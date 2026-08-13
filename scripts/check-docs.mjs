import fs from 'node:fs';
import path from 'node:path';

const DOCS_DIR = path.resolve('docs');
const FORMAT_DIR = path.resolve('.agent/doc-format');

let errorsCount = 0;
let warningsCount = 0;

function logError(file, msg) {
  console.error(`\x1b[31m[ERROR]\x1b[0m ${file}: ${msg}`);
  errorsCount++;
}

function logWarn(file, msg) {
  console.warn(`\x1b[33m[WARN]\x1b[0m ${file}: ${msg}`);
  warningsCount++;
}

function getMarkdownFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  let files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'schema') continue; // テンプレート・スキーマ除外
      files = files.concat(getMarkdownFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      files.push(fullPath);
    }
  }
  return files;
}

function parseFrontmatter(content) {
  if (!content.startsWith('---')) return { data: null, body: content };
  const endIdx = content.indexOf('---', 3);
  if (endIdx === -1) return { data: null, body: content };

  const rawYaml = content.slice(3, endIdx).trim();
  const body = content.slice(endIdx + 3).trim();
  const data = {};

  for (const line of rawYaml.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const colonIdx = trimmed.indexOf(':');
    if (colonIdx === -1) continue;
    const key = trimmed.slice(0, colonIdx).trim();
    let val = trimmed.slice(colonIdx + 1).trim();

    if (val.startsWith('[') && val.endsWith(']')) {
      val = val.slice(1, -1).split(',').map(s => s.trim().replace(/^['"]|['"]$/g, '')).filter(Boolean);
    } else {
      val = val.replace(/^['"]|['"]$/g, '');
    }
    data[key] = val;
  }
  return { data, body };
}

// テンプレートごとの見出しセクション抽出
function extractSections(content) {
  const sections = [];
  const lines = content.split('\n');
  for (const line of lines) {
    const match = line.match(/^##\s+(.+)$/);
    if (match) {
      sections.push(match[1].trim());
    }
  }
  return sections;
}

const allDocFiles = getMarkdownFiles(DOCS_DIR);
const docMap = new Map(); // id -> filePath
const definedMessageKeys = new Set();
const referencedMessageKeys = new Set();

// 1パス目: ID および MSG キーの収集
for (const filePath of allDocFiles) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const { data, body } = parseFrontmatter(content);
  if (data && data.id) {
    docMap.set(data.id, filePath);
  }

  // メッセージ辞書のキー収集
  if (data && data.id === 'MSG-0001') {
    const keyMatches = body.match(/`([^`]+\.[^`]+)`/g) || [];
    for (const k of keyMatches) {
      definedMessageKeys.add(k.replace(/`/g, ''));
    }
  }
}

// 2パス目: 詳細10検証
for (const filePath of allDocFiles) {
  const relPath = path.relative(process.cwd(), filePath);
  const content = fs.readFileSync(filePath, 'utf-8');
  const { data, body } = parseFrontmatter(content);

  // #1 フロントマターおよび ID / ファイル名一致チェック
  if (!data || !data.id) {
    logError(relPath, 'フロントマターに id が定義されていません。');
    continue;
  }
  const fileNameWithoutExt = path.basename(filePath, '.md');
  if (!fileNameWithoutExt.startsWith(data.id)) {
    logError(relPath, `ID (${data.id}) とファイル名 (${fileNameWithoutExt}) が不一致です。`);
  }

  // #2 & #3 参照ID実在性チェック
  const refsKeys = ['consumes', 'calls_apis', 'related_screens', 'test_viewpoints'];
  for (const refKey of refsKeys) {
    if (data[refKey]) {
      const refs = Array.isArray(data[refKey]) ? data[refKey] : [data[refKey]];
      for (const refId of refs) {
        if (!docMap.has(refId) && !refId.startsWith('VP-')) {
          logError(relPath, `${refKey} で参照している ID (${refId}) が存在しません。`);
        }
      }
    }
  }

  // #3 test_viewpoints チェック
  if (!data.id.startsWith('VP-') && !data.id.startsWith('MSG-') && !data.id.startsWith('PLAN-') && !data.id.startsWith('ADR-') && !data.id.startsWith('BUG-')) {
    if (!data.test_viewpoints || (Array.isArray(data.test_viewpoints) && data.test_viewpoints.length === 0)) {
      logError(relPath, 'test_viewpoints が定義されていないか空です。');
    }
  }

  // #4 テンプレートセクション存在チェック
  let tmplFile = null;
  if (data.id.startsWith('API-')) tmplFile = path.join(FORMAT_DIR, 'api-design.md');
  else if (data.id.startsWith('SCR-')) tmplFile = path.join(FORMAT_DIR, 'screen-design.md');
  else if (data.id.startsWith('TBL-')) tmplFile = path.join(FORMAT_DIR, 'table-design.md');
  else if (data.id.startsWith('UC-')) tmplFile = path.join(FORMAT_DIR, 'use-case.md');

  if (tmplFile && fs.existsSync(tmplFile)) {
    const tmplContent = fs.readFileSync(tmplFile, 'utf-8');
    const requiredSections = extractSections(tmplContent);
    const docSections = extractSections(content);
    for (const reqSec of requiredSections) {
      if (!docSections.some(s => s.includes(reqSec.split(' ')[0]))) {
        logError(relPath, `必須セクション「${reqSec}」が存在しません。`);
      }
    }
  }

  // #6 文章参照の検出（警告）
  if (/を参照/i.test(body)) {
    logWarn(relPath, '文章による参照（「〜を参照」）が検出されました。ID参照に統一してください。');
  }

  // #7 未定・TBDチェック (否定先読み 相当)
  if (/未定(?!義)|TBD|TODO/i.test(body)) {
    logWarn(relPath, '本文中に「未定/TBD/TODO」が検出されました。');
  }

  // #8 エラーコードチェック (API設計書)
  if (data.id.startsWith('API-')) {
    const apiNum = data.id.replace('API-', '');
    const errMatches = body.match(/E-\d{4}-\d{3}/g) || [];
    for (const errCode of errMatches) {
      if (!errCode.startsWith(`E-${apiNum}-`)) {
        logError(relPath, `エラーコード ${errCode} のAPI番号が自文書 (${data.id}) と不一致です。`);
      }
    }
  }

  // #9 messageKey チェック
  const msgKeyMatches = body.match(/`MSG-0001\.key\.([^`]+)`/g) || [];
  for (const match of msgKeyMatches) {
    const key = match.replace(/`MSG-0001\.key\.|`/g, '');
    referencedMessageKeys.add(key);
    if (definedMessageKeys.size > 0 && !definedMessageKeys.has(key)) {
      logError(relPath, `メッセージキー '${key}' が MSG-0001 に定義されていません。`);
    }
  }

  // #10 画面設計書の4状態チェック
  if (data.id.startsWith('SCR-')) {
    const requiredStates = ['読込中', '0件', '正常', 'エラー'];
    for (const state of requiredStates) {
      if (!body.includes(state)) {
        logError(relPath, `画面設計書に状態「${state}」の表示定義が含まれていません。`);
      }
    }
  }
}

// #9 逆方向未参照キーチェック (警告)
if (definedMessageKeys.size > 0) {
  for (const defKey of definedMessageKeys) {
    if (!referencedMessageKeys.has(defKey) && !defKey.startsWith('label.')) {
      logWarn('MSG-0001-messages.md', `メッセージキー '${defKey}' がいずれの設計書からも参照されていません。`);
    }
  }
}

console.log(`\n--- チェック完了 ---`);
console.log(`エラー: ${errorsCount} 件, 警告: ${warningsCount} 件`);

if (errorsCount > 0) {
  process.exit(1);
} else {
  process.exit(0);
}
