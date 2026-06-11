"""Runtime environment configuration: settings model, env parsing, and validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.lifecycle_api import LifecycleWebhookAuthMode
from jedi_devproject.servicenow import load_dotenv_values


class RuntimeConfigError(ValueError):
    """Raised when runtime environment configuration is incomplete."""


class RuntimeSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    runtime_environment: str = "development"
    database_url: str
    servicenow_instance_url: str
    servicenow_client_id: str
    servicenow_client_secret: str
    servicenow_pm_instance_url: str = ""
    servicenow_pm_client_id: str = ""
    servicenow_pm_client_secret: str = ""
    servicenow_dev_instance_url: str = ""
    servicenow_dev_client_id: str = ""
    servicenow_dev_client_secret: str = ""
    worker_id: str = "jedi-devproject-worker"
    audit_root: Path
    build_claim_apply: bool = False
    build_claim_from_state: str = "Ready"
    build_claim_state: str = "Work in Progress"
    model_provider: str | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None
    admin_api_token: str | None = None
    admin_auth_mode: Literal["disabled", "dev_basic", "oidc", "servicenow_oauth"] = "disabled"
    admin_console_username: str | None = None
    admin_console_password: str | None = None
    lifecycle_webhook_auth_mode: LifecycleWebhookAuthMode = "disabled"
    lifecycle_webhook_secret: str | None = None
    lifecycle_webhook_max_skew_seconds: int = 300
    lifecycle_webhook_max_body_bytes: int = 64 * 1024
    lifecycle_rate_limit_max_requests: int = 60
    lifecycle_rate_limit_window_seconds: int = 60
    admin_rate_limit_max_requests: int = 120
    admin_rate_limit_window_seconds: int = 60
    update_set_apply: bool = False
    update_set_user_name: str | None = None
    classifier_gate: bool = True
    public_web_access: Literal["disabled", "worker"] = "disabled"
    public_web_allowed_domains: list[str] = Field(default_factory=list)
    public_web_doc_urls: list[str] = Field(default_factory=list)
    public_web_timeout_seconds: float = 3.0
    public_web_max_response_bytes: int = 128 * 1024
    public_web_max_excerpt_chars: int = 4000
    public_web_max_results: int = 3


def _env_value(values: dict[str, str], primary_key: str, fallback_key: str) -> str:
    return str(values.get(primary_key) or values.get(fallback_key) or "")


def _missing_split_servicenow_settings(
    *,
    pm_instance_url: str,
    pm_client_id: str,
    pm_client_secret: str,
    dev_instance_url: str,
    dev_client_id: str,
    dev_client_secret: str,
) -> list[str]:
    missing: list[str] = []
    if not pm_instance_url:
        missing.append("SERVICENOW_PM_INSTANCE_URL or SERVICENOW_INSTANCE_URL")
    if not pm_client_id:
        missing.append("SERVICENOW_PM_CLIENT_ID or SERVICENOW_CLIENT_ID")
    if not pm_client_secret:
        missing.append("SERVICENOW_PM_CLIENT_SECRET or SERVICENOW_CLIENT_SECRET")
    if not dev_instance_url:
        missing.append("SERVICENOW_DEV_INSTANCE_URL or SERVICENOW_INSTANCE_URL")
    if not dev_client_id:
        missing.append("SERVICENOW_DEV_CLIENT_ID or SERVICENOW_CLIENT_ID")
    if not dev_client_secret:
        missing.append("SERVICENOW_DEV_CLIENT_SECRET or SERVICENOW_CLIENT_SECRET")
    return missing


def load_runtime_settings(env_path: Path | None = None) -> RuntimeSettings:
    values = dict(os.environ)
    if env_path is not None and env_path.exists():
        values.update(load_dotenv_values(env_path))
    pm_instance_url = _env_value(values, "SERVICENOW_PM_INSTANCE_URL", "SERVICENOW_INSTANCE_URL")
    pm_client_id = _env_value(values, "SERVICENOW_PM_CLIENT_ID", "SERVICENOW_CLIENT_ID")
    pm_client_secret = _env_value(
        values,
        "SERVICENOW_PM_CLIENT_SECRET",
        "SERVICENOW_CLIENT_SECRET",
    )
    dev_instance_url = _env_value(values, "SERVICENOW_DEV_INSTANCE_URL", "SERVICENOW_INSTANCE_URL")
    dev_client_id = _env_value(values, "SERVICENOW_DEV_CLIENT_ID", "SERVICENOW_CLIENT_ID")
    dev_client_secret = _env_value(
        values,
        "SERVICENOW_DEV_CLIENT_SECRET",
        "SERVICENOW_CLIENT_SECRET",
    )
    required = [
        "DATABASE_URL",
        "JEDI_AUDIT_ROOT",
    ]
    missing = [key for key in required if not values.get(key)]
    missing.extend(
        _missing_split_servicenow_settings(
            pm_instance_url=pm_instance_url,
            pm_client_id=pm_client_id,
            pm_client_secret=pm_client_secret,
            dev_instance_url=dev_instance_url,
            dev_client_id=dev_client_id,
            dev_client_secret=dev_client_secret,
        )
    )
    if missing:
        raise RuntimeConfigError(f"Missing required runtime settings: {', '.join(missing)}")

    return RuntimeSettings(
        runtime_environment=str(values.get("JEDI_ENVIRONMENT") or "development"),
        database_url=str(values["DATABASE_URL"]),
        servicenow_instance_url=str(dev_instance_url),
        servicenow_client_id=str(dev_client_id),
        servicenow_client_secret=str(dev_client_secret),
        servicenow_pm_instance_url=str(pm_instance_url),
        servicenow_pm_client_id=str(pm_client_id),
        servicenow_pm_client_secret=str(pm_client_secret),
        servicenow_dev_instance_url=str(dev_instance_url),
        servicenow_dev_client_id=str(dev_client_id),
        servicenow_dev_client_secret=str(dev_client_secret),
        worker_id=str(values.get("JEDI_WORKER_ID") or "jedi-devproject-worker"),
        audit_root=Path(str(values["JEDI_AUDIT_ROOT"])),
        build_claim_apply=_truthy(values.get("JEDI_BUILD_CLAIM_APPLY")),
        build_claim_from_state=str(values.get("JEDI_BUILD_CLAIM_FROM_STATE") or "Ready"),
        build_claim_state=str(values.get("JEDI_BUILD_CLAIM_STATE") or "Work in Progress"),
        model_provider=_optional_str(values.get("JEDI_MODEL_PROVIDER")),
        openai_api_key=_optional_str(values.get("OPENAI_API_KEY")),
        openai_model=_optional_str(values.get("OPENAI_MODEL")),
        admin_api_token=_optional_str(values.get("JEDI_ADMIN_API_TOKEN")),
        admin_auth_mode=cast(
            Literal["disabled", "dev_basic", "oidc", "servicenow_oauth"],
            str(values.get("JEDI_ADMIN_AUTH_MODE") or "disabled"),
        ),
        admin_console_username=_optional_str(values.get("JEDI_ADMIN_CONSOLE_USERNAME")),
        admin_console_password=_optional_str(values.get("JEDI_ADMIN_CONSOLE_PASSWORD")),
        lifecycle_webhook_auth_mode=cast(
            LifecycleWebhookAuthMode,
            str(values.get("JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE") or "disabled"),
        ),
        lifecycle_webhook_secret=_optional_str(values.get("JEDI_LIFECYCLE_WEBHOOK_SECRET")),
        lifecycle_webhook_max_skew_seconds=_int_value(
            values.get("JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS"),
            default=300,
        ),
        lifecycle_webhook_max_body_bytes=_int_value(
            values.get("JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES"),
            default=64 * 1024,
        ),
        lifecycle_rate_limit_max_requests=_int_value(
            values.get("JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS"),
            default=60,
        ),
        lifecycle_rate_limit_window_seconds=_int_value(
            values.get("JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS"),
            default=60,
        ),
        admin_rate_limit_max_requests=_int_value(
            values.get("JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS"),
            default=120,
        ),
        admin_rate_limit_window_seconds=_int_value(
            values.get("JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS"),
            default=60,
        ),
        update_set_apply=_truthy(values.get("JEDI_UPDATE_SET_APPLY")),
        update_set_user_name=_optional_str(values.get("JEDI_UPDATE_SET_USER_NAME")),
        classifier_gate=_truthy(values.get("JEDI_CLASSIFIER_GATE"), default=True),
        public_web_access=cast(
            Literal["disabled", "worker"],
            str(values.get("JEDI_PUBLIC_WEB_ACCESS") or "disabled"),
        ),
        public_web_allowed_domains=_csv_values(values.get("JEDI_PUBLIC_WEB_ALLOWED_DOMAINS")),
        public_web_doc_urls=_csv_values(values.get("JEDI_PUBLIC_WEB_DOC_URLS")),
        public_web_timeout_seconds=_float_value(
            values.get("JEDI_PUBLIC_WEB_TIMEOUT_SECONDS"),
            default=3.0,
        ),
        public_web_max_response_bytes=_int_value(
            values.get("JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES"),
            default=128 * 1024,
        ),
        public_web_max_excerpt_chars=_int_value(
            values.get("JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS"),
            default=4000,
        ),
        public_web_max_results=_int_value(
            values.get("JEDI_PUBLIC_WEB_MAX_RESULTS"),
            default=3,
        ),
    )


def validate_runtime_settings(
    settings: RuntimeSettings,
    *,
    require_admin_auth: bool = True,
) -> None:
    if _runtime_environment(settings) != "production":
        return

    errors: list[str] = []
    if settings.lifecycle_webhook_auth_mode != "hmac_sha256":
        errors.append("JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE must be hmac_sha256 in production")
    elif not settings.lifecycle_webhook_secret:
        errors.append("JEDI_LIFECYCLE_WEBHOOK_SECRET is required in production")

    if require_admin_auth:
        if settings.admin_auth_mode == "disabled":
            errors.append("JEDI_ADMIN_AUTH_MODE must not be disabled in production")
        elif settings.admin_auth_mode == "dev_basic":
            errors.append("JEDI_ADMIN_AUTH_MODE=dev_basic is development-only")
        elif settings.admin_auth_mode in {"oidc", "servicenow_oauth"}:
            errors.append(f"JEDI_ADMIN_AUTH_MODE={settings.admin_auth_mode} is not implemented")

    if settings.model_provider is None:
        errors.append("JEDI_MODEL_PROVIDER is required in production")
    elif settings.model_provider != "openai":
        errors.append(f"Unsupported JEDI_MODEL_PROVIDER: {settings.model_provider}")
    elif not settings.openai_api_key or not settings.openai_model:
        if not settings.openai_api_key:
            errors.append("OPENAI_API_KEY is required when JEDI_MODEL_PROVIDER=openai")
        if not settings.openai_model:
            errors.append("OPENAI_MODEL is required when JEDI_MODEL_PROVIDER=openai")

    if settings.public_web_access == "worker" and not settings.public_web_allowed_domains:
        errors.append(
            "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS is required when public web access is enabled"
        )
    if settings.public_web_access == "worker" and not settings.public_web_doc_urls:
        errors.append("JEDI_PUBLIC_WEB_DOC_URLS is required when public web access is enabled")

    if errors:
        raise RuntimeConfigError("; ".join(errors))


def _runtime_environment(settings: RuntimeSettings) -> str:
    return settings.runtime_environment.strip().lower()


def _truthy(value: str | None, *, default: bool = False) -> bool:
    text = str(value or "").strip().lower()
    if text == "":
        return default
    return text in {"1", "true", "yes", "on"}


def _int_value(value: str | None, *, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    return int(value.strip())


def _float_value(value: str | None, *, default: float) -> float:
    if value is None or value.strip() == "":
        return default
    return float(value.strip())


def _csv_values(value: str | None) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _optional_str(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    return value.strip()
