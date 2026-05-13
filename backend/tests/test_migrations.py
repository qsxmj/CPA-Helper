from pathlib import Path

from alembic.config import Config
from sqlalchemy import inspect

from alembic import command
from app.db.session import get_engine, reset_engine_for_tests


def _alembic_config() -> Config:
    backend_root = Path(__file__).resolve().parents[1]
    return Config(str(backend_root / "alembic.ini"))


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in inspect(get_engine()).get_columns(table_name)}


def test_theme_preference_migration_removes_app_settings_column(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CPA_HELPER_DATA_DIR", str(tmp_path))
    reset_engine_for_tests()
    config = _alembic_config()

    try:
        command.upgrade(config, "20260511_0005")
        assert "theme_preference" in _column_names("app_settings")

        command.upgrade(config, "head")
        assert "theme_preference" not in _column_names("app_settings")

        command.downgrade(config, "20260511_0005")
        assert "theme_preference" in _column_names("app_settings")
    finally:
        reset_engine_for_tests()
