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


def _precheck(body, title):
    """发布前预检：标题/正文非空、图片全上传（无占位）。失败抛可操作错误。"""
    if not title.strip():
        raise RuntimeError("文章标题为空，无法发布。")
    if not body.strip():
        raise RuntimeError("正文为空，无法发布。")
    if "[图片占位]" in body:
        raise RuntimeError("正文含未上传的图片占位（画板/图片导出失败）。检查 lark-cli 授权或重试。")
    if "lark2wechat://" in body:
        raise RuntimeError("正文含未替换的图片 src（上传失败）。")
    if "internal-api-drive-stream.feishu.cn" in body:
        raise RuntimeError("正文含未替换的飞书图片 URL（下载/上传失败）。检查网络或重试。")


def _record(title, theme, media_id, updated=False):
    """记录发布到本地历史（失败静默，不影响发布）。"""
    try:
        from .history import record_publish
        record_publish(title, theme, media_id, updated=updated)
    except Exception:
        pass


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
    """自动生成封面：cosmic 深空宇宙模板（HTML→Edge 截图）；playwright 缺失时降级纯色。"""
    from .cover import render_cover
    try:
        return render_cover(title, out_path)
    except Exception:
        return _gen_cover_plain(title, bg_color, out_path)


def _gen_cover_plain(title, bg_color, out_path):
    """降级封面：纯色底 + 居中标题（playwright/Edge 不可用时）。"""
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


def publish(url, theme, cover, auto_cover, digest, dry_run, cfg, assets_dir=None, update_id=None):
    """端到端发布。返回 dict：dry_run 时含 html；否则含 media_id。"""
    from .fetcher import fetch_document, export_whiteboard, download_media, download_image_url
    from .parser import parse_feishu_markdown
    from . import renderer
    from .renderer import render_article_body, render_preview_page
    from .themes import get_style
    from .images import trim_whitespace
    from .publisher import get_access_token, upload_image, add_material, add_draft, update_draft
    from .wechat_compat import validate_html

    md = fetch_document(url)
    blocks = parse_feishu_markdown(md)
    title = extract_title(blocks) or "未命名"
    style = get_style(theme)

    # 正文移除作为标题的 H1（标题已作为草稿 title，正文里不再重复）
    title_idx = next((i for i, b in enumerate(blocks)
                      if b.get("type") == "heading" and b.get("level") == 1), -1)
    body_blocks = (blocks[:title_idx] + blocks[title_idx + 1:]) if title_idx >= 0 else blocks

    # lark-cli --output 只接受相对路径（当前目录内），用固定相对目录
    assets = assets_dir or ".lark2wechat_assets"
    os.makedirs(assets, exist_ok=True)

    # 导出画板 + 文档图片，裁白边，用占位 src（发布时替换为微信 URL）
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
    for b in blocks:
        if b["type"] == "image" and b.get("token") and b["token"] not in renderer.IMAGE_SOURCES:
            try:
                p = download_media(b["token"], assets)
                p = trim_whitespace(p)
                ph = f"lark2wechat://img/{b['token']}"
                renderer.IMAGE_SOURCES[b["token"]] = ph
                placeholders[ph] = p
            except Exception:
                pass  # 图片下载失败则保留占位块
    # 标准 markdown ![](url) 形式的正文图片（如飞书 authcode URL）：无 token，直接下载 src
    for b in blocks:
        if b["type"] == "image" and not b.get("token") and b.get("src"):
            src = b["src"]
            if src in placeholders or not src.startswith(("http://", "https://")):
                continue
            try:
                p = download_image_url(src, assets)
                p = trim_whitespace(p)
                placeholders[src] = p  # 用原始 src 作占位 key，复用下方 body.replace
            except Exception:
                pass  # 下载失败则 _precheck 拦截

    body = render_article_body(body_blocks, style)
    violations = validate_html(body)

    if dry_run:
        return {"dry_run": True, "html": render_preview_page(body_blocks, title, style),
                "violations": violations, "title": title}

    cfg.require_wechat()
    token = get_access_token(cfg.wechat_app_id, cfg.wechat_app_secret)

    # 上传正文图片，替换占位 src
    for ph, path in placeholders.items():
        body = body.replace(ph, upload_image(token, path))

    _precheck(body, title)

    cover_path = _resolve_cover(cover, auto_cover, title, style, assets)
    thumb = add_material(token, cover_path)
    if not digest:
        digest = extract_digest(blocks)
    if update_id:
        update_draft(token, update_id, title, body, thumb, digest)
        _record(title, theme, update_id, updated=True)
        return {"media_id": update_id, "updated": True, "violations": violations, "title": title}
    media_id = add_draft(token, title, body, thumb, digest)
    _record(title, theme, media_id, updated=False)
    return {"media_id": media_id, "violations": violations, "title": title}
