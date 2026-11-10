"""Fixtures reflect AllStarLink res_rpt_http_registrations.c's JSON contract."""

import pytest

from rpt_http.app import create_app
from rpt_http.auth import AuthUnavailable
from rpt_http.config import load_settings
from rpt_http.publisher import PublishUnavailable


class Provider:
    def get(self, node):
        return "generated-secret" if node == "1234" else None


class Publisher:
    def __init__(self):
        self.sent = []

    def publish(self, *args):
        self.sent.append(args)


@pytest.fixture
def setup(monkeypatch, tmp_path):
    monkeypatch.setenv("RPT_CONFIG_DIR", str(tmp_path))
    settings = load_settings()
    publisher = Publisher()
    app = create_app(settings, Provider(), publisher)
    return app.test_client(), publisher, app


def payload(password="generated-secret", **kwargs):
    return {
        "data": {"nodes": {"1234": {"node": "1234", "passwd": password, "remote": 0}}},
        **kwargs,
    }


def test_allstar_success_optional_port_and_forwarded_headers(setup):
    client, publisher, app = setup
    result = client.post("/", json=payload(), headers={"X-Forwarded-For": "192.0.2.99"})
    assert result.status_code == 200
    assert result.json == {
        "ipaddr": "127.0.0.1",
        "port": 4569,
        "refresh": 60,
        "data": ["1234 successfully registered."],
    }
    assert publisher.sent == [("1234", "127.0.0.1", 4569)]


def test_allstar_explicit_port(setup):
    client, publisher, _ = setup
    assert client.post("/", json=payload(port=4570)).json["port"] == 4570
    assert publisher.sent[0][2] == 4570


def test_rejection_clears_client_success_detection(setup):
    client, publisher, _ = setup
    result = client.post("/", json=payload("bad"))
    assert result.status_code == 200
    assert "successfully registered" not in str(result.json["data"])
    assert not publisher.sent


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"data": {"nodes": {}}},
        payload(port=0),
        payload(port=True),
        payload(port=65536),
        {"data": {"nodes": {"1235": {"node": "1234"}}}},
    ],
)
def test_malformed_does_not_publish(setup, body):
    client, publisher, _ = setup
    assert client.post("/", json=body).status_code == 400
    assert not publisher.sent


def test_multiple_nodes_rejected_explicitly(setup):
    client, publisher, _ = setup
    body = payload()
    body["data"]["nodes"]["5678"] = {"node": "5678", "passwd": "other"}
    assert client.post("/", json=body).status_code == 400
    assert not publisher.sent


def test_request_size_limit(setup):
    client, _, _ = setup
    assert client.post("/", data=b"x" * 17000, content_type="application/json").status_code == 413


def test_failure_throttle_does_not_publish(setup):
    client, publisher, _ = setup
    for _ in range(5):
        assert client.post("/", json=payload("bad")).status_code == 200
    assert client.post("/", json=payload()).status_code == 429
    assert not publisher.sent


def test_unavailable(monkeypatch, tmp_path):
    monkeypatch.setenv("RPT_CONFIG_DIR", str(tmp_path))

    class Broken:
        def get(self, node):
            raise AuthUnavailable()

    publisher = Publisher()
    app = create_app(load_settings(), Broken(), publisher)
    assert app.test_client().post("/", json=payload()).status_code == 503
    assert not publisher.sent


def test_publish_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("RPT_CONFIG_DIR", str(tmp_path))

    class Broken:
        def publish(self, *args):
            raise PublishUnavailable()

    app = create_app(load_settings(), Provider(), Broken())
    result = app.test_client().post("/", json=payload())
    assert result.status_code == 503
    assert "successfully registered" not in str(result.json)


def test_proxy_trust_requires_matching_peer(monkeypatch, tmp_path):
    monkeypatch.setenv("RPT_CONFIG_DIR", str(tmp_path))
    settings = load_settings(http={"trusted_proxies": ["192.0.2.0/24"]})
    app = create_app(settings, Provider(), Publisher())
    client = app.test_client()
    headers = {"X-Forwarded-For": "198.51.100.5"}
    assert client.post("/", json=payload(), headers=headers).json["ipaddr"] == "127.0.0.1"
    result = client.post(
        "/", json=payload(), headers=headers, environ_base={"REMOTE_ADDR": "192.0.2.5"}
    )
    assert result.json["ipaddr"] == "198.51.100.5"
