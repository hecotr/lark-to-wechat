"""封面生成：cosmic 深空宇宙模板（HTML → playwright 截图 → PNG）。

playwright / 系统 Edge 不可用时，调用方应降级到 Pillow 纯色封面（见 publish_flow._gen_cover_plain）。
"""
import html
from pathlib import Path

FONT = "-apple-system,'PingFang SC','Microsoft YaHei',sans-serif"
SERIF = "Georgia,'Songti SC','STSong',serif"
SUB = "飞书文档 → 微信公众号 · 一键发布"

# 星点（一个 div + 多 box-shadow 模拟星空）
STARS = ("position:absolute;width:2px;height:2px;background:#fff;border-radius:50%;"
         "box-shadow:60px 40px 0 0 #fff,140px 90px 0 0 #fff,220px 30px 0 0 rgba(255,255,255,.6),"
         "310px 130px 0 0 #fff,400px 60px 0 0 rgba(255,255,255,.5),480px 110px 0 0 #fff,"
         "560px 40px 0 0 rgba(255,255,255,.7),640px 150px 0 0 #fff,720px 70px 0 0 rgba(255,255,255,.5),"
         "90px 180px 0 0 rgba(255,255,255,.6),260px 220px 0 0 #fff,430px 190px 0 0 rgba(255,255,255,.5),"
         "600px 240px 0 0 #fff,780px 200px 0 0 rgba(255,255,255,.7),170px 300px 0 0 #fff,"
         "370px 340px 0 0 rgba(255,255,255,.6),540px 310px 0 0 #fff,700px 380px 0 0 rgba(255,255,255,.5);")

# 行星轨道 SVG（右侧）
ORBIT_SVG = '''<svg style="position:absolute;right:30px;top:50%;transform:translateY(-50%);" width="340" height="340" viewBox="0 0 340 340">
  <ellipse cx="170" cy="170" rx="158" ry="62" fill="none" stroke="rgba(120,160,255,.35)" stroke-dasharray="3 7" transform="rotate(-22 170 170)"/>
  <ellipse cx="170" cy="170" rx="116" ry="46" fill="none" stroke="rgba(120,160,255,.22)" stroke-dasharray="2 6" transform="rotate(-22 170 170)"/>
  <circle cx="170" cy="170" r="30" fill="#f0e8d0" filter="url(#cg)"/>
  <circle cx="312" cy="128" r="7" fill="#6fa8dc"/>
  <circle cx="60" cy="210" r="4" fill="#e8c06a"/>
  <defs><filter id="cg"><feGaussianBlur stdDeviation="6"/></filter></defs>
</svg>'''


def _cosmic_html(title: str) -> str:
    """生成 cosmic 封面完整 HTML（标题参数化，自动换行）。"""
    title_e = html.escape(title)
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<style>*{{margin:0;padding:0;box-sizing:border-box;}}</style></head>
<body><div style="width:900px;height:500px;background:radial-gradient(ellipse at 28% 42%,#1a1f3a 0%,#050818 100%);font-family:{SERIF};position:relative;overflow:hidden;color:#f0e8d0;">
  <div style="{STARS}"></div>
  {ORBIT_SVG}
  <div style="position:relative;padding:70px 80px;display:flex;flex-direction:column;justify-content:center;height:100%;max-width:560px;">
    <div style="font-size:13px;letter-spacing:6px;color:#6fa8dc;font-family:{FONT};margin-bottom:24px;font-weight:600;">LARK2WECHAT · COSMIC</div>
    <div style="font-size:46px;font-weight:700;line-height:1.18;font-style:italic;word-break:break-word;">{title_e}</div>
    <div style="font-size:17px;color:#8a9bc0;margin-top:22px;font-family:{FONT};">{SUB}</div>
  </div>
</div></body></html>'''


def render_cover(title: str, out_path: str) -> str:
    """渲染 cosmic 封面 → PNG（900×500，device_scale=2 高清）。"""
    from playwright.sync_api import sync_playwright
    out = Path(out_path).resolve()
    tmp = out.with_suffix(".cover.html")
    tmp.write_text(_cosmic_html(title), encoding="utf-8")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge")
            page = browser.new_page(viewport={"width": 900, "height": 500}, device_scale_factor=2)
            page.goto(tmp.as_uri())
            page.wait_for_timeout(300)
            page.screenshot(path=str(out))
            browser.close()
    finally:
        tmp.unlink(missing_ok=True)
    return str(out)
