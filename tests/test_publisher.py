"""publisher 单元测试（mock httpx，不真实调用微信）。"""

import pytest

from lark2wechat import publisher


class _FakeResp:
    def __init__(self, data):
        self._d = data

    def json(self):
        return self._d


def test_get_access_token(monkeypatch):
    monkeypatch.setattr(publisher.httpx, "get",
                        lambda *a, **k: _FakeResp({"access_token": "TOK123"}))
    assert publisher.get_access_token("id", "secret") == "TOK123"


def test_ip_whitelist_error(monkeypatch):
    monkeypatch.setattr(publisher.httpx, "get",
                        lambda *a, **k: _FakeResp({"errcode": 40164, "errmsg": "invalid ip 1.2.3.4"}))
    with pytest.raises(RuntimeError) as e:
        publisher.get_access_token("id", "secret")
    assert "白名单" in str(e.value) and "1.2.3.4" in str(e.value)


def test_invalid_credential_error(monkeypatch):
    monkeypatch.setattr(publisher.httpx, "get",
                        lambda *a, **k: _FakeResp({"errcode": 40125, "errmsg": "invalid appsecret"}))
    with pytest.raises(RuntimeError) as e:
        publisher.get_access_token("id", "secret")
    assert "凭证" in str(e.value)


def test_upload_image(monkeypatch, tmp_path):
    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0")
    monkeypatch.setattr(publisher.httpx, "post",
                        lambda *a, **k: _FakeResp({"url": "http://mmbiz.qpic.cn/x"}))
    assert publisher.upload_image("TOK", str(img)) == "http://mmbiz.qpic.cn/x"


def test_add_material(monkeypatch, tmp_path):
    img = tmp_path / "c.jpg"
    img.write_bytes(b"\xff\xd8")
    monkeypatch.setattr(publisher.httpx, "post",
                        lambda *a, **k: _FakeResp({"media_id": "MAT1", "url": "u"}))
    assert publisher.add_material("TOK", str(img)) == "MAT1"


def test_add_draft(monkeypatch):
    captured = {}

    def fake_post(url, params=None, json=None, timeout=None):
        captured["json"] = json
        return _FakeResp({"media_id": "DRAFT1"})

    monkeypatch.setattr(publisher.httpx, "post", fake_post)
    mid = publisher.add_draft("TOK", "标题", "<p>c</p>", "thumb1", "摘要")
    assert mid == "DRAFT1"
    assert captured["json"]["articles"][0]["title"] == "标题"
    assert captured["json"]["articles"][0]["thumb_media_id"] == "thumb1"


def test_add_draft_error(monkeypatch):
    monkeypatch.setattr(publisher.httpx, "post",
                        lambda *a, **k: _FakeResp({"errcode": 40007, "errmsg": "no media"}))
    with pytest.raises(RuntimeError) as e:
        publisher.add_draft("TOK", "t", "c", "thumb")
    assert "errcode=40007" in str(e.value)
