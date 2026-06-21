# lark2wechat

> 飞书文档 → 微信公众号草稿箱，一键发布。

在飞书写完文章，一条命令发布到微信公众号草稿箱，审核后即可群发。保留飞书源格式、图片不丢失、可选排版主题。

## 特性

- 📝 直接支持飞书源格式（callout / 分栏 / 表格 / 画板 / 引用块 / 图片 / 公式 / 任务列表）
- 🎨 多套排版主题（固定微信兼容骨架 + 参数化），可自定义
- 🖼️ 画板与正文图片自动处理、上传，不丢失
- 📤 直接进草稿箱，审核后发布
- 🤖 提供 Claude Code Skill 薄壳，让 AI 一句话帮你发布

## 安装

```bash
pip install -e .
# 公式支持（可选）
pip install -e ".[math]"
```

## 配置

1. 复制 `.env.example` 为 `.env`，填入微信公众号 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`。
2. 出口 IP 加入 mp.weixin.qq.com → 设置与开发 → 基本配置 → IP 白名单。
3. 飞书侧执行 `lark-cli auth login`（需含画板读取、文档媒体下载权限）。

## 使用

```bash
lark2wechat publish <飞书文档链接> --theme default        # 端到端 → 草稿箱
lark2wechat render  <md文件>      --theme default          # 只渲染预览 HTML
lark2wechat fetch   <飞书文档链接>                          # 只取数（调试）
lark2wechat themes list                                     # 列出主题
```

## 主题

主题位于 `src/lark2wechat/themes/`，每套两个文件：`<name>.yaml`（参数）+ `<name>.md`（气质描述），`themes list` 查看。内置：

| 主题 | 风格 | 来源 |
|---|---|---|
| `default` | 零装饰，字号字重分层级（微信蓝链接） | — |
| `clean` | 极简白，大留白 | — |
| `brand` | 暖橙品牌 | — |
| `warm` | 暖色出版，衬线标题×无衬线正文，奶油底 | huashu-design |
| `zenfox` | 暖灰墨正文+砖红衬线标题+橘红强调+红色色条 | 扒自公众号实样 |
| `feishu` | 飞书文档阅读视图（飞书蓝+浅灰块+高亮块） | 飞书设计规范 |

主题支持参数：正文字体/颜色/底色/行高、标题独立字体、强调色、引用与高亮块的背景+色条。生成主题画廊 demo：`python scripts/theme_gallery.py` → `demos/theme-gallery.html`。

## 状态

🚧 开发中（Phase 0-2：骨架 / 核心纯函数 / 微信兼容性校验器）。详见 `docs/superpowers/plans/`。

## License

MIT
