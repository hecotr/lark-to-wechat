"""lark2wechat CLI 入口。

Phase 0：命令骨架。
Phase 1：render / themes 接 parser + renderer + 主题。
Phase 3/5/6：fetch / publish 接真实实现。
"""

import click


def _extract_title(blocks):
    """从 IR 取标题：优先 H1，其次任意 heading。"""
    for b in blocks:
        if b.get("type") == "heading" and b.get("level") == 1:
            return b.get("text", "")
    for b in blocks:
        if b.get("type") == "heading":
            return b.get("text", "")
    return ""


@click.group()
def main():
    """lark2wechat — 飞书文档 → 微信公众号草稿箱一键发布。"""


@main.command()
@click.argument("url")
@click.option("--theme", default="zenfox", help="排版主题（见 themes list）")
@click.option("-i", "--interactive", is_flag=True, help="交互式选择主题")
@click.option("--cover", type=click.Path(exists=True), help="封面图本地路径")
@click.option("--auto-cover", is_flag=True, help="无封面时自动生成")
@click.option("--digest", help="文章摘要（默认取正文前 54 字）")
@click.option("--dry-run", is_flag=True, help="只渲染不发布")
@click.option("--update", "update_id", help="更新已有草稿 media_id（覆盖而非新增，见 drafts list）")
def publish(url, theme, cover, auto_cover, digest, dry_run, update_id, interactive):
    """端到端：飞书文档 → 微信公众号草稿箱。"""
    import sys
    from .config import load_config
    from . import publish_flow
    if interactive and sys.stdin.isatty():
        from .themes import list_themes
        names = list_themes()
        if names:
            default = str(names.index(theme) + 1) if theme in names else "1"
            for i, n in enumerate(names, 1):
                click.echo(f"  {i}. {n}")
            idx = click.prompt("选择主题序号", default=default, show_default=True)
            try:
                theme = names[int(idx) - 1]
            except (ValueError, IndexError):
                pass
    try:
        result = publish_flow.publish(
            url=url, theme=theme, cover=cover, auto_cover=auto_cover,
            digest=digest, dry_run=dry_run, cfg=load_config(), update_id=update_id)
    except Exception as e:
        raise click.ClickException(str(e))
    if result.get("violations"):
        click.echo("⚠️ 微信兼容性警告：", err=True)
        for v in result["violations"][:5]:
            click.echo(f"  {v}", err=True)
    if result.get("dry_run"):
        click.echo(result["html"])
        return
    if result.get("updated"):
        click.echo(f"✅ 已更新草稿 {result['media_id']}")
    else:
        click.echo(f"✅ 发布成功，草稿 media_id: {result['media_id']}")
    click.echo("到 mp.weixin.qq.com → 草稿箱 审核。")


@main.command()
@click.argument("md_file", type=click.Path(exists=True))
@click.option("--theme", default="zenfox", help="排版主题")
@click.option("-o", "--output", type=click.Path(), help="输出 HTML 路径（默认 stdout）")
def render(md_file, theme, output):
    """只渲染：markdown 文件 → 微信预览 HTML。"""
    from pathlib import Path
    from .parser import parse_feishu_markdown
    from .renderer import render_preview_page, render_article_body
    from .themes import get_style
    from .wechat_compat import validate_html

    md = Path(md_file).read_text(encoding="utf-8")
    blocks = parse_feishu_markdown(md)
    title = _extract_title(blocks) or Path(md_file).stem
    style = get_style(theme)

    violations = validate_html(render_article_body(blocks, style))
    if violations:
        click.echo("⚠️ 微信兼容性警告：", err=True)
        for v in violations[:5]:
            click.echo(f"  {v}", err=True)

    html = render_preview_page(blocks, title, style)
    if output:
        Path(output).write_text(html, encoding="utf-8")
        click.echo(f"已生成：{output}")
    else:
        click.echo(html)


@main.command()
@click.argument("url")
@click.option("-o", "--output", type=click.Path(), help="输出 markdown 路径（默认 stdout）")
def fetch(url, output):
    """只取数：飞书文档 → markdown（调试用）。"""
    from pathlib import Path
    from .fetcher import fetch_document
    md = fetch_document(url)
    if output:
        Path(output).write_text(md, encoding="utf-8")
        click.echo(f"已生成：{output}")
    else:
        click.echo(md)


@main.group(name="themes")
def themes():
    """排版主题管理。"""


@themes.command(name="list")
def themes_list():
    """列出可用主题。"""
    from .themes import list_themes, load_theme
    for name in list_themes():
        try:
            desc = load_theme(name).get("meta", {}).get("description", "")
        except Exception:
            desc = ""
        click.echo(f"  {name:<12} {desc}")


@main.group(name="drafts")
def drafts():
    """草稿箱管理（列出 / 删除）。"""


@drafts.command(name="list")
def drafts_list():
    """列出公众号草稿箱。"""
    from .config import load_config
    from .publisher import get_access_token, list_drafts
    cfg = load_config()
    cfg.require_wechat()
    token = get_access_token(cfg.wechat_app_id, cfg.wechat_app_secret)
    data = list_drafts(token)
    click.echo(f"共 {data.get('total_count', 0)} 篇，本页 {data.get('item_count', 0)} 篇：")
    for it in data.get("item", []):
        mid = it.get("media_id", "")
        news = it.get("content", {}).get("news_item", [{}])
        title = news[0].get("title", "(无标题)") if news else "(无标题)"
        click.echo(f"  {mid[:24]:<26} {title[:40]}")


@drafts.command(name="delete")
@click.argument("media_id")
def drafts_delete(media_id):
    """删除指定草稿（按 media_id，见 drafts list）。"""
    from .config import load_config
    from .publisher import get_access_token, delete_draft
    cfg = load_config()
    cfg.require_wechat()
    token = get_access_token(cfg.wechat_app_id, cfg.wechat_app_secret)
    delete_draft(token, media_id)
    click.echo(f"已删除草稿 {media_id}")


@drafts.command(name="history")
def drafts_history():
    """本地发布历史（最近 20 条，含主题/media_id/时间）。"""
    from .history import list_history
    rows = list_history()
    if not rows:
        click.echo("（暂无发布历史）")
        return
    click.echo(f"最近 {len(rows)} 条发布：")
    for r in reversed(rows):
        flag = "更新" if r.get("updated") else "新增"
        click.echo(f"  {r.get('time', '')[:16]}  [{r.get('theme', ''):>7}] {flag}  "
                   f"{r.get('title', '')[:28]}  {r.get('media_id', '')[:20]}")


if __name__ == "__main__":
    main()
