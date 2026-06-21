"""主题加载、校验与转换。

每套主题 = themes/<name>.yaml（参数）+ themes/<name>.md（DNA 气质描述）。
嵌套 yaml 经 theme_to_style 展平为 renderer 用的扁平 STYLE。
"""

import yaml
from pathlib import Path

THEMES_DIR = Path(__file__).parent  # themes/ 目录本身

_REQUIRED_TOP = ["name", "base", "heading", "accent"]
_REQUIRED_BASE = ["font_family", "text_color", "text_size", "line_height"]
_REQUIRED_HEADING_NODES = ["h1", "h2", "h3"]


def list_themes():
    """返回所有可用主题名（按字母序）。"""
    return sorted(p.stem for p in THEMES_DIR.glob("*.yaml"))


def load_theme(name):
    """加载并校验主题 yaml，返回原始嵌套字典。"""
    path = THEMES_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"主题不存在：{name}（可用主题：{', '.join(list_themes()) or '无'}）")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    validate_theme(name, data)
    return data


def validate_theme(name, data):
    """校验主题 schema 完整性。"""
    for k in _REQUIRED_TOP:
        if k not in data:
            raise ValueError(f"主题 {name} 缺少顶层字段：{k}")
    for k in _REQUIRED_BASE:
        if k not in data["base"]:
            raise ValueError(f"主题 {name} 的 base 缺少字段：{k}")
    h = data["heading"]
    if "color" not in h:
        raise ValueError(f"主题 {name} 的 heading 缺少字段：color")
    for hk in _REQUIRED_HEADING_NODES:
        if hk not in h:
            raise ValueError(f"主题 {name} 的 heading 缺少字段：{hk}")
        for f in ("size", "weight"):
            if f not in h[hk]:
                raise ValueError(f"主题 {name} 的 heading.{hk} 缺少字段：{f}")
    if "primary" not in data["accent"]:
        raise ValueError(f"主题 {name} 的 accent 缺少字段：primary")


def theme_to_style(data):
    """把嵌套主题字典展平为 renderer 用的扁平 STYLE。"""
    b = data["base"]; h = data["heading"]; a = data["accent"]
    c = data.get("callout", {}); cd = data.get("code", {})
    t = data.get("table", {}); q = data.get("quote", {})
    return {
        "font": b["font_family"],
        "heading_font": h.get("font_family", b["font_family"]),
        "text_color": b["text_color"],
        "body_bg": b.get("background", "#FFFFFF"),
        "text_size": b["text_size"],
        "line_height": b["line_height"],
        "primary": a["primary"],
        "highlight": a.get("highlight", a["primary"]),
        "bold_color": a.get("bold_color"),
        "heading_color": h["color"],
        "h1_size": h["h1"]["size"], "h1_weight": str(h["h1"]["weight"]),
        "h2_size": h["h2"]["size"], "h2_weight": str(h["h2"]["weight"]),
        "h3_size": h["h3"]["size"], "h3_weight": str(h["h3"]["weight"]),
        "table_border": t.get("border", "#e0e0e0"),
        "table_header_bg": t.get("header_bg", "#f7f7f7"),
        "code_bg": cd.get("block_bg", "#f7f7f7"),
        "code_text": cd.get("text_color", "#333333"),
        "code_inline_bg": cd.get("inline_bg", "#f0f0f0"),
        "inline_code_color": cd.get("inline_color"),
        "callout_border": c.get("border_color", "#e0e0e0"),
        "callout_bg": c.get("bg"),
        "quote_border": q.get("border_color", "#d0d0d0"),
        "quote_bg": q.get("bg"),
        "quote_color": q.get("color", "#666666"),
    }


def get_style(name):
    """加载主题并返回扁平 STYLE。"""
    return theme_to_style(load_theme(name))
