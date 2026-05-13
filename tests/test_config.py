from pathlib import Path

import pytest

from jedi_devproject.config import ConfigError, load_config


def test_load_config_rejects_missing_required_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "empty.toml"
    config_path.write_text("", encoding="utf-8")

    with pytest.raises(ConfigError) as exc:
        load_config(config_path)

    message = str(exc.value)
    assert "servicenow_instance_url" in message
    assert "artifact_dir" in message
    assert "target_boundary" in message


def test_load_config_accepts_required_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "app.toml"
    config_path.write_text(
        '\n'.join(
            [
                'servicenow_instance_url = "https://example.service-now.com"',
                'artifact_dir = "artifacts"',
                'target_boundary = "FedRAMP Moderate"',
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.servicenow_instance_url == "https://example.service-now.com"
    assert config.artifact_dir == Path("artifacts")
    assert config.target_boundary == "FedRAMP Moderate"
