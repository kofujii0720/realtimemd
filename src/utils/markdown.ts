/**
 * HTMLエスケープ
 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * 軽量かつ安全なクライアントサイドMarkdownパーサー
 * 見出し, リスト, 太字, 斜体, コードブロック, Mermaid, KaTeX, リンク, テーブル, 水平線をサポート
 */
export function parseMarkdown(markdown: string): string {
  if (!markdown) return '';

  // 改行の正規化 (\r\n -> \n)
  let text = markdown.replace(/\r\n/g, '\n');

  // コードブロック / Mermaidブロックの退避
  const codeBlocks: string[] = [];
  text = text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (_match, lang, code) => {
    const cleanLang = (lang || '').trim().toLowerCase();
    const cleanCode = (code || '').trimEnd();
    const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`;

    if (cleanLang === 'mermaid') {
      codeBlocks.push(
        `<div class="mermaid-diagram" data-testid="mermaid-diagram"><pre class="mermaid">${escapeHtml(cleanCode)}</pre></div>`
      );
    } else {
      codeBlocks.push(
        `<pre><code class="language-${escapeHtml(cleanLang)}">${escapeHtml(cleanCode)}</code></pre>`
      );
    }
    return placeholder;
  });

  // KaTeXブロック式 ($$...$$) の退避
  const mathBlocks: string[] = [];
  text = text.replace(/\$\$([\s\S]*?)\$\$/g, (_match, math) => {
    const placeholder = `__MATH_BLOCK_${mathBlocks.length}__`;
    mathBlocks.push(
      `<div class="katex-display" data-testid="katex-display"><code>$$${escapeHtml(math.trim())}$$</code></div>`
    );
    return placeholder;
  });

  // KaTeXインライン式 ($...$) の退避
  text = text.replace(/\$([^\$\n]+)\$/g, (_match, math) => {
    const placeholder = `__MATH_BLOCK_${mathBlocks.length}__`;
    mathBlocks.push(
      `<span class="katex-inline" data-testid="katex-inline"><code>$${escapeHtml(math.trim())}$</code></span>`
    );
    return placeholder;
  });

  // インラインコード (`...`) の退避
  const inlineCodes: string[] = [];
  text = text.replace(/`([^`\n]+)`/g, (_match, code) => {
    const placeholder = `__INLINE_CODE_${inlineCodes.length}__`;
    inlineCodes.push(`<code>${escapeHtml(code)}</code>`);
    return placeholder;
  });

  // 見出し (# ~ ######)
  text = text.replace(/^######\s+(.*)$/gm, '<h6>$1</h6>');
  text = text.replace(/^#####\s+(.*)$/gm, '<h5>$1</h5>');
  text = text.replace(/^####\s+(.*)$/gm, '<h4>$1</h4>');
  text = text.replace(/^###\s+(.*)$/gm, '<h3>$1</h3>');
  text = text.replace(/^##\s+(.*)$/gm, '<h2>$1</h2>');
  text = text.replace(/^#\s+(.*)$/gm, '<h1>$1</h1>');

  // 水平線
  text = text.replace(/^(?:---|\*\*\*|___)\s*$/gm, '<hr />');

  // 引用
  text = text.replace(/^>\s+(.*)$/gm, '<blockquote>$1</blockquote>');

  // 太字と斜体
  text = text.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
  text = text.replace(/~~(.*?)~~/g, '<del>$1</del>');

  // リンク [text](url)
  text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

  // リスト処理 (- / * / 1.)
  const lines = text.split('\n');
  const resultLines: string[] = [];
  let inUnorderedList = false;
  let inOrderedList = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] ?? '';
    const ulMatch = line.match(/^[\*\-]\s+(.*)$/);
    const olMatch = line.match(/^(\d+)\.\s+(.*)$/);

    if (ulMatch) {
      if (!inUnorderedList) {
        if (inOrderedList) {
          resultLines.push('</ol>');
          inOrderedList = false;
        }
        resultLines.push('<ul>');
        inUnorderedList = true;
      }
      resultLines.push(`<li>${ulMatch[1]}</li>`);
    } else if (olMatch) {
      if (!inOrderedList) {
        if (inUnorderedList) {
          resultLines.push('</ul>');
          inUnorderedList = false;
        }
        resultLines.push('<ol>');
        inOrderedList = true;
      }
      resultLines.push(`<li>${olMatch[2]}</li>`);
    } else {
      if (inUnorderedList) {
        resultLines.push('</ul>');
        inUnorderedList = false;
      }
      if (inOrderedList) {
        resultLines.push('</ol>');
        inOrderedList = false;
      }

      if (
        line.trim() &&
        !line.startsWith('<h') &&
        !line.startsWith('<hr') &&
        !line.startsWith('<blockquote') &&
        !line.startsWith('__CODE_BLOCK_') &&
        !line.startsWith('__MATH_BLOCK_')
      ) {
        resultLines.push(`<p>${line}</p>`);
      } else {
        resultLines.push(line);
      }
    }
  }

  if (inUnorderedList) resultLines.push('</ul>');
  if (inOrderedList) resultLines.push('</ol>');

  let html = resultLines.join('\n');

  // プレースホルダーの復元
  for (let i = 0; i < inlineCodes.length; i++) {
    const val = inlineCodes[i];
    if (val !== undefined) {
      html = html.replace(`__INLINE_CODE_${i}__`, val);
    }
  }
  for (let i = 0; i < mathBlocks.length; i++) {
    const val = mathBlocks[i];
    if (val !== undefined) {
      html = html.replace(`__MATH_BLOCK_${i}__`, val);
    }
  }
  for (let i = 0; i < codeBlocks.length; i++) {
    const val = codeBlocks[i];
    if (val !== undefined) {
      html = html.replace(`__CODE_BLOCK_${i}__`, val);
    }
  }

  return html;
}
