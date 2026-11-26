"""
The dashboard (web/enhanced.html) and the server agree on what can be opened.

The page is read from disk on each load while the server keeps running the
code it started with, so after a `git pull` the page could be newer than the
server: cards said "open ›" and nothing opened. Now /health says which
dashboard API the server speaks and whether its code changed since it
started, and the page shows how to restart when they don't match.

    python3 -m pytest tests/test_dashboard_contract.py -q
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
PAGE = open(os.path.join(ROOT, "web", "enhanced.html"), encoding="utf-8").read()


def test_the_page_and_server_speak_the_same_dashboard_api():
    from api import server
    page = re.search(r"const DASHBOARD_API = (\d+);", PAGE)
    assert page and int(page.group(1)) == server.DASHBOARD_API


def test_every_kind_the_page_opens_is_one_the_server_describes():
    from engine.details import DESCRIBERS
    kinds = set(re.findall(r"(?:openAttr|dlink)\('(\w+)'", PAGE))
    assert kinds and kinds <= set(DESCRIBERS), kinds - set(DESCRIBERS)


def test_health_says_whether_the_code_changed_since_the_server_started(monkeypatch):
    from fastapi.testclient import TestClient
    from api import server
    with TestClient(server.app) as client:
        body = client.get("/health").json()
        assert body["dashboard_api"] == server.DASHBOARD_API and body["code_changed"] is False
        monkeypatch.setattr(server, "_STARTED_WITH_CODE", 0.0)       # as if every file changed since
        monkeypatch.setitem(server._code_check, "at", 0.0)
        assert client.get("/health").json()["code_changed"] is True
