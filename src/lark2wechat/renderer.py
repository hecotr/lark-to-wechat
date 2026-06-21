"""IR → 微信兼容 HTML 渲染器。

Phase 1：style 参数化（由 themes/*.yaml 经 theme_to_style 注入）+ 新块渲染（quote/image/equation/todo）。
Phase 2：输出统一过微信兼容性校验器。
"""

import re
import os
import html
import base64

# 画板图片 token → data URI（预览）/ 微信 URL（发布）。Phase 4/5 由外部填充。
WHITEBOARD_IMAGES = {}
# 文档内图片 token → src（同上）。
IMAGE_SOURCES = {}

# 默认扁平样式（兜底；正式渲染由 theme_to_style 注入）。
DEFAULT_STYLE = {
    "font": "-apple-system, BlinkMacSystemFont, Helvetica Neue, PingFang SC, Microsoft YaHei, sans-serif",
    "text_color": "#333333",
    "body_bg": "#FFFFFF",
    "text_size": "15px",
    "line_height": "2em",
    "primary": "#576b95",
    "highlight": "#576b95",
    "h1_size": "22px", "h1_weight": "700",
    "h2_size": "18px", "h2_weight": "700",
    "h3_size": "16px", "h3_weight": "600",
    "heading_color": "#1a1a1a",
    "table_border": "#e0e0e0",
    "table_header_bg": "#f7f7f7",
    "code_bg": "#f7f7f7",
    "code_text": "#333333",
    "code_inline_bg": "#f0f0f0",
    "callout_border": "#e0e0e0",
    "quote_border": "#d0d0d0",
    "quote_color": "#666666",
}


def _rich(text, style):
    """富文本: 颜色标记 / 加粗 / 行内代码 / 链接。

    先把 <text color> 颜色标记提取为占位符，再 html.escape 全文
    （防止正文里的裸尖括号如 <id> 被当成 HTML 标签，破坏微信兼容性），
    然后处理 markdown 标记，最后还原颜色占位。
    """
    color_map = {"green": "#34C759", "red": "#FF3B30", "blue": "#007AFF", "yellow": "#F5A623"}

    def extract_color(m):
        c = color_map.get(m.group(1), m.group(1))
        return f"\x00C:{c}\x00{m.group(2)}\x00/C\x00"
    text = re.sub(r'<text\s+color="([^"]*)">(.*?)</text>', extract_color, text, flags=re.DOTALL)

    text = html.escape(text, quote=False)

    bold_color = style.get("bold_color")
    bold_open = f'<strong style="color:{bold_color};">' if bold_color else '<strong>'
    text = re.sub(r'\*\*(.*?)\*\*', bold_open + r'\1</strong>', text)
    # 斜体：*xx* → <em>（必须在加粗之后，避免误吃 **）
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    icc = style.get("inline_code_color")
    code_clr = f"color:{icc};" if icc else ""
    text = re.sub(r'`([^`]+)`',
        f'<code style="{code_clr}background-color:{style["code_inline_bg"]};padding:1px 3px;font-size:0.9em;'
        f'font-family:Menlo,Monaco,Courier New,monospace;">\\1</code>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
        f'<a href="\\2" style="color:{style["primary"]};text-decoration:none;">\\1</a>', text)

    text = re.sub(r'\x00C:([^\x00]*?)\x00(.*?)\x00/C\x00',
        lambda m: f'<strong style="color:{m.group(1)};">{m.group(2)}</strong>', text, flags=re.DOTALL)
    return text


def _section(content, style_str):
    """统一用 section 包裹，WeChat 兼容。"""
    return f'<section style="{style_str}">{content}</section>'


def render_block(block, style=None):
    style = style or DEFAULT_STYLE
    f = style["font"]; hf = style.get("heading_font", f); tc = style["text_color"]; bs = style["text_size"]; lh = style["line_height"]

    if block["type"] == "heading" and block["level"] == 1:
        return _section(_rich(block["text"], style),
            f"margin:32px 0 16px 0;padding:0;"
            f"font-size:{style['h1_size']};font-weight:{style['h1_weight']};color:{style['heading_color']};"
            f"font-family:{hf};line-height:1.5;")

    if block["type"] == "heading" and block["level"] == 2:
        return _section(_rich(block["text"], style),
            f"margin:28px 0 12px 0;padding:0;"
            f"font-size:{style['h2_size']};font-weight:{style['h2_weight']};color:{style['heading_color']};"
            f"font-family:{hf};line-height:1.5;")

    if block["type"] == "heading":
        return _section(_rich(block["text"], style),
            f"margin:20px 0 8px 0;"
            f"font-size:{style['h3_size']};font-weight:{style['h3_weight']};color:{style['heading_color']};"
            f"font-family:{hf};line-height:1.6;")

    if block["type"] == "paragraph":
        text = _rich(block["text"], style)
        if not text:
            return ""
        return _section(text,
            f"margin:0 0 12px 0;font-size:{bs};line-height:{lh};color:{tc};font-family:{f};")

    if block["type"] == "quote":
        content = _rich(block["content"], style).replace('\n', '<br/>')
        bg = style.get("quote_bg")
        pad_bg = (f"background-color:{bg};border-radius:0 6px 6px 0;padding:8px 14px;"
                  if bg else "padding:8px 0 8px 14px;")
        return _section(content,
            f"margin:12px 0;{pad_bg}"
            f"font-size:14px;line-height:1.8;color:{style['quote_color']};font-family:{f};"
            f"border-left:3px solid {style['quote_border']};")

    if block["type"] == "callout":
        content = _rich(block["content"], style).replace('\n', '<br/>')
        emoji = f'<span>{block["emoji"]} </span>' if block["emoji"] else ''
        bg = style.get("callout_bg")
        pad_bg = (f"background-color:{bg};border-radius:0 6px 6px 0;padding:8px 14px;"
                  if bg else "padding:8px 0 8px 12px;")
        return _section(emoji + content,
            f"margin:12px 0;{pad_bg}"
            f"font-size:14px;line-height:1.85;color:{tc};font-family:{f};"
            f"border-left:2px solid {style['callout_border']};")

    if block["type"] == "grid":
        cols = block["columns"]
        if not cols:
            return ""
        total = sum(c["width"] for c in cols)
        cells = ""
        for col in cols:
            pct = round(col["width"] / total * 100)
            inner = "".join(render_block(it, style) for it in col["items"])
            cells += f'<td style="width:{pct}%;padding:2px;vertical-align:top;">{inner}</td>'
        return f'<table style="width:100%;border-collapse:separate;border-spacing:4px 0;margin:8px 0;"><tr>{cells}</tr></table>'

    if block["type"] == "table":
        rows = block["rows"]
        if not rows:
            return ""
        ws = block.get("widths", []); tw = sum(ws) if ws else 100
        html_rows = ""
        for ri, row in enumerate(rows):
            is_hdr = ri == 0 and block.get("has_header")
            cells = ""
            for ci, cell in enumerate(row):
                cc = _rich(cell.strip(), style)
                wp = round(ws[ci] / tw * 100) if ci < len(ws) else 0
                ws_ = f'width:{wp}%;' if wp else ''
                if is_hdr:
                    cells += (
                        f'<td style="{ws_}padding:6px 8px;background-color:{style["table_header_bg"]};'
                        f'color:{style["heading_color"]};font-weight:600;font-size:13px;'
                        f'border:1px solid {style["table_border"]};text-align:left;font-family:{f};">{cc}</td>')
                else:
                    cells += (
                        f'<td style="{ws_}padding:6px 8px;'
                        f'font-size:13px;color:{tc};border:1px solid {style["table_border"]};'
                        f'text-align:left;font-family:{f};">{cc}</td>')
            html_rows += f'<tr>{cells}</tr>'
        return f'<table style="width:100%;border-collapse:collapse;margin:12px 0;font-size:13px;">{html_rows}</table>'

    if block["type"] == "code":
        # 微信不吃 <pre> 的 white-space，多行代码会塌成一行 → 用 <br/> 显式换行
        content = block["content"].replace("\n", "<br/>")
        return _section(
            f'<section style="margin:12px 0;padding:10px 12px;background-color:{style["code_bg"]};border-radius:4px;">'
            f'<section style="margin:0;font-size:13px;line-height:1.6;'
            f'font-family:Menlo,Monaco,Courier New,monospace;color:{style["code_text"]};'
            f'word-wrap:break-word;">{content}</section></section>',
            "")

    if block["type"] == "equation":
        # Phase 1：降级为 code 块纯文本。Phase 5 publisher 用 matplotlib 转图替换。
        latex = html.escape(block.get("latex", ""))
        return _section(
            f'<section style="margin:12px 0;padding:10px 12px;background-color:{style["code_bg"]};">'
            f'<pre style="margin:0;font-size:14px;line-height:1.6;'
            f'font-family:Menlo,Monaco,Courier New,monospace;color:{style["code_text"]};'
            f'white-space:pre-wrap;">{latex}</pre></section>',
            "")

    if block["type"] == "image":
        src = block.get("src") or IMAGE_SOURCES.get(block.get("token", ""), "")
        alt = block.get("alt", "")
        if src:
            return (f'<section style="margin:12px 0;text-align:center;">'
                    f'<img src="{src}" alt="{html.escape(alt)}" style="width:100%;" /></section>')
        return (f'<section style="margin:12px 0;padding:20px 16px;text-align:center;'
                f'background-color:#f7f7f7;font-size:13px;color:#999999;font-family:{f};">[图片占位]</section>')

    if block["type"] == "whiteboard":
        token = block.get("token", "")
        img_src = WHITEBOARD_IMAGES.get(token)
        if img_src:
            return (f'<section style="margin:12px 0;text-align:center;">'
                    f'<img src="{img_src}" style="width:100%;" /></section>')
        return (f'<section style="margin:12px 0;padding:20px 16px;text-align:center;'
                f'background-color:#f7f7f7;font-size:13px;color:#999999;font-family:{f};">[图片占位]</section>')

    if block["type"] == "olist":
        items = "".join(
            f'<p style="margin:2px 0;font-size:{bs};line-height:{lh};color:{tc};font-family:{f};">'
            f'{idx+1}. {_rich(item, style)}</p>'
            for idx, item in enumerate(block["items"]))
        return f'<section style="margin:8px 0 12px 0;">{items}</section>'

    if block["type"] == "ulist":
        items = "".join(
            f'<p style="margin:2px 0;font-size:{bs};line-height:{lh};color:{tc};font-family:{f};">'
            f'<span style="margin-right:4px;">•</span>{_rich(item, style)}</p>'
            for item in block["items"])
        return f'<section style="margin:8px 0 12px 0;">{items}</section>'

    if block["type"] == "todo":
        items = "".join(
            f'<p style="margin:2px 0;font-size:{bs};line-height:{lh};color:{tc};font-family:{f};">'
            f'<span style="margin-right:6px;">{"☑" if it["checked"] else "☐"}</span>{_rich(it["text"], style)}</p>'
            for it in block["items"])
        return f'<section style="margin:8px 0 12px 0;">{items}</section>'

    if block["type"] == "hr":
        return (
            f'<section style="margin:20px 0;">'
            f'<table style="width:100%;border-collapse:collapse;">'
            f'<tr><td style="height:1px;background-color:{style["table_border"]};font-size:1px;line-height:1px;">\xa0</td></tr>'
            f'</table></section>')

    return ""


def _embed_base64(filepath):
    """本地图片 → base64 data URI（预览页用；发布时改用微信 uploadimg URL）。Phase 4 迁到 images.py。"""
    with open(filepath, "rb") as fh:
        data = base64.b64encode(fh.read()).decode("ascii")
    ext = os.path.splitext(filepath)[1].lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{data}"


def render_article_body(blocks, style=None):
    """渲染正文 HTML 片段（给 publisher 用）。"""
    return "".join(render_block(b, style) for b in blocks)


def render_preview_page(blocks, title="", style=None):
    """渲染带'复制文章'按钮的预览页（给 render / --dry-run 用）。"""
    style = style or DEFAULT_STYLE
    body = render_article_body(blocks, style)
    f = style["font"]
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
body {{ margin: 0; padding: 0; background-color: #f5f5f5; }}
.top-bar {{ background-color: #fff; border-bottom: 1px solid #e8e8e8;
  padding: 8px 16px; font-family: {f}; }}
.top-bar-inner {{ max-width: 580px; margin: 0 auto; }}
.copy-btn {{ padding: 5px 14px; background-color: #576b95; color: #fff;
  border: none; font-size: 12px; cursor: pointer; font-family: {f}; }}
.article {{ max-width: 580px; margin: 12px auto; background-color: {style['body_bg']};
  padding: 24px 20px; font-family: {f}; }}
</style>
</head>
<body>
<div class="top-bar">
  <div class="top-bar-inner">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <span style="font-size:13px;color:#333;font-weight:600;">{html.escape(title)}</span>
      <button class="copy-btn" onclick="copyArticle(this)">复制文章</button>
    </div>
  </div>
</div>
<div class="article" id="article-content">
  {body}
</div>
<script>
function copyArticle(btn) {{
  var article = document.getElementById('article-content');
  var range = document.createRange();
  range.selectNodeContents(article);
  var sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  try {{
    navigator.clipboard.write([new ClipboardItem({{
      'text/html': new Blob([article.innerHTML], {{type:'text/html'}}),
      'text/plain': new Blob([article.innerText], {{type:'text/plain'}})
    }})]).then(ok).catch(function() {{ document.execCommand('copy'); ok(); }});
  }} catch(e) {{ document.execCommand('copy'); ok(); }}
  function ok() {{ btn.textContent='已复制!'; btn.style.backgroundColor='#34C759';
    setTimeout(function() {{ btn.textContent='复制文章'; btn.style.backgroundColor='#576b95'; }}, 2000); }}
  sel.removeAllRanges();
}}
</script>
</body>
</html>'''
