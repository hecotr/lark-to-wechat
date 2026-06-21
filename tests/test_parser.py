"""parser 单元测试。覆盖现有块 + Phase 1 新增块（quote / image / equation / todo）。"""

from lark2wechat.parser import parse_feishu_markdown as parse


def first(md):
    blocks = parse(md)
    assert len(blocks) >= 1, f"expected >=1 block, got 0"
    return blocks[0]


def only(md):
    blocks = parse(md)
    assert len(blocks) == 1, f"expected exactly 1 block, got {len(blocks)}: {blocks}"
    return blocks[0]


# ---- 现有块（锁定行为）----
def test_heading_h1():
    assert only("# 标题") == {"type": "heading", "level": 1, "text": "标题"}

def test_heading_h3():
    assert only("### 三级") == {"type": "heading", "level": 3, "text": "三级"}

def test_paragraph():
    assert only("正文段落") == {"type": "paragraph", "text": "正文段落"}

def test_unordered_list():
    assert only("- 甲\n- 乙") == {"type": "ulist", "items": ["甲", "乙"]}

def test_ordered_list():
    assert only("1. 甲\n2. 乙") == {"type": "olist", "items": ["甲", "乙"]}

def test_code_block():
    assert only("```python\nprint(1)\n```") == {"type": "code", "lang": "python", "content": "print(1)"}

def test_hr():
    assert only("---") == {"type": "hr"}

def test_whiteboard():
    assert only('<whiteboard token="abc123"/>') == {"type": "whiteboard", "token": "abc123"}

def test_callout():
    b = first('<callout emoji="💡" background-color="light-blue">\n提示内容\n</callout>')
    assert b["type"] == "callout"
    assert b["emoji"] == "💡"
    assert b["content"] == "提示内容"

def test_grid():
    md = '<grid cols="2">\n<column width="50">\n左\n</column>\n<column width="50">\n右\n</column>\n</grid>'
    b = only(md)
    assert b["type"] == "grid"
    assert len(b["columns"]) == 2
    assert b["columns"][0]["items"][0]["text"] == "左"

def test_table_compact():
    md = ('<lark-table header-row="true">\n'
          '<lark-tr><lark-td>A</lark-td><lark-td>B</lark-td></lark-tr>\n'
          '</lark-table>')
    b = only(md)
    assert b["type"] == "table"
    assert b["rows"] == [["A", "B"]]
    assert b["has_header"] is True


def test_std_markdown_table():
    """v2 fetch 输出标准 markdown 表格，必须支持。"""
    md = "| 列1 | 列2 |\n|---|---|\n| a | b |\n| c | d |"
    b = only(md)
    assert b["type"] == "table"
    assert b["rows"] == [["列1", "列2"], ["a", "b"], ["c", "d"]]
    assert b["has_header"] is True


# ---- Phase 1 新增块 ----
def test_quote_markdown():
    assert only("> 引用内容") == {"type": "quote", "content": "引用内容"}

def test_quote_markdown_multiline():
    assert only("> 第一行\n> 第二行") == {"type": "quote", "content": "第一行\n第二行"}

def test_quote_container():
    b = first('<quote-container>\n容器引用\n</quote-container>')
    assert b == {"type": "quote", "content": "容器引用"}

def test_image_markdown():
    assert only("![说明](https://example.com/x.png)") == {
        "type": "image", "alt": "说明", "src": "https://example.com/x.png"}

def test_image_token():
    assert only('<image token="imgToken123"/>') == {"type": "image", "token": "imgToken123"}

def test_equation():
    assert only("<equation>x^2 + y^2 = r^2</equation>") == {
        "type": "equation", "latex": "x^2 + y^2 = r^2"}

def test_todo_unchecked():
    assert only("- [ ] 未完成") == {
        "type": "todo", "items": [{"text": "未完成", "checked": False}]}

def test_todo_checked():
    assert only("- [x] 已完成") == {
        "type": "todo", "items": [{"text": "已完成", "checked": True}]}

def test_todo_mixed():
    b = only("- [ ] a\n- [x] b")
    assert b == {"type": "todo", "items": [
        {"text": "a", "checked": False},
        {"text": "b", "checked": True},
    ]}


# ---- 混合：确保块边界正确 ----
def test_mixed_blocks():
    md = "# 标题\n\n正文\n\n- 列表项"
    blocks = parse(md)
    assert [b["type"] for b in blocks] == ["heading", "paragraph", "ulist"]

def test_todo_not_swallowed_by_ulist():
    """todo 必须优先于 ulist 判断，否则 - [ ] 会被当成 ulist。"""
    md = "- [ ] 任务一\n- 普通列表项"
    blocks = parse(md)
    assert blocks[0]["type"] == "todo"
    assert blocks[1]["type"] == "ulist"
