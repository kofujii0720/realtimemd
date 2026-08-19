import html
import re
from typing import List, Tuple


class MarkdownRenderer:
    """
    Markdownテキストを安全なHTML文字列へ変換するレンダラー.
    
    XSS対策としてHTMLエスケープおよびURLスキームのサニタイズを実施する.
    """

    SAFE_URL_SCHEMES = ("http://", "https://", "mailto:", "/", "#", "./", "../")

    @classmethod
    def sanitize_url(cls, url: str) -> str:
        """危険なURLスキーム (javascript:, data: 等) を排除し安全なURLを返却する."""
        stripped = url.strip()
        lower = stripped.lower()
        if lower.startswith(("javascript:", "vbscript:", "data:")):
            return "#"
        return stripped

    @classmethod
    def render_inline(cls, text: str) -> str:
        """インライン要素 (コード, リンク, 画像, 強調, 斜体, 取消線) をHTML化する."""
        # 1. 一旦テキスト全体をHTMLエスケープ
        escaped = html.escape(text, quote=True)

        # 2. インラインコードのプレースホルダー退避 (他の記法と混同しないため)
        code_spans: List[str] = []

        def code_repl(match: re.Match) -> str:
            code_content = match.group(1)
            code_spans.append(f"<code>{code_content}</code>")
            return f"\x00CODE{len(code_spans) - 1}\x00"

        # エスケープ後の `...` を検出
        escaped = re.sub(r"`([^`]+)`", code_repl, escaped)

        # 3. 画像: ![alt](url)
        def img_repl(match: re.Match) -> str:
            alt = match.group(1)
            url = cls.sanitize_url(match.group(2))
            return f'<img src="{url}" alt="{alt}" />'

        escaped = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", img_repl, escaped)

        # 4. リンク: [text](url)
        def link_repl(match: re.Match) -> str:
            link_text = match.group(1)
            url = cls.sanitize_url(match.group(2))
            return f'<a href="{url}">{link_text}</a>'

        escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, escaped)

        # 5. 太字: **text** または __text__
        escaped = re.sub(r"\*\*([^\*]+)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", escaped)

        # 6. 斜体: *text* または _text_
        escaped = re.sub(r"\*([^\*]+)\*", r"<em>\1</em>", escaped)
        escaped = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<em>\1</em>", escaped)

        # 7. 取り消し線: ~~text~~
        escaped = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", escaped)

        # 8. インラインコード復元
        for idx, span in enumerate(code_spans):
            escaped = escaped.replace(f"\x00CODE{idx}\x00", span)

        return escaped

    @classmethod
    def _is_block_start(cls, line: str) -> bool:
        """指定された行が段落以外のブロック要素の開始行であるかを判定する."""
        s = line.strip()
        if not s:
            return True
        if re.match(r"^```(\w*)\s*$", line):
            return True
        if re.match(r"^(#{1,6})\s+(.+)$", line):
            return True
        if re.match(r"^(?:-{3,}|\*{3,}|_{3,})\s*$", line):
            return True
        if line.startswith(">"):
            return True
        if re.match(r"^[\*\-\+]\s+(.+)$", line):
            return True
        if re.match(r"^\d+\.\s+(.+)$", line):
            return True
        if s.startswith("|") and s.endswith("|"):
            return True
        return False

    @classmethod
    def render(cls, markdown_text: str) -> str:
        """Markdown文字列をパースし、安全なHTML文字列を生成する."""
        if not markdown_text:
            return ""

        # 改行コードの統一
        normalized = markdown_text.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")

        html_blocks: List[str] = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]

            # 空行はスキップ
            if not line.strip():
                i += 1
                continue

            # 1. コードブロック (```lang ... ```)
            code_block_match = re.match(r"^```(\w*)\s*$", line)
            if code_block_match:
                lang = code_block_match.group(1).strip()
                code_lines: List[str] = []
                i += 1
                while i < n and not lines[i].startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                if i < n and lines[i].startswith("```"):
                    i += 1  # 閉じ ``` をスキップ

                code_raw = "\n".join(code_lines)
                escaped_code = html.escape(code_raw, quote=True)
                if lang:
                    html_blocks.append(
                        f'<pre><code class="language-{lang}">{escaped_code}</code></pre>'
                    )
                else:
                    html_blocks.append(f"<pre><code>{escaped_code}</code></pre>")
                continue

            # 2. 見出し (# 〜 ######)
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2).strip()
                rendered_content = cls.render_inline(content)
                html_blocks.append(f"<h{level}>{rendered_content}</h{level}>")
                i += 1
                continue

            # 3. 水平線 (---, ***, ___)
            if re.match(r"^(?:-{3,}|\*{3,}|_{3,})\s*$", line):
                html_blocks.append("<hr />")
                i += 1
                continue

            # 4. 引用 (> text)
            if line.startswith(">"):
                quote_lines: List[str] = []
                while i < n and lines[i].startswith(">"):
                    q_line = re.sub(r"^>\s?", "", lines[i])
                    quote_lines.append(q_line)
                    i += 1
                quote_text = " ".join(quote_lines).strip()
                rendered_quote = cls.render_inline(quote_text)
                html_blocks.append(f"<blockquote><p>{rendered_quote}</p></blockquote>")
                continue

            # 5. 順序なしリスト (-, *, +)
            if re.match(r"^[\*\-\+]\s+(.+)$", line):
                list_items: List[str] = []
                while i < n and re.match(r"^[\*\-\+]\s+(.+)$", lines[i]):
                    m = re.match(r"^[\*\-\+]\s+(.+)$", lines[i])
                    if m:
                        list_items.append(cls.render_inline(m.group(1).strip()))
                    i += 1
                items_html = "".join(f"<li>{item}</li>" for item in list_items)
                html_blocks.append(f"<ul>{items_html}</ul>")
                continue

            # 6. 順序付きリスト (1., 2., etc.)
            if re.match(r"^\d+\.\s+(.+)$", line):
                list_items: List[str] = []
                while i < n and re.match(r"^\d+\.\s+(.+)$", lines[i]):
                    m = re.match(r"^\d+\.\s+(.+)$", lines[i])
                    if m:
                        list_items.append(cls.render_inline(m.group(1).strip()))
                    i += 1
                items_html = "".join(f"<li>{item}</li>" for item in list_items)
                html_blocks.append(f"<ol>{items_html}</ol>")
                continue

            # 7. テーブル (| col1 | col2 |)
            if line.strip().startswith("|") and line.strip().endswith("|"):
                table_lines: List[str] = []
                while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    table_lines.append(lines[i].strip())
                    i += 1

                if len(table_lines) >= 2 and re.match(r"^\|[\s\-:|]+\|$", table_lines[1]):
                    # ヘッダー行
                    header_cells = [
                        c.strip() for c in table_lines[0].strip("|").split("|")
                    ]
                    thead_th = "".join(
                        f"<th>{cls.render_inline(cell)}</th>" for cell in header_cells
                    )
                    thead_html = f"<thead><tr>{thead_th}</tr></thead>"

                    # ボディ行
                    tbody_trs: List[str] = []
                    for row_line in table_lines[2:]:
                        row_cells = [
                            c.strip() for c in row_line.strip("|").split("|")
                        ]
                        tds = "".join(
                            f"<td>{cls.render_inline(cell)}</td>" for cell in row_cells
                        )
                        tbody_trs.append(f"<tr>{tds}</tr>")
                    tbody_html = f"<tbody>{''.join(tbody_trs)}</tbody>"
                    html_blocks.append(f"<table>{thead_html}{tbody_html}</table>")
                    continue
                else:
                    # 通常の段落として扱う
                    for tl in table_lines:
                        html_blocks.append(f"<p>{cls.render_inline(tl)}</p>")
                    continue

            # 8. 通常の段落
            paragraph_lines: List[str] = []
            while i < n and lines[i].strip() and not cls._is_block_start(lines[i]):
                paragraph_lines.append(lines[i].strip())
                i += 1
            if paragraph_lines:
                para_text = " ".join(paragraph_lines)
                html_blocks.append(f"<p>{cls.render_inline(para_text)}</p>")
            elif i < n:
                # どのブロックにも該当せず段落にも入らなかった場合の進捗保証
                html_blocks.append(f"<p>{cls.render_inline(lines[i].strip())}</p>")
                i += 1

        return "\n".join(html_blocks)
