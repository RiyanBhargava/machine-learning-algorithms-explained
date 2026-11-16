import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NOTEBOOK_PATH = ROOT / "ml-algorithms-explained.ipynb"
OUTPUT_PATH = ROOT / "ml-algorithms-explained.html"


CSS = """
:root {
  --bg: #f5f1e8;
  --panel: #fffdf8;
  --panel-2: #f8f4ec;
  --ink: #1f2430;
  --muted: #5f6675;
  --line: #ddd3c3;
  --accent: #0f766e;
  --accent-2: #b45309;
  --code-bg: #1f2430;
  --code-ink: #eef2f7;
  --shadow: 0 18px 50px rgba(31, 36, 48, 0.08);
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  background:
    radial-gradient(circle at top left, rgba(15,118,110,0.08), transparent 28%),
    radial-gradient(circle at top right, rgba(180,83,9,0.08), transparent 24%),
    linear-gradient(180deg, #f8f4ec 0%, #f5f1e8 35%, #efe8db 100%);
  color: var(--ink);
  line-height: 1.75;
}

.page {
  width: min(1120px, calc(100vw - 48px));
  margin: 32px auto 64px;
}

.hero {
  background: linear-gradient(145deg, rgba(255,253,248,0.96), rgba(248,244,236,0.96));
  border: 1px solid rgba(221, 211, 195, 0.9);
  border-radius: 28px;
  padding: 40px 44px 34px;
  box-shadow: var(--shadow);
  position: relative;
  overflow: hidden;
}

.hero::after {
  content: "";
  position: absolute;
  inset: auto -40px -55px auto;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(15,118,110,0.16), transparent 68%);
  pointer-events: none;
}

.eyebrow {
  margin: 0 0 10px;
  font-family: "Trebuchet MS", "Segoe UI", sans-serif;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--accent);
}

.hero h1 {
  margin: 0;
  font-size: clamp(2.4rem, 5vw, 4.1rem);
  line-height: 1.05;
  letter-spacing: -0.03em;
}

.hero p {
  margin: 16px 0 0;
  max-width: 760px;
  color: var(--muted);
  font-size: 1.08rem;
}

.topbar {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin: 18px 0 0;
}

.pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(15,118,110,0.08);
  border: 1px solid rgba(15,118,110,0.18);
  font-family: "Trebuchet MS", "Segoe UI", sans-serif;
  font-size: 0.92rem;
  color: #104b46;
}

.content {
  margin-top: 26px;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 18px;
}

.cell {
  background: rgba(255,253,248,0.92);
  border: 1px solid rgba(221, 211, 195, 0.9);
  border-radius: 22px;
  padding: 26px 30px;
  box-shadow: var(--shadow);
}

.cell.markdown { padding-top: 22px; }
.cell.code { background: linear-gradient(180deg, rgba(255,252,245,0.96), rgba(250,246,239,0.96)); }

.cell h1, .cell h2, .cell h3, .cell h4 {
  margin-top: 0;
  color: #18202a;
  line-height: 1.18;
  letter-spacing: -0.02em;
}

.cell h1 {
  font-size: 2.1rem;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(221, 211, 195, 0.85);
}

.cell h2 {
  font-size: 1.62rem;
  margin-bottom: 14px;
}

.cell h3 {
  font-size: 1.16rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--accent);
  font-family: "Trebuchet MS", "Segoe UI", sans-serif;
}

.cell p, .cell li, .cell blockquote {
  font-size: 1.03rem;
}

.cell p { margin: 0 0 14px; }
.cell ul, .cell ol { margin: 8px 0 16px 22px; padding: 0; }
.cell li + li { margin-top: 8px; }

.cell hr {
  border: 0;
  border-top: 1px solid rgba(221, 211, 195, 0.85);
  margin: 22px 0;
}

.cell a {
  color: #0f5f94;
  text-decoration: none;
  border-bottom: 1px solid rgba(15,95,148,0.2);
}

.cell a:hover { border-bottom-color: rgba(15,95,148,0.75); }

.cell strong { color: #18202a; }
.cell em { color: #5c4323; }

.inline-code {
  font-family: Consolas, "Courier New", monospace;
  background: #f1e8d8;
  border: 1px solid #e2d5bc;
  border-radius: 7px;
  padding: 0.1rem 0.35rem;
  font-size: 0.92em;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  font-family: "Trebuchet MS", "Segoe UI", sans-serif;
}

.code-label {
  font-size: 0.84rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.code-note {
  font-size: 0.88rem;
  color: #7a6040;
}

pre {
  margin: 0;
  overflow-x: auto;
  border-radius: 18px;
  padding: 20px 22px;
  background: linear-gradient(180deg, #202733, #171c25);
  color: var(--code-ink);
  border: 1px solid rgba(16, 22, 31, 0.55);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}

pre code {
  font-family: Consolas, "SFMono-Regular", "Courier New", monospace;
  font-size: 0.92rem;
  line-height: 1.7;
  white-space: pre;
}

blockquote {
  margin: 18px 0;
  padding: 10px 0 10px 18px;
  border-left: 3px solid rgba(15,118,110,0.35);
  color: #4c5564;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0 18px;
  font-size: 0.96rem;
  overflow: hidden;
  border-radius: 16px;
}

thead th {
  background: #efe7d8;
  color: #30261a;
  font-family: "Trebuchet MS", "Segoe UI", sans-serif;
  text-align: left;
}

th, td {
  border: 1px solid rgba(221, 211, 195, 0.8);
  padding: 10px 12px;
  vertical-align: top;
}

tbody tr:nth-child(even) { background: rgba(248, 244, 236, 0.78); }

.image-wrap {
  margin: 18px 0 10px;
}

.image-wrap img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 18px;
  border: 1px solid rgba(221, 211, 195, 0.92);
  box-shadow: 0 14px 35px rgba(31, 36, 48, 0.08);
  background: white;
}

.section-anchor {
  color: inherit;
  text-decoration: none;
}

.footer {
  margin: 26px 0 0;
  text-align: center;
  color: var(--muted);
  font-size: 0.95rem;
}

@media (max-width: 840px) {
  .page { width: min(100vw - 24px, 1120px); margin-top: 12px; }
  .hero { padding: 28px 22px 24px; border-radius: 22px; }
  .cell { padding: 22px 18px; border-radius: 18px; }
  .hero h1 { font-size: clamp(2rem, 10vw, 3rem); }
  .cell h1 { font-size: 1.72rem; }
  .cell h2 { font-size: 1.42rem; }
}
"""


def convert_inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r'<code class="inline-code">\1</code>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def render_table(lines_block):
    rows = []
    for raw in lines_block:
        stripped = raw.strip()
        if not stripped:
            continue
        if set(stripped.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            continue
        parts = [convert_inline(part.strip()) for part in stripped.strip("|").split("|")]
        rows.append(parts)
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:]
    head_html = "".join(f"<th>{cell}</th>" for cell in header)
    body_html = ""
    for row in body:
        body_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    return f"<table><thead><tr>{head_html}</tr></thead><tbody>{body_html}</tbody></table>"


def render_markdown(source_lines):
    src = "".join(source_lines).replace("\r\n", "\n")
    lines_in = src.split("\n")
    out = []
    paragraph = []
    list_stack = []
    table_buffer = []
    in_code_fence = False
    fence_lang = ""
    fence_lines = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            out.append(f"<p>{convert_inline(' '.join(paragraph).strip())}</p>")
            paragraph = []

    def flush_lists(target_level=0):
        nonlocal list_stack
        while len(list_stack) > target_level:
            out.append(f"</{list_stack.pop()}>")

    def flush_table():
        nonlocal table_buffer
        if table_buffer:
            out.append(render_table(table_buffer))
            table_buffer = []

    def flush_code():
        nonlocal fence_lines, fence_lang
        code_html = html.escape("\n".join(fence_lines))
        out.append(f'<pre><code class="language-{html.escape(fence_lang)}">{code_html}</code></pre>')
        fence_lines = []
        fence_lang = ""

    i = 0
    while i < len(lines_in):
        raw = lines_in[i]
        line = raw.rstrip()
        stripped = line.strip()

        if in_code_fence:
            if stripped.startswith("```"):
                flush_code()
                in_code_fence = False
            else:
                fence_lines.append(raw)
            i += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            flush_table()
            flush_lists()
            in_code_fence = True
            fence_lang = stripped[3:].strip()
            i += 1
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            flush_lists()
            table_buffer.append(raw)
            i += 1
            continue
        else:
            flush_table()

        if not stripped:
            flush_paragraph()
            flush_lists()
            i += 1
            continue

        if stripped == "---":
            flush_paragraph()
            flush_lists()
            out.append("<hr>")
            i += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_lists()
            level = len(heading_match.group(1))
            content = convert_inline(heading_match.group(2))
            slug = re.sub(r"[^a-z0-9]+", "-", heading_match.group(2).lower()).strip("-")
            out.append(f'<h{level} id="{slug}"><a class="section-anchor" href="#{slug}">{content}</a></h{level}>')
            i += 1
            continue

        image_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if image_match:
            flush_paragraph()
            flush_lists()
            alt = html.escape(image_match.group(1))
            src_path = html.escape(image_match.group(2))
            out.append(f'<div class="image-wrap"><img src="{src_path}" alt="{alt}"></div>')
            i += 1
            continue

        quote_match = re.match(r"^>\s?(.*)$", stripped)
        if quote_match:
            flush_paragraph()
            flush_lists()
            out.append(f"<blockquote>{convert_inline(quote_match.group(1))}</blockquote>")
            i += 1
            continue

        ul_match = re.match(r"^(\s*)-\s+(.*)$", raw)
        ol_match = re.match(r"^(\s*)\d+\.\s+(.*)$", raw)
        if ul_match or ol_match:
            flush_paragraph()
            list_type = "ul" if ul_match else "ol"
            item_text = ul_match.group(2) if ul_match else ol_match.group(2)
            indent = len((ul_match.group(1) if ul_match else ol_match.group(1)).replace("\t", "    "))
            level = indent // 2 + 1
            while len(list_stack) < level:
                out.append(f"<{list_type}>")
                list_stack.append(list_type)
            while len(list_stack) > level:
                out.append(f"</{list_stack.pop()}>")
            if list_stack and list_stack[-1] != list_type:
                out.append(f"</{list_stack.pop()}>")
                out.append(f"<{list_type}>")
                list_stack.append(list_type)
            out.append(f"<li>{convert_inline(item_text.strip())}</li>")
            i += 1
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    flush_table()
    flush_lists()
    if in_code_fence:
        flush_code()
    return "\n".join(out)


def render_code(source_lines):
    code_text = "".join(source_lines).rstrip("\n")
    escaped = html.escape(code_text)
    return f"""
<div class="code-header">
  <div class="code-label">Code Cell</div>
  <div class="code-note">Source preserved from the notebook</div>
</div>
<pre><code>{escaped}</code></pre>
"""


def build_html(cells):
    body_parts = []
    first_heading_handled = False

    for cell in cells:
        if cell.get("cell_type") == "markdown":
            source = "".join(cell.get("source", []))
            if not first_heading_handled and source.lstrip().startswith("# "):
                lines_src = source.strip().splitlines()
                title = lines_src[0].replace("#", "", 1).strip()
                subtitle = " ".join(line.strip() for line in lines_src[1:] if line.strip())
                body_parts.append(f"""
<section class="hero">
  <p class="eyebrow">Notebook Presentation</p>
  <h1>{html.escape(title)}</h1>
  <p>{convert_inline(subtitle)}</p>
  <div class="topbar">
    <span class="pill">Same notebook content</span>
    <span class="pill">Custom HTML presentation</span>
    <span class="pill">Professional learning layout</span>
  </div>
</section>
""")
                first_heading_handled = True
                continue
            rendered = render_markdown(cell.get("source", []))
            if rendered.strip():
                body_parts.append(f'<section class="cell markdown">{rendered}</section>')
        elif cell.get("cell_type") == "code":
            rendered = render_code(cell.get("source", []))
            body_parts.append(f'<section class="cell code">{rendered}</section>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Machine Learning Algorithms</title>
  <style>{CSS}</style>
</head>
<body>
  <main class="page">
    <div class="content">
      {''.join(body_parts)}
    </div>
    <p class="footer">Generated from <code class="inline-code">ml-algorithms-explained.ipynb</code> without modifying the notebook source.</p>
  </main>
</body>
</html>
"""


def main():
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    html_doc = build_html(notebook["cells"])
    OUTPUT_PATH.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
