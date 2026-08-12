from app.core.config import Settings


def test_default_settings() -> None:
    settings = Settings(_env_file=None)
    assert settings.app_name == "RelayGuard"
    assert settings.app_env == "development"
    assert settings.app_port == 8000


def test_settings_from_environment(monkeypatch: object) -> None:
    # pytest's monkeypatch type is deliberately avoided in production dependencies.
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.setenv("APP_NAME", "RelayGuard Test")
    settings = Settings(_env_file=None)
    assert settings.app_name == "RelayGuard Test"
