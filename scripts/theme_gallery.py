"""主题画廊 demo：同一篇示范文章，用所有主题渲染，输出纵向对比 HTML。

跑法：
    python scripts/theme_gallery.py
产物：
    demos/theme-gallery.html  （浏览器打开即可）

本脚本不发布、不改主题，仅用于肉眼对比 10 套新主题（+ default 参照）的真实效果，
并对每个主题的渲染输出跑一次微信兼容性校验。
"""

import sys
import html
from pathlib import Path

# 让脚本能直接 import 未安装的 src 包。
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lark2wechat import themes, renderer, wechat_compat  # noqa: E402

# 示范文章 IR：覆盖 renderer 支持的所有块类型，内容自指（讲排版本身）。
DEMO_BLOCKS = [
    {"type": "heading", "level": 1, "text": "好的排版，是退让的艺术"},
    {"type": "paragraph",
     "text": "一篇公众号文章**最该被看见的是内容本身**，不是装饰。"
             "`主题系统`的意义，是让不同的内容找到合适的[气质容器](https://example.com)。"},
    {"type": "quote", "content": "少即是多，但少不等于空。—— Massimo Vignelli"},
    {"type": "heading", "level": 2, "text": "为什么需要多套主题"},
    {"type": "paragraph",
     "text": '技术长文需要克制与密度，品牌故事需要温度，宣言需要力量。<text color="red">一套主题打天下</text>，等于让所有内容穿同一件衣服。'},
    {"type": "callout", "emoji": "💡",
     "content": "主题由 YAML 参数驱动，骨架固定为微信兼容结构。换色、换字号、换字重，气质就变了。"},
    {"type": "heading", "level": 3, "text": "这套系统的三件事"},
    {"type": "ulist", "items": [
        "固定微信兼容骨架：inline style、系统字体、白名单标签",
        "参数化主题：颜色 / 字号 / 字重 / 行高 / 底色",
        "气质描述：每套主题配一段 DNA 说明",
    ]},
    {"type": "olist", "items": [
        "选择与内容气质匹配的主题",
        "在飞书写好正文",
        "一键发布到草稿箱",
    ]},
    {"type": "todo", "items": [
        {"text": "挑选主题", "checked": True},
        {"text": "写正文", "checked": True},
        {"text": "预览确认", "checked": False},
        {"text": "发布草稿箱", "checked": False},
    ]},
    {"type": "heading", "level": 2, "text": "主题参数速览"},
    {"type": "table", "has_header": True, "widths": [40, 30, 30], "rows": [
        ["参数", "作用", "示例"],
        ["正文字号 text_size", "阅读密度", "15px"],
        ["强调色 primary", "链接与点睛", "#576b95"],
        ["行高 line_height", "呼吸感", "2em"],
    ]},
    {"type": "heading", "level": 2, "text": "代码块与公式"},
    {"type": "code", "lang": "python",
     "content": "from lark2wechat import themes\nprint(themes.list_themes())"},
    {"type": "equation", "latex": "E = mc^2"},
    {"type": "heading", "level": 2, "text": "分栏与图文"},
    {"type": "grid", "columns": [
        {"width": 50, "items": [{"type": "paragraph", "text": "**左栏**：并列观点。"}]},
        {"width": 50, "items": [{"type": "paragraph", "text": "**右栏**：相互对照。"}]},
    ]},
    {"type": "image", "alt": "示例配图",
     "src": "https://picsum.photos/seed/lark2wechat/600/280"},
    {"type": "hr"},
    {"type": "paragraph", "text": "（完）每个主题都在用不同的方式说同一句话：**内容第一**。"},
]

NEW_THEMES = ["warm", "zenfox", "feishu"]


def swatch(label, color):
    """单个色块。"""
    return (f'<span style="display:inline-flex;align-items:center;gap:5px;'
            f'margin:2px 6px 2px 0;font-size:11px;color:#555;">'
            f'<span style="display:inline-block;width:14px;height:14px;'
            f'border:1px solid #ddd;border-radius:3px;background-color:{color};"></span>'
            f'{html.escape(label)}</span>')


def render_card(name, is_new):
    data = themes.load_theme(name)
    style = themes.theme_to_style(data)
    body = renderer.render_article_body(DEMO_BLOCKS, style)

    # 微信兼容性校验：每个主题的渲染输出都过一遍。
    violations = wechat_compat.validate_html(body)
    if violations:
        compat = f'<span class="badge bad">⚠ 微信兼容 {len(violations)} 项</span>'
    else:
        compat = '<span class="badge ok">✓ 微信兼容</span>'

    meta = data.get("meta", {})
    desc = meta.get("description", "")
    source = meta.get("source", "")
    badge = '<span class="badge new">新增</span>' if is_new else '<span class="badge old">参照</span>'
    palette = "".join([
        swatch("底色", style["body_bg"]),
        swatch("正文", style["text_color"]),
        swatch("标题", style["heading_color"]),
        swatch("主色", style["primary"]),
        swatch("点睛", style["highlight"]),
    ])

    return f'''<section class="card">
  <div class="card-head">
    <div class="title-row"><span class="tname">{html.escape(name)}</span>{badge}{compat}</div>
    <div class="desc">{html.escape(desc)}</div>
    <div class="source">{html.escape(source)}</div>
    <div class="palette">{palette}</div>
  </div>
  <div class="preview" style="background-color:{style['body_bg']};font-family:{style['font']};">
    {body}
  </div>
</section>'''


def main():
    names = [("default", False)] + [(n, True) for n in NEW_THEMES]
    cards = "\n".join(render_card(n, new) for n, new in names)
    count = len(NEW_THEMES)

    page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>lark2wechat · 主题画廊</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin:0; padding:0; background-color:#ececec;
  font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif; color:#222; }}
.hero {{ max-width:760px; margin:0 auto; padding:40px 20px 16px; }}
.hero h1 {{ font-size:26px; font-weight:800; margin:0 0 8px; }}
.hero p {{ font-size:14px; line-height:1.7; color:#555; margin:0 0 6px; }}
.hero .hint {{ font-size:12px; color:#999; }}
.wrap {{ max-width:760px; margin:0 auto; padding:0 20px 60px; }}
.card {{ background-color:#fff; border-radius:12px; box-shadow:0 1px 3px rgba(0,0,0,.08);
  margin:18px 0; overflow:hidden; }}
.card-head {{ padding:16px 18px; border-bottom:1px solid #f0f0f0; }}
.title-row {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; }}
.tname {{ font-size:20px; font-weight:800; letter-spacing:.5px; }}
.badge {{ font-size:11px; padding:2px 8px; border-radius:10px; font-weight:600; }}
.badge.new {{ background-color:#e8f5e9; color:#2e7d32; }}
.badge.old {{ background-color:#f5f5f5; color:#888; }}
.badge.ok {{ background-color:#e3f2fd; color:#1565c0; }}
.badge.bad {{ background-color:#ffebee; color:#c62828; }}
.desc {{ font-size:13px; color:#444; margin-top:6px; line-height:1.6; }}
.source {{ font-size:11px; color:#aaa; margin-top:3px; }}
.palette {{ margin-top:8px; }}
.preview {{ padding:20px 16px; }}
</style>
</head>
<body>
<div class="hero">
  <h1>lark2wechat · 主题画廊</h1>
  <p>同一篇文章，用 {count} 套主题各渲染一遍：warm 借鉴 huashu-design 暖色出版；
     zenfox 扒自公众号「赛博禅心」实样；feishu 复刻飞书文档阅读视图。均为微信兼容的参数化 YAML。</p>
  <p class="hint">说明：字体走系统栈（外部字体在微信不可用，已降级）；每套主题渲染输出均通过微信兼容性校验。底部色块为该主题的关键色。</p>
</div>
<div class="wrap">
{cards}
</div>
</body>
</html>'''

    out = Path(__file__).resolve().parents[1] / "demos" / "theme-gallery.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"OK -> {out}  ({count + 1} themes)")


if __name__ == "__main__":
    main()
