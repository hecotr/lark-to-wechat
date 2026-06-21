---
name: lark2wechat
description: 飞书文档一键发布到微信公众号草稿箱。当用户给出飞书文档链接、说"发布到公众号/草稿箱"、或想用 lark2wechat 排版发布时使用。本 skill 是薄壳，所有逻辑由 lark2wechat CLI 完成。
---

# lark2wechat（Skill 薄壳）

飞书文档 → 微信公众号草稿箱一键发布。**本 skill 不实现任何逻辑**，只指导调用 `lark2wechat` CLI 并处理常见报错。

## 前置条件（publish 前）

1. `lark2wechat` 已安装（`pip install -e .` 或 `pip install lark2wechat`），`lark2wechat --help` 可用
2. `.env` 配置 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`（config 会自动向上搜索 .env）
3. 出口 IP 已加入 mp.weixin.qq.com → 设置与开发 → 基本配置 → IP 白名单
4. `lark-cli auth status` 已授权（user 身份，含画板读取 + 文档媒体下载权限）

## 命令

```bash
lark2wechat publish <飞书链接> --theme default [--cover x.jpg|--auto-cover] [--digest "..."]
lark2wechat publish <飞书链接> --theme default --dry-run       # 只渲染预览，不发布
lark2wechat render  <md文件>   --theme default                  # markdown → 预览 HTML
lark2wechat fetch   <飞书链接>                                   # 飞书 → markdown（调试）
lark2wechat themes list                                         # 列出主题
```

主题：`default`（零装饰内容驱动）/ `clean`（极简白）/ `brand`（暖橙品牌）。

## 流程

1. 预览：`publish --dry-run` 或 `render` 看排版
2. 发布：`publish --theme <名> --auto-cover` → 草稿箱
3. 审核：到 mp.weixin.qq.com → 草稿箱，审核后群发（注意：每次 publish 是新增草稿，不覆盖，旧草稿手动删）

## 报错处理

| 错误 | 原因 | 解决 |
|---|---|---|
| `40164 ... not in whitelist` | 出口 IP 不在白名单 | 错误里带 IP，加入 mp.weixin.qq.com IP 白名单 |
| `未找到 lark-cli` | lark-cli 未装/未授权 | 装 lark-cli + `lark-cli auth login` |
| `unsafe output path` | lark-cli --output 要相对路径 | 在目标目录 cwd 下跑（CLI 已处理） |
| 画板显示占位 | 画板导出失败 | 检查 lark-cli user 授权 + board 读取权限 |
| `缺少封面` | 无封面 | 加 `--cover <path>` 或 `--auto-cover` |
| 列表/符号显示字面实体 | （已修复）renderer 用 Unicode 字符 | 用最新版 |
