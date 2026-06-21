"""微信公众号发布。

- get_access_token(app_id, app_secret)
- upload_image(token, path) → 正文图片微信域名 URL
- add_material(token, path) → 封面 thumb_media_id
- add_draft(token, title, content, thumb_media_id, digest) → 草稿 media_id（新增不覆盖）
"""

import httpx

BASE = "https://api.weixin.qq.com/cgi-bin"


def _check(data, ctx):
    """检查微信 API 返回，错误转可操作中文报错。"""
    errcode = data.get("errcode", 0)
    if not errcode:
        return
    if errcode == 40164:
        raise RuntimeError(
            f"{ctx}失败：IP 不在白名单。{data.get('errmsg')}。"
            f"请到 mp.weixin.qq.com → 设置与开发 → 基本配置 → IP 白名单，加入你的出口 IP。")
    if errcode in (40001, 40125):
        raise RuntimeError(f"{ctx}失败：凭证无效（{data.get('errmsg')}）。检查 WECHAT_APP_ID / WECHAT_APP_SECRET。")
    raise RuntimeError(f"{ctx}失败（errcode={errcode}）：{data.get('errmsg', data)}")


def get_access_token(app_id: str, app_secret: str) -> str:
    r = httpx.get(f"{BASE}/token", params={
        "grant_type": "client_credential", "appid": app_id, "secret": app_secret}, timeout=15)
    data = r.json()
    if "access_token" not in data:
        _check(data, "获取 access_token")
        raise RuntimeError(f"获取 access_token 失败：{data}")
    return data["access_token"]


def upload_image(token: str, image_path: str) -> str:
    """正文图片 → uploadimg → 微信域名 URL。"""
    with open(image_path, "rb") as f:
        r = httpx.post(f"{BASE}/media/uploadimg", params={"access_token": token},
                       files={"media": f}, timeout=60)
    data = r.json()
    _check(data, "上传正文图片")
    return data["url"]


def add_material(token: str, image_path: str) -> str:
    """封面 → add_material → thumb_media_id。"""
    with open(image_path, "rb") as f:
        r = httpx.post(f"{BASE}/material/add_material",
                       params={"access_token": token, "type": "image"},
                       files={"media": f}, timeout=60)
    data = r.json()
    _check(data, "上传封面")
    return data["media_id"]


def add_draft(token: str, title: str, content: str, thumb_media_id: str, digest: str = "") -> str:
    """新增草稿（不覆盖）。返回 media_id。"""
    r = httpx.post(f"{BASE}/draft/add", params={"access_token": token}, json={
        "articles": [{
            "title": title,
            "author": "",
            "digest": digest,
            "content": content,
            "content_source": "",
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]
    }, timeout=30)
    data = r.json()
    _check(data, "新增草稿")
    return data["media_id"]


def list_drafts(token: str, offset: int = 0, count: int = 20) -> dict:
    """获取草稿列表（no_content=1 不返回正文，省流量）。返回 {total_count, item_count, item:[...]}。"""
    r = httpx.post(f"{BASE}/draft/batchget", params={"access_token": token},
                   json={"offset": offset, "count": count, "no_content": 1}, timeout=30)
    data = r.json()
    _check(data, "获取草稿列表")
    return data


def delete_draft(token: str, media_id: str) -> bool:
    """删除草稿（按 media_id）。"""
    r = httpx.post(f"{BASE}/draft/delete", params={"access_token": token},
                   json={"media_id": media_id}, timeout=30)
    data = r.json()
    _check(data, "删除草稿")
    return True
