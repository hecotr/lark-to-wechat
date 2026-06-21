"""把主题预览 HTML 截图成 PNG（供 README 展示）。

依赖：pip install playwright && python -m playwright install chromium
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEMOS = ROOT / "demos"
OUT = ROOT / "docs" / "img"
OUT.mkdir(parents=True, exist_ok=True)

THEMES = ["warm", "zenfox", "feishu"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        # 各主题竖图：截 #article-content（去掉顶栏，纯文章+底色）
        for t in THEMES:
            page = browser.new_page(viewport={"width": 620, "height": 1000}, device_scale_factor=2)
            page.goto((DEMOS / f"render-{t}.html").as_uri())
            page.wait_for_load_state("networkidle", timeout=10000)
            try:
                page.locator("#article-content").screenshot(path=str(OUT / f"theme-{t}.png"))
            except Exception:
                page.screenshot(path=str(OUT / f"theme-{t}.png"), full_page=True)
            print(f"  done theme-{t}.png")
            page.close()
        # 画廊总览（full_page，含 default 参照 + 三主题并排 + 色板）
        page = browser.new_page(viewport={"width": 820, "height": 1200}, device_scale_factor=2)
        page.goto((DEMOS / "theme-gallery.html").as_uri())
        page.wait_for_load_state("networkidle", timeout=10000)
        page.screenshot(path=str(OUT / "themes-gallery.png"), full_page=True)
        print("  done themes-gallery.png")
        browser.close()


if __name__ == "__main__":
    main()
