"""端到端发布编排：fetch → parse → render → 图片上传 → 草稿。"""

import os
import re
import tempfile


def extract_title(blocks):
    for b in blocks:
        if b.get("type") == "heading" and b.get("level") == 1:
            return b.get("text", "")
    for b in blocks:
        if b.get("type") == "heading":
            return b.get("text", "")
    return ""


def extract_digest(blocks, limit=54):
    parts = []
    for b in blocks:
        t = b.get("type")
        if t in ("paragraph", "quote", "callout"):
            parts.append(b.get("text") or b.get("content", ""))
        elif t == "heading":
            parts.append(b.get("text", ""))
    text = " ".join(parts)
    text = re.sub(r'[*#`>\[\]()<_~-]', "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()[:limit]


def _hex(c):
    return c if c.startswith("#") else "#" + c


def _font(size):
    from PIL import ImageFont
    for cand in (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
                 r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\DejaVuSans.ttf"):
        if os.path.exists(cand):
            try:
                return ImageFont.truetype(cand, size)
            except Exception:
                continue
    return ImageFont.load_default()


def gen_cover(title, bg_color, out_path):
    """自动生成封面：纯色底 + 居中标题。"""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (900, 500), _hex(bg_color))
    draw = ImageDraw.Draw(img)
    font = _font(56)
    # 简单居中（不换行，超长截断）
    line = title[:18]
    try:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
    except Exception:
        w, h = 400, 56
    draw.text(((900 - w) / 2, (500 - h) / 2), line, fill="white", font=font)
    img.save(out_path, "JPEG", quality=92)
    return out_path


def _resolve_cover(cover, auto_flag, title, style, assets):
    if cover:
        return cover
    if auto_flag:
        return gen_cover(title, style["heading_color"], os.path.join(assets, "cover.jpg"))
    raise RuntimeError("缺少封面。请用 --cover <path> 指定，或加 --auto-cover 自动生成。")


def publish(url, theme, cover, auto_cover, digest, dry_run, cfg, assets_dir=None):
    """端到端发布。返回 dict：dry_run 时含 html；否则含 media_id。"""
    from .fetcher import fetch_document, export_whiteboard
    from .parser import parse_feishu_markdown
    from . import renderer
    from .renderer import render_article_body, render_preview_page
    from .themes import get_style
    from .images import trim_whitespace
    from .publisher import get_access_token, upload_image, add_material, add_draft
    from .wechat_compat import validate_html

    md = fetch_document(url)
    blocks = parse_feishu_markdown(md)
    title = extract_title(blocks) or "未命名"
    style = get_style(theme)

    # lark-cli --output 只接受相对路径（当前目录内），用固定相对目录
    assets = assets_dir or ".lark2wechat_assets"
    os.makedirs(assets, exist_ok=True)

    # 导出画板 + 裁白边，用占位 src（发布时替换为微信 URL）
    placeholders = {}
    for b in blocks:
        if b["type"] == "whiteboard":
            try:
                p = export_whiteboard(b["token"], assets)
                p = trim_whitespace(p)
                ph = f"lark2wechat://wb/{b['token']}"
                renderer.WHITEBOARD_IMAGES[b["token"]] = ph
                placeholders[ph] = p
            except Exception:
                pass  # 画板失败则保留占位块

    body = render_article_body(blocks, style)
    violations = validate_html(body)

    if dry_run:
        return {"dry_run": True, "html": render_preview_page(blocks, title, style),
                "violations": violations, "title": title}

    cfg.require_wechat()
    token = get_access_token(cfg.wechat_app_id, cfg.wechat_app_secret)

    # 上传正文图片，替换占位 src
    for ph, path in placeholders.items():
        body = body.replace(ph, upload_image(token, path))

    cover_path = _resolve_cover(cover, auto_cover, title, style, assets)
    thumb = add_material(token, cover_path)
    if not digest:
        digest = extract_digest(blocks)
    media_id = add_draft(token, title, body, thumb, digest)
    return {"media_id": media_id, "violations": violations, "title": title}
