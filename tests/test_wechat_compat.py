"""微信兼容性校验器测试。"""

import pytest

from lark2wechat.wechat_compat import validate_html, assert_wechat_compatible


def test_clean_html_passes():
    assert validate_html('<section style="color:red;"><p>hi</p></section>') == []

def test_allowed_tags_pass():
    html = '<p>a</p><strong>b</strong><code>c</code><img src="x" style="w:1px"/><br/>'
    assert validate_html(html) == []

def test_class_detected():
    v = validate_html('<p class="x">hi</p>')
    assert any("class" in x for x in v)

def test_id_detected():
    assert any("id" in x for x in validate_html('<p id="x">hi</p>'))

def test_non_whitelisted_tag_detected():
    v = validate_html('<div>hi</div>')
    assert any("div" in x for x in v)

def test_script_tag_detected():
    v = validate_html('<script>alert(1)</script>')
    assert any("script" in x for x in v)

def test_event_attr_detected():
    v = validate_html('<img src="x" onclick="bad()">')
    assert any("onclick" in x for x in v)

def test_assert_raises_on_violation():
    with pytest.raises(ValueError):
        assert_wechat_compatible('<div class="x">bad</div>')

def test_assert_passes_clean():
    assert assert_wechat_compatible('<p style="x">ok</p>') is True


def test_all_block_types_render_wechat_compatible():
    """防回归：renderer 对所有块类型的输出都必须通过校验。"""
    from lark2wechat.renderer import render_block
    from lark2wechat.themes import get_style

    style = get_style("zenfox")
    blocks = [
        {"type": "heading", "level": 1, "text": "标题一"},
        {"type": "heading", "level": 2, "text": "标题二"},
        {"type": "heading", "level": 3, "text": "标题三"},
        {"type": "paragraph", "text": "正文 **加粗** [链接](http://x.io)"},
        {"type": "quote", "content": "引用"},
        {"type": "callout", "emoji": "💡", "bg_color": "light-blue", "content": "提示"},
        {"type": "code", "lang": "python", "content": "print(1)"},
        {"type": "equation", "latex": "x^2 + y^2"},
        {"type": "image", "src": "http://x/y.png", "alt": "图"},
        {"type": "whiteboard", "token": "t"},
        {"type": "todo", "items": [{"text": "任务", "checked": False}]},
        {"type": "ulist", "items": ["甲", "乙"]},
        {"type": "olist", "items": ["甲", "乙"]},
        {"type": "hr"},
        {"type": "table", "rows": [["A", "B"]], "widths": [], "has_header": True},
        {"type": "grid", "columns": [
            {"width": 50, "items": [{"type": "paragraph", "text": "左"}]},
            {"width": 50, "items": [{"type": "paragraph", "text": "右"}]},
        ]},
    ]
    for b in blocks:
        html = render_block(b, style)
        violations = validate_html(html)
        assert violations == [], f"块 {b['type']} 不兼容：{violations}"


def test_all_themes_render_wechat_compatible():
    """防回归：所有主题渲染真实文档都通过校验。"""
    from pathlib import Path
    from lark2wechat.parser import parse_feishu_markdown
    from lark2wechat.renderer import render_article_body
    from lark2wechat.themes import list_themes, get_style

    fixture = Path(__file__).resolve().parent.parent.parent / "feishu_content.md"
    if not fixture.exists():
        pytest.skip("无 feishu_content.md fixture")
    blocks = parse_feishu_markdown(fixture.read_text(encoding="utf-8"))
    for name in list_themes():
        html = render_article_body(blocks, get_style(name))
        violations = validate_html(html)
        assert violations == [], f"主题 {name} 不兼容：{violations[:3]}"
