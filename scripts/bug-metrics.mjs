import fs from 'node:fs';
import path from 'node:path';

const REVIEWS_DIR = path.resolve('docs/reviews');

function getBugFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  let files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isFile() && entry.name.startsWith('BUG-') && entry.name.endsWith('.md')) {
      files.push(fullPath);
    }
  }
  return files;
}

function parseFrontmatter(content) {
  if (!content.startsWith('---')) return null;
  const endIdx = content.indexOf('---', 3);
  if (endIdx === -1) return null;
  const rawYaml = content.slice(3, endIdx).trim();
  const data = {};
  for (const line of rawYaml.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const colonIdx = trimmed.indexOf(':');
    if (colonIdx === -1) continue;
    const key = trimmed.slice(0, colonIdx).trim();
    let val = trimmed.slice(colonIdx + 1).trim().replace(/^['"]|['"]$/g, '');
    data[key] = val;
  }
  return data;
}

const bugFiles = getBugFiles(REVIEWS_DIR);
console.log(`=== バグ票定量集計レポート (総件数: ${bugFiles.length} 件) ===\n`);

if (bugFiles.length === 0) {
  console.log('現在起票されているバグ票はありません。');
  process.exit(0);
}

const causeCategories = {};
const causePhases = {};
const fixMethods = {};

for (const file of bugFiles) {
  const content = fs.readFileSync(file, 'utf-8');
  const data = parseFrontmatter(content);
  if (!data) continue;

  causeCategories[data.cause_category] = (causeCategories[data.cause_category] || 0) + 1;
  causePhases[data.cause_phase] = (causePhases[data.cause_phase] || 0) + 1;
  fixMethods[data.fix_method] = (fixMethods[data.fix_method] || 0) + 1;
}

console.log('■ 原因分類 (cause_category) 分布:');
console.table(causeCategories);

console.log('\n■ 作り込み工程 (cause_phase) 分布:');
console.table(causePhases);

console.log('\n■ 修正方法 (fix_method) 分布:');
console.table(fixMethods);
