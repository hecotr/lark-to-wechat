"""主题加载/校验/转换测试。"""

import pytest

from lark2wechat.themes import list_themes, load_theme, get_style, validate_theme, theme_to_style


def test_list_themes_includes_builtins():
    names = list_themes()
    assert "warm" in names
    assert "zenfox" in names
    assert "feishu" in names
    assert len(names) == 3


def test_load_zenfox():
    data = load_theme("zenfox")
    assert data["name"] == "zenfox"
    assert data["base"]["text_size"] == "15px"


def test_get_style_flat_keys():
    style = get_style("zenfox")
    for k in ("font", "heading_font", "text_color", "text_size", "line_height",
              "primary", "heading_color", "h1_size", "h1_weight",
              "table_border", "code_bg", "callout_border", "quote_color"):
        assert k in style, f"missing key {k}"


def test_load_missing_raises():
    with pytest.raises(FileNotFoundError):
        load_theme("__not_exist__")


def test_validate_rejects_missing_base():
    with pytest.raises(ValueError):
        validate_theme("bad", {"name": "bad", "base": {}, "heading": {"color": "#000", "h1": {"size": "1px", "weight": 700}, "h2": {"size": "1px", "weight": 700}, "h3": {"size": "1px", "weight": 600}}, "accent": {"primary": "#000"}})


def test_validate_rejects_missing_heading_node():
    bad = {"name": "x", "base": {"font_family": "f", "text_color": "#000", "text_size": "15px", "line_height": "2em"},
           "heading": {"color": "#000", "h1": {"size": "1px", "weight": 700}},
           "accent": {"primary": "#000"}}
    with pytest.raises(ValueError):
        validate_theme("x", bad)


def test_all_builtin_themes_valid_and_renderable():
    from lark2wechat.renderer import render_block
    for name in list_themes():
        style = get_style(name)
        assert style["font"]
        assert style["h1_size"]
        html = render_block({"type": "heading", "level": 1, "text": "标题"}, style)
        assert "标题" in html


def test_themes_have_distinct_colors():
    """不同主题应产出不同强调色。"""
    zenfox = get_style("zenfox")
    warm = get_style("warm")
    assert zenfox["primary"] != warm["primary"]


def test_theme_to_style_weight_string():
    style = theme_to_style(load_theme("zenfox"))
    assert isinstance(style["h1_weight"], str)
