import pytest
from pydantic import ValidationError

from app.core.config import DEVELOPMENT_TOKEN_SECRET, Settings


def test_default_settings(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.delenv("APP_ENV", raising=False)
    settings = Settings(_env_file=None)
    assert settings.app_name == "RelayGuard"
    assert settings.app_env == "development"
    assert settings.app_port == 8000
    assert settings.access_token_expire_minutes == 30
    assert settings.sync_database_url.startswith("postgresql+psycopg2://")


def test_settings_from_environment(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.setenv("APP_NAME", "RelayGuard Test")
    settings = Settings(_env_file=None)
    assert settings.app_name == "RelayGuard Test"


@pytest.mark.parametrize(
    "values",
    [
        {"access_token_secret": "short"},
        {"access_token_expire_minutes": 4},
        {"access_token_expire_minutes": 1441},
        {"app_env": "production", "access_token_secret": DEVELOPMENT_TOKEN_SECRET},
    ],
)
def test_rejects_insecure_token_configuration(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)  # type: ignore[arg-type]
