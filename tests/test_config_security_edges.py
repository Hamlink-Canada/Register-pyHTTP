import pytest

from rpt_http.config import load_settings
from rpt_http.security import AbuseGuard


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch, tmp_path):
    monkeypatch.setenv("RPT_CONFIG_DIR", str(tmp_path))


@pytest.mark.parametrize(
    "overrides",
    [
        {"port": 65536},
        {"refresh": 0},
        {"lifetime": 60, "refresh": 60},
        {"server_id": ""},
        {"kafka": {"security_protocol": "SSL"}},
        {"kafka": {"security_protocol": "SASL_SSL"}},
        {"limits": {"workers": True}},
    ],
)
def test_http_config_rejects_invalid_values(overrides):
    with pytest.raises(ValueError):
        load_settings(**overrides)


def test_http_config_loads_nested_file_environment_and_override(monkeypatch, tmp_path):
    (tmp_path / "settings.toml").write_text('[kafka]\ntopic="from-file"\n')
    monkeypatch.setenv("RPT_KAFKA__TOPIC", "from-environment")
    settings = load_settings(kafka={"topic": "from-override"})
    assert settings.KAFKA.TOPIC == "from-override"
    assert settings.AUTH.CACHE_SIZE == 4096


def test_abuse_guard_throttles_then_refills_and_tracks_outcomes():
    settings = load_settings(
        limits={
            "global_rate": 60,
            "global_burst": 1,
            "source_rate": 60,
            "source_burst": 10,
            "fail_ip_burst": 1,
            "fail_pair_burst": 1,
            "refresh_burst": 1,
        }
    )
    now = [10.0]
    guard = AbuseGuard(settings, timer=lambda: now[0])
    assert guard.ingress("192.0.2.1")
    assert not guard.ingress("192.0.2.2")
    assert guard.metrics["throttled"] == 1
    now[0] += 1
    assert guard.ingress("192.0.2.2")

    assert guard.auth_allowed("192.0.2.1", "1234")
    guard.failure("192.0.2.1", "1234")
    assert not guard.auth_allowed("192.0.2.1", "1234")
    assert guard.success("192.0.2.1", "1234")
    assert not guard.success("192.0.2.1", "1234")
    assert guard.metrics["auth_failure"] == 1
    assert guard.metrics["auth_success"] == 2


def test_abuse_guard_bounds_state_and_records_rejection():
    settings = load_settings(limits={"state_size": 2, "global_burst": 100})
    guard = AbuseGuard(settings, timer=lambda: 0)
    assert guard.ingress("192.0.2.1")
    assert not guard.ingress("192.0.2.2")
    assert len(guard.buckets) == 2
    assert guard.metrics["state_full"] == 1
