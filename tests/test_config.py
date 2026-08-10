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
        "\n".join(
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


@pytest.mark.parametrize(
    ("setting_line", "expected_error"),
    [
        (
            'servicenow_instance_url = "http://example.service-now.com"',
            "servicenow_instance_url",
        ),
        (
            'servicenow_instance_url = "https://user:secret@example.service-now.com"',
            "servicenow_instance_url",
        ),
        (
            'servicenow_instance_url = "https://example.service-now.com#fragment"',
            "servicenow_instance_url",
        ),
        (
            'servicenow_instance_url = "https://example.service-now.com/%0aheader"',
            "servicenow_instance_url",
        ),
        ('artifact_dir = " artifacts"', "artifact_dir"),
        ('artifact_dir = "artifacts\tfallback"', "artifact_dir"),
        ('target_boundary = " FedRAMP Moderate"', "target_boundary"),
        ('target_boundary = "FedRAMP Moderate\tfallback"', "target_boundary"),
        ('target_boundary = "FedRAMP\u200bModerate"', "target_boundary"),
    ],
)
def test_load_config_rejects_malformed_required_values(
    tmp_path: Path,
    setting_line: str,
    expected_error: str,
) -> None:
    config_path = tmp_path / "app.toml"
    settings = {
        "servicenow_instance_url": ('servicenow_instance_url = "https://example.service-now.com"'),
        "artifact_dir": 'artifact_dir = "artifacts"',
        "target_boundary": 'target_boundary = "FedRAMP Moderate"',
    }
    setting_name = setting_line.split("=", maxsplit=1)[0].strip()
    settings[setting_name] = setting_line
    config_path.write_text(
        "\n".join(
            [
                settings["servicenow_instance_url"],
                settings["artifact_dir"],
                settings["target_boundary"],
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match=expected_error) as exc:
        load_config(config_path)

    message = str(exc.value)
    assert "secret" not in message
    assert "fallback" not in message
    assert "\t" not in message


def test_load_config_rejects_oversized_toml_without_whole_file_text_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "app.toml"
    config_path.write_text('servicenow_instance_url = "https://example.gov"\n', encoding="utf-8")
    monkeypatch.setattr(
        "jedi_devproject.config.PROJECT_CONFIG_MAX_BYTES",
        4,
        raising=False,
    )

    def fail_read_text(
        self: Path,
        encoding: str | None = None,
        errors: str | None = None,
    ) -> str:
        raise AssertionError(f"unexpected whole-file text read for {self}")

    monkeypatch.setattr(Path, "read_text", fail_read_text)

    with pytest.raises(ConfigError, match="project_config_too_large"):
        load_config(config_path)


def test_load_config_oversized_error_does_not_echo_config_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "client_secret=config-loader-secret.toml"
    config_path.write_text('servicenow_instance_url = "https://example.gov"\n', encoding="utf-8")
    monkeypatch.setattr(
        "jedi_devproject.config.PROJECT_CONFIG_MAX_BYTES",
        4,
        raising=False,
    )

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_path)

    diagnostic = str(exc_info.value)
    assert "project_config_too_large" in diagnostic
    assert "config-loader-secret" not in diagnostic
    assert str(config_path) not in diagnostic


def test_load_config_rejects_symlinked_toml(tmp_path: Path) -> None:
    target_path = tmp_path / "target.toml"
    target_path.write_text(
        "\n".join(
            [
                'servicenow_instance_url = "https://example.service-now.com"',
                'artifact_dir = "artifacts"',
                'target_boundary = "FedRAMP Moderate"',
            ]
        ),
        encoding="utf-8",
    )
    config_link = tmp_path / "app.toml"
    config_link.symlink_to(target_path)

    with pytest.raises(ConfigError, match="project_config_must_be_regular_file"):
        load_config(config_link)


def test_load_config_regular_file_error_does_not_echo_config_path(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "target.toml"
    target_path.write_text(
        "\n".join(
            [
                'servicenow_instance_url = "https://example.service-now.com"',
                'artifact_dir = "artifacts"',
                'target_boundary = "FedRAMP Moderate"',
            ]
        ),
        encoding="utf-8",
    )
    config_link = tmp_path / "client_secret=config-link-secret.toml"
    config_link.symlink_to(target_path)

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_link)

    diagnostic = str(exc_info.value)
    assert "project_config_must_be_regular_file" in diagnostic
    assert "config-link-secret" not in diagnostic
    assert str(config_link) not in diagnostic
    assert exc_info.value.__cause__ is None


def test_load_config_invalid_utf8_error_does_not_echo_config_path_or_bytes(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "client_secret=config-utf8-secret.toml"
    config_path.write_bytes(b'servicenow_instance_url = "https://example.gov"\xff\n')

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_path)

    diagnostic = str(exc_info.value)
    assert "project_config_invalid_utf8" in diagnostic
    assert "config-utf8-secret" not in diagnostic
    assert str(config_path) not in diagnostic
    assert "servicenow_instance_url" not in diagnostic
    assert exc_info.value.__cause__ is None
