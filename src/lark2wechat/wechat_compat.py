"""微信兼容性校验器。

微信公众号正文会被严格过滤：剥 class/id、外部 CSS、<script>、事件属性等。
本模块扫描渲染输出的正文 HTML，确保只用白名单标签 + 安全属性，
防止"渲染出来好看但贴进公众号被拍扁"的回归。
"""

from html.parser import HTMLParser

# 微信正文允许的标签白名单（renderer 实际使用的 + 常见安全标签）。
ALLOWED_TAGS = {
    "section", "p", "h1", "h2", "h3", "h4", "strong", "em", "b", "i",
    "code", "pre", "table", "tr", "td", "th", "thead", "tbody",
    "img", "a", "blockquote", "ul", "ol", "li", "br", "span", "font", "hr",
}

# 微信会剥掉的属性（出现即不兼容）。
FORBIDDEN_ATTRS = {"class", "id"}


class _Checker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.violations = []

    def _check(self, tag, attrs):
        if tag not in ALLOWED_TAGS:
            self.violations.append(f"非白名单标签：<{tag}>")
        for name, _val in attrs:
            if name in FORBIDDEN_ATTRS:
                self.violations.append(f"禁止属性 {name}（在 <{tag}>）")
            if name.startswith("on"):
                self.violations.append(f"事件属性 {name}（在 <{tag}>）")

    def handle_starttag(self, tag, attrs):
        self._check(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self._check(tag, attrs)


def validate_html(html_str):
    """返回违规列表；空列表表示通过微信兼容性校验。"""
    checker = _Checker()
    checker.feed(html_str)
    return checker.violations


def assert_wechat_compatible(html_str):
    """断言 HTML 微信兼容；不兼容抛 ValueError（带违规详情）。"""
    violations = validate_html(html_str)
    if violations:
        raise ValueError("微信兼容性校验失败：\n  " + "\n  ".join(violations[:20]))
    return True
