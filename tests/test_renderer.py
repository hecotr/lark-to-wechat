"""renderer 单元测试。各块类型 → HTML 片段子串断言（不写死完整 HTML，避免脆弱）。"""

from lark2wechat.renderer import render_block


def r(block):
    return render_block(block)


def test_heading_h1():
    html = r({"type": "heading", "level": 1, "text": "标题"})
    assert "标题" in html and "font-size:22px" in html and "font-weight:700" in html

def test_heading_h2():
    html = r({"type": "heading", "level": 2, "text": "二级"})
    assert "二级" in html and "font-size:18px" in html

def test_paragraph():
    assert "正文" in r({"type": "paragraph", "text": "正文"})

def test_paragraph_bold():
    html = r({"type": "paragraph", "text": "**重点**"})
    assert "<strong>重点</strong>" in html

def test_paragraph_link():
    html = r({"type": "paragraph", "text": "[链接](https://x.io)"})
    assert '<a href="https://x.io"' in html and "链接" in html

def test_quote():
    html = r({"type": "quote", "content": "引用文字"})
    assert "引用文字" in html and "border-left" in html

def test_callout():
    html = r({"type": "callout", "emoji": "💡", "bg_color": "light-blue", "content": "提示"})
    assert "💡" in html and "提示" in html and "border-left" in html

def test_image_with_src():
    html = r({"type": "image", "alt": "图", "src": "https://e.com/x.png"})
    assert "<img" in html and "https://e.com/x.png" in html and "alt=\"图\"" in html

def test_image_token_placeholder():
    assert "[图片占位]" in r({"type": "image", "token": "tok"})

def test_whiteboard_placeholder():
    assert "[图片占位]" in r({"type": "whiteboard", "token": "t"})

def test_equation():
    html = r({"type": "equation", "latex": "x^2 + y^2"})
    assert "x^2 + y^2" in html and "<pre" in html

def test_todo_unchecked():
    html = r({"type": "todo", "items": [{"text": "未完成", "checked": False}]})
    assert "☐" in html and "未完成" in html

def test_todo_checked():
    html = r({"type": "todo", "items": [{"text": "已完成", "checked": True}]})
    assert "☑" in html and "已完成" in html

def test_unordered_list():
    html = r({"type": "ulist", "items": ["甲", "乙"]})
    assert "甲" in html and "乙" in html and "•" in html

def test_ordered_list():
    html = r({"type": "olist", "items": ["甲", "乙"]})
    assert "1. 甲" in html and "2. 乙" in html

def test_code_block():
    html = r({"type": "code", "lang": "python", "content": "print(1)"})
    assert "print(1)" in html
    # 多行代码块应用 <br/> 换行（微信不吃 <pre> 的 white-space）
    multi = r({"type": "code", "lang": "python", "content": "a\nb"})
    assert "<br/>" in multi

def test_table():
    html = r({"type": "table", "rows": [["A", "B"]], "widths": [], "has_header": True})
    assert "<table" in html and "<td" in html and "A" in html and "B" in html

def test_hr():
    assert "<table" in r({"type": "hr"})

def test_custom_style_changes_heading_size():
    """主题参数应能改变渲染数值。"""
    from lark2wechat.renderer import DEFAULT_STYLE
    big = dict(DEFAULT_STYLE, h1_size="30px")
    html = r({"type": "heading", "level": 1, "text": "大标题"})
    assert "font-size:22px" in html
    html2 = render_block({"type": "heading", "level": 1, "text": "大标题"}, big)
    assert "font-size:30px" in html2


def test_angle_brackets_in_text_are_escaped():
    """正文裸尖括号必须转义，否则被微信当标签（回归点）。"""
    html = r({"type": "paragraph", "text": "看 <id> 元素"})
    assert "&lt;id&gt;" in html
    assert "<id>" not in html


def test_text_color_marker_still_works_after_escape_fix():
    """转义修复不应破坏 <text color> 颜色标记。"""
    html = r({"type": "paragraph", "text": '<text color="red">重点</text>'})
    assert '<strong style="color:#FF3B30;">重点</strong>' in html
