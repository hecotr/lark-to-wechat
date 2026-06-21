"""图片后处理：裁白边、转码、收集正文图片。"""

import os
import re
from PIL import Image, ImageChops


def trim_whitespace(path: str, out_path: str = None) -> str:
    """裁掉图片白边（画板导出常有大片白边）。"""
    im = Image.open(path).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bbox = ImageChops.difference(im, bg).getbbox()
    if not bbox:
        return path
    trimmed = im.crop(bbox)
    out_path = out_path or _suffix(path, "_trimmed")
    trimmed.save(out_path, "JPEG", quality=92)
    return out_path


def to_jpg(path: str, out_path: str = None) -> str:
    """转为 JPG（处理 WebP 封面等）。"""
    im = Image.open(path).convert("RGB")
    out_path = out_path or _suffix(path, "", ext=".jpg")
    im.save(out_path, "JPEG", quality=92)
    return out_path


def _suffix(path: str, sfx: str, ext: str = None) -> str:
    root, old_ext = os.path.splitext(path)
    return root + sfx + (ext or old_ext)


def collect_image_sources(html: str):
    """扫描 HTML，返回所有 <img src=...> 的 src 列表。"""
    return re.findall(r'<img[^>]+src="([^"]+)"', html)
