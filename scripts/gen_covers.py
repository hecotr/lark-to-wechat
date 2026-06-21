"""生成 5 种炫酷风格的封面 HTML + 截图（暗色光效系，高大上方向）。

依赖：playwright + 系统 Edge（channel="msedge"）。
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEMOS = ROOT / "demos"
IMG = ROOT / "docs" / "img"
IMG.mkdir(parents=True, exist_ok=True)

TITLE = "好的排版，是退让的艺术"
SUB = "飞书文档 → 微信公众号 · 一键发布"
FONT = "-apple-system,'PingFang SC','Microsoft YaHei',sans-serif"
SERIF = "Georgia,'Songti SC',serif"

# 星点（一个 div + 多 box-shadow 模拟星空）
STARS = ("position:absolute;width:2px;height:2px;background:#fff;border-radius:50%;"
         "box-shadow:60px 40px 0 0 #fff,140px 90px 0 0 #fff,220px 30px 0 0 rgba(255,255,255,.6),"
         "310px 130px 0 0 #fff,400px 60px 0 0 rgba(255,255,255,.5),480px 110px 0 0 #fff,"
         "560px 40px 0 0 rgba(255,255,255,.7),640px 150px 0 0 #fff,720px 70px 0 0 rgba(255,255,255,.5),"
         "90px 180px 0 0 rgba(255,255,255,.6),260px 220px 0 0 #fff,430px 190px 0 0 rgba(255,255,255,.5),"
         "600px 240px 0 0 #fff,780px 200px 0 0 rgba(255,255,255,.7),170px 300px 0 0 #fff,"
         "370px 340px 0 0 rgba(255,255,255,.6),540px 310px 0 0 #fff,700px 380px 0 0 rgba(255,255,255,.5);")

COVERS = [
    ("neon", f'''<div style="width:900px;height:500px;background:#0a0a14;font-family:{FONT};position:relative;overflow:hidden;display:flex;align-items:center;padding:0 80px;">
  <div style="position:absolute;left:-120px;top:-120px;width:440px;height:440px;background:radial-gradient(circle,rgba(124,58,237,.55),transparent 70%);filter:blur(45px);"></div>
  <div style="position:absolute;right:-100px;bottom:-100px;width:420px;height:420px;background:radial-gradient(circle,rgba(34,211,238,.45),transparent 70%);filter:blur(45px);"></div>
  <div style="position:relative;color:#fff;">
    <div style="font-size:64px;font-weight:900;line-height:1.1;letter-spacing:-1px;background:linear-gradient(135deg,#a78bfa,#f0abfc,#67e8f9);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 24px rgba(167,139,250,.45));">{TITLE}</div>
    <div style="font-size:22px;color:#a8a8c8;margin-top:26px;">{SUB}</div>
  </div>
</div>'''),
    ("cosmic", f'''<div style="width:900px;height:500px;background:radial-gradient(ellipse at 28% 42%,#1a1f3a 0%,#050818 100%);font-family:{SERIF};position:relative;overflow:hidden;color:#f0e8d0;">
  <div style="{STARS}"></div>
  <svg style="position:absolute;right:30px;top:50%;transform:translateY(-50%);" width="340" height="340" viewBox="0 0 340 340">
    <ellipse cx="170" cy="170" rx="158" ry="62" fill="none" stroke="rgba(120,160,255,.35)" stroke-dasharray="3 7" transform="rotate(-22 170 170)"/>
    <ellipse cx="170" cy="170" rx="116" ry="46" fill="none" stroke="rgba(120,160,255,.22)" stroke-dasharray="2 6" transform="rotate(-22 170 170)"/>
    <circle cx="170" cy="170" r="30" fill="#f0e8d0" filter="url(#g)"/>
    <circle cx="312" cy="128" r="7" fill="#6fa8dc"/>
    <circle cx="60" cy="210" r="4" fill="#e8c06a"/>
    <defs><filter id="g"><feGaussianBlur stdDeviation="6"/></filter></defs>
  </svg>
  <div style="position:relative;padding:80px;display:flex;flex-direction:column;justify-content:center;height:100%;">
    <div style="font-size:13px;letter-spacing:6px;color:#6fa8dc;font-family:{FONT};margin-bottom:26px;font-weight:600;">LARK2WECHAT · COSMIC</div>
    <div style="font-size:58px;font-weight:700;line-height:1.15;font-style:italic;">好的排版，是<br/>退让的艺术</div>
    <div style="font-size:18px;color:#8a9bc0;margin-top:22px;font-family:{FONT};">{SUB}</div>
  </div>
</div>'''),
    ("metallic", f'''<div style="width:900px;height:500px;background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f0f1e 100%);font-family:{SERIF};display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;">
  <div style="position:absolute;inset:0;background:radial-gradient(circle at 50% 45%,rgba(255,215,0,.1),transparent 60%);"></div>
  <div style="position:relative;text-align:center;">
    <div style="font-size:66px;font-weight:900;letter-spacing:2px;line-height:1.12;background:linear-gradient(180deg,#fff8dc 0%,#ffd700 35%,#b8860b 55%,#ffd700 75%,#fff8dc 100%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 2px 14px rgba(255,215,0,.3));">好的排版<br/>是退让的艺术</div>
    <div style="width:140px;height:2px;background:linear-gradient(90deg,transparent,#ffd700,transparent);margin:32px auto;"></div>
    <div style="font-size:17px;color:#c0a060;letter-spacing:5px;font-family:{FONT};font-weight:600;">FEISHU → WECHAT · ONE CLICK</div>
  </div>
</div>'''),
    ("glass", f'''<div style="width:900px;height:500px;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);font-family:{FONT};display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;">
  <div style="position:absolute;left:8%;top:-25%;width:320px;height:320px;background:radial-gradient(circle,rgba(124,58,237,.5),transparent);filter:blur(55px);"></div>
  <div style="position:absolute;right:5%;bottom:-25%;width:380px;height:380px;background:radial-gradient(circle,rgba(236,72,153,.4),transparent);filter:blur(55px);"></div>
  <div style="position:relative;background:rgba(255,255,255,.07);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);border:1px solid rgba(255,255,255,.18);border-radius:22px;padding:58px 68px;max-width:680px;box-shadow:0 24px 60px rgba(0,0,0,.35);">
    <div style="font-size:52px;font-weight:800;color:#fff;line-height:1.2;letter-spacing:-1px;">好的排版，是<br/>退让的艺术</div>
    <div style="font-size:20px;color:rgba(255,255,255,.72);margin-top:24px;">{SUB}</div>
  </div>
</div>'''),
    ("cyber", f'''<div style="width:900px;height:500px;background:#050510;font-family:{FONT};position:relative;overflow:hidden;display:flex;align-items:center;">
  <div style="position:absolute;bottom:0;left:-10%;right:-10%;height:280px;background-image:linear-gradient(rgba(0,255,200,.18) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,200,.18) 1px,transparent 1px);background-size:44px 44px;transform:perspective(340px) rotateX(62deg);transform-origin:bottom;"></div>
  <div style="position:absolute;left:70px;top:54px;width:44px;height:44px;border:2px solid #00ffc8;box-shadow:0 0 18px rgba(0,255,200,.6);"></div>
  <div style="position:relative;padding:0 80px;color:#fff;">
    <div style="font-size:60px;font-weight:900;line-height:1.1;letter-spacing:-1px;text-shadow:0 0 18px #00ffc8,0 0 36px rgba(255,0,170,.7);">{TITLE}</div>
    <div style="font-size:20px;color:#00ffc8;margin-top:26px;letter-spacing:1px;">&gt; 飞书 → 微信 · ONE CLICK PUBLISH</div>
  </div>
</div>'''),
]

LABELS = {
    "neon": "暗夜霓虹（紫青渐变发光）",
    "cosmic": "深空宇宙（星轨·复古衬线）",
    "metallic": "金属质感（金色液态金属字）",
    "glass": "玻璃拟态（磨砂暗光卡）",
    "cyber": "赛博网格（透视网格·霓虹）",
}


def page(inner):
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<style>*{{margin:0;padding:0;box-sizing:border-box;}}</style></head>'
            f'<body>{inner}</body></html>')


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        for key, inner in COVERS:
            (DEMOS / f"cover-{key}.html").write_text(page(inner), encoding="utf-8")
            pg = browser.new_page(viewport={"width": 900, "height": 500}, device_scale_factor=2)
            pg.goto((DEMOS / f"cover-{key}.html").as_uri())
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(IMG / f"cover-{key}.png"))
            print(f"  done cover-{key}.png")
            pg.close()
        browser.close()

    rows = "\n".join(
        f'<figure style="margin:0 0 28px;"><img src="../docs/img/cover-{k}.png" '
        f'style="width:100%;border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.3);"/>'
        f'<figcaption style="font:15px sans-serif;color:#333;margin-top:10px;">{i+1}. {LABELS[k]}</figcaption></figure>'
        for i, (k, _) in enumerate(COVERS))
    (DEMOS / "covers.html").write_text(
        f'<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<style>body{{max-width:720px;margin:40px auto;font-family:sans-serif;background:#fafafa;}}</style>'
        f'</head><body><h2>封面方案 · 炫酷版（5 种）</h2>{rows}</body></html>', encoding="utf-8")
    print("  done covers.html")


if __name__ == "__main__":
    main()
