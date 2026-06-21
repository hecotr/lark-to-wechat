"""本地发布历史：记录每次 publish（标题/主题/media_id/时间/新增or更新）。

存 ~/.lark2wechat/history.jsonl（用户级，跨项目）。失败静默，不影响发布。
"""
import json
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path.home() / ".lark2wechat" / "history.jsonl"


def record_publish(title, theme, media_id, updated=False):
    """追加一条发布记录。"""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {"title": title, "theme": theme, "media_id": media_id,
             "updated": updated,
             "time": datetime.now().isoformat(timespec="seconds")}
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def list_history(limit=20):
    """读取最近 limit 条记录（按时间正序；调用方可 reverse 最新在前）。"""
    if not HISTORY_FILE.exists():
        return []
    out = []
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out
