"""飞书取数：subprocess 调 lark-cli。

- fetch_document(url) → markdown 文本（docs +fetch --api-version v2 --doc-format markdown）
- export_whiteboard(token, output_dir) → PNG 路径（docs +media-download --type whiteboard）
- download_media(token, output_dir) → 文档内图片路径

Windows 注意：lark-cli 是 .cmd，subprocess 需 shell=True 才能解析（绕过 Node execFile 的 spawn 坑）。
"""

import json
import os
import shlex
import shutil
import subprocess


def _cmd_string(argv):
    """跨平台命令字符串（Windows 用 list2cmdline，POSIX 用 shlex.quote）。"""
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return " ".join(shlex.quote(a) for a in argv)


def _decode(b):
    """lark-cli 输出可能是 UTF-8 或 GBK（Windows console），逐一尝试。"""
    if not b:
        return ""
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", errors="replace")


_LARK_CLI = None


def _lark_bin():
    """解析 lark-cli 完整路径（npm 装的是 .CMD，短名在 cmd.exe 下未必可解析）。"""
    global _LARK_CLI
    if _LARK_CLI is None:
        p = shutil.which("lark-cli") or shutil.which("lark-cli.cmd")
        if not p:
            raise RuntimeError("未找到 lark-cli。请先安装并确保在 PATH，再 lark-cli auth login 授权。")
        _LARK_CLI = p
    return _LARK_CLI


def _node_env():
    """注入 node 路径，修复 git-bash 损坏的 PATH（盘符丢失致 cmd.exe 找不到 node）。"""
    env = os.environ.copy()
    node = shutil.which("node") or shutil.which("node.exe")
    if node:
        env["PATH"] = os.path.dirname(node) + os.pathsep + env.get("PATH", "")
    return env


def _run_lark_cli(args):
    """调 lark-cli，返回 stdout。用完整路径 + shell 解析 .CMD，bytes 手动解码兼容编码。"""
    cmd = _cmd_string([_lark_bin()] + args)
    result = subprocess.run(cmd, capture_output=True, shell=True, env=_node_env())
    out = _decode(result.stdout)
    if result.returncode != 0:
        _raise_lark_error(_decode(result.stderr) or out)
    return out


def _raise_lark_error(err):
    """把 lark-cli 错误转成可操作中文报错。"""
    low = err.lower()
    if "enoent" in low or "不是内部或外部命令" in err or "not found" in low and "lark" in low:
        raise RuntimeError("未找到 lark-cli。请先安装并确保在 PATH，再 lark-cli auth login 授权。")
    if "need_user_authorization" in err or "access denied" in low or "not authorized" in low:
        raise RuntimeError("飞书授权不足。请执行 lark-cli auth login 重新授权（需 user 身份 + 画板/媒体读取权限）。")
    raise RuntimeError(f"lark-cli 调用失败：{err[:300]}")


def fetch_document(url: str) -> str:
    """飞书文档 URL → markdown 文本（标准 markdown）。"""
    out = _run_lark_cli(["docs", "+fetch", "--api-version", "v2", "--doc", url, "--doc-format", "markdown"])
    data = json.loads(out)
    if not data.get("ok"):
        err = data.get("error", {})
        raise RuntimeError(f"抓取飞书文档失败：{err.get('message', err)}")
    return data["data"]["document"]["content"]


def export_whiteboard(token: str, output_dir: str = ".") -> str:
    """画板 token → 图片文件路径（JPEG，需 user 身份 + board 读取权限）。

    lark-cli 按 content_type 自动加扩展名；返回实际保存路径（data.saved_path）。
    """
    out = _run_lark_cli(["docs", "+media-download", "--type", "whiteboard",
                         "--token", token,
                         "--output", os.path.join(output_dir, f"whiteboard_{token}")])
    data = json.loads(out)
    if not data.get("ok"):
        err = data.get("error", {})
        raise RuntimeError(f"画板导出失败（token={token}）：{err.get('message', err)}")
    return data["data"]["saved_path"]
