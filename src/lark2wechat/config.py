"""配置与凭证加载。"""

import os
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    default_theme: str = "zenfox"

    def require_wechat(self):
        """发布前校验微信凭证齐全。"""
        missing = [k for k, v in (
            ("WECHAT_APP_ID", self.wechat_app_id),
            ("WECHAT_APP_SECRET", self.wechat_app_secret),
        ) if not v]
        if missing:
            raise RuntimeError(
                "缺少微信凭证：" + "、".join(missing) +
                "。请在 .env 中配置（参考 .env.example）。"
            )


def _find_env(explicit=None):
    """查找 .env：显式路径 → 当前目录向上逐级搜索。"""
    if explicit:
        return explicit
    cwd = Path.cwd()
    for d in [cwd] + list(cwd.parents):
        p = d / ".env"
        if p.exists():
            return str(p)
    return None


def load_config(env_file=None) -> Config:
    """从 .env 加载配置（自动向上搜索，便于子目录项目复用上级凭证）。"""
    found = _find_env(env_file)
    if found:
        load_dotenv(found)
    return Config(
        wechat_app_id=os.getenv("WECHAT_APP_ID", ""),
        wechat_app_secret=os.getenv("WECHAT_APP_SECRET", ""),
        default_theme=os.getenv("LARK2WECHAT_DEFAULT_THEME", "zenfox"),
    )
