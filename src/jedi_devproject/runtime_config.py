"""Runtime environment configuration: settings model, env parsing, and validation."""

from __future__ import annotations

import os
from math import isfinite
from pathlib import Path
from typing import Literal, cast
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject import (
    admin_basic_auth_policy,
    admin_token_policy,
    lifecycle_webhook_policy,
)
from jedi_devproject.alert_webhook_url import validate_alert_webhook_url
from jedi_devproject.exception_diagnostics import exception_diagnostic_message
from jedi_devproject.lifecycle_api import LifecycleWebhookAuthMode
from jedi_devproject.numeric_settings import (
    parse_optional_ascii_decimal_float,
    parse_optional_base10_int,
)
from jedi_devproject.provider_settings_safety import (
    validate_provider_api_key,
    validate_provider_model,
)
from jedi_devproject.rate_limit import (
    MAX_CONFIGURABLE_RATE_LIMIT_BUCKETS,
    MAX_CONFIGURABLE_RATE_LIMIT_REQUESTS,
    MAX_CONFIGURABLE_RATE_LIMIT_WINDOW_SECONDS,
    MAX_RATE_LIMIT_BUCKETS,
)
from jedi_devproject.servicenow import load_dotenv_values
from jedi_devproject.url_host_safety import is_non_public_hostname, normalize_hostname
from jedi_devproject.url_query_safety import (
    has_encoded_whitespace_or_control_character,
    has_whitespace_or_control_character,
    sensitive_query_keys,
)

MIN_PRODUCTION_WEBHOOK_SECRET_LENGTH = 32
MAX_PRODUCTION_LIFECYCLE_WEBHOOK_SECRET_BYTES = (
    lifecycle_webhook_policy.MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES
)
MIN_PRODUCTION_ADMIN_API_TOKEN_LENGTH = 32
MAX_ADMIN_CONSOLE_CREDENTIAL_BYTES = admin_basic_auth_policy.MAX_BASIC_AUTH_CREDENTIAL_BYTES
MAX_PRODUCTION_ADMIN_API_TOKEN_BYTES = admin_token_policy.MAX_ADMIN_BEARER_TOKEN_BYTES
MAX_PRODUCTION_LIFECYCLE_WEBHOOK_SKEW_SECONDS = 15 * 60
MIN_PRODUCTION_HSTS_MAX_AGE_SECONDS = 365 * 24 * 60 * 60
MAX_PRODUCTION_LIFECYCLE_WEBHOOK_BODY_BYTES = 1024 * 1024
MAX_PRODUCTION_ADMIN_BODY_BYTES = 64 * 1024
MAX_PRODUCTION_ALERT_WEBHOOK_BODY_BYTES = 64 * 1024
MAX_PRODUCTION_RUNNING_JOB_STALE_AFTER_SECONDS = 24 * 60 * 60
MAX_PRODUCTION_OUTBOUND_TIMEOUT_SECONDS = 30.0
MAX_PRODUCTION_PUBLIC_WEB_RESPONSE_BYTES = 1024 * 1024
MAX_PRODUCTION_PUBLIC_WEB_EXCERPT_CHARS = 16_000
MAX_PRODUCTION_PUBLIC_WEB_RESULTS = 10
MAX_MODEL_PROVIDER_CHARS = 256
ADMIN_AUTH_MODES = {"disabled", "dev_basic", "oidc", "servicenow_oauth"}
JEDI_MODEL_PROVIDER_CONTROL_ERROR = (
    "JEDI_MODEL_PROVIDER must not contain whitespace or control characters"
)
JEDI_MODEL_PROVIDER_UNSUPPORTED_ERROR = "Unsupported JEDI_MODEL_PROVIDER"
RUNTIME_PATH_SETTING_TYPE = type(Path())


class RuntimeConfigError(ValueError):
    """Raised when runtime environment configuration is incomplete."""


class RuntimeSettings(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        hide_input_in_errors=True,
    )

    runtime_environment: str = "development"
    runtime_role: Literal["combined", "api", "worker"] = "combined"
    allow_combined_production: bool = False
    trusted_hosts: list[str] = Field(default_factory=list)
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
    lifecycle_webhook_previous_secret: str | None = None
    lifecycle_webhook_max_skew_seconds: int = 300
    lifecycle_webhook_max_body_bytes: int = 64 * 1024
    lifecycle_rate_limit_max_requests: int = 60
    lifecycle_rate_limit_window_seconds: int = 60
    lifecycle_rate_limit_max_buckets: int = MAX_RATE_LIMIT_BUCKETS
    admin_rate_limit_max_requests: int = 120
    admin_rate_limit_window_seconds: int = 60
    admin_rate_limit_max_buckets: int = MAX_RATE_LIMIT_BUCKETS
    admin_max_body_bytes: int = 8 * 1024
    strict_transport_security_enabled: bool = False
    strict_transport_security_max_age_seconds: int = 365 * 24 * 60 * 60
    running_job_stale_after_seconds: int = 60 * 60
    alert_webhook_enabled: bool = False
    alert_webhook_url: str | None = None
    alert_webhook_timeout_seconds: float = 3.0
    alert_webhook_max_body_bytes: int = 16 * 1024
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
    primary = _runtime_setting_text(values.get(primary_key), name=primary_key)
    if primary != "":
        return primary
    return _runtime_setting_text(values.get(fallback_key), name=fallback_key)


def _blank_split_servicenow_override_errors(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    fallback_by_key = {
        "SERVICENOW_PM_INSTANCE_URL": "SERVICENOW_INSTANCE_URL",
        "SERVICENOW_PM_CLIENT_ID": "SERVICENOW_CLIENT_ID",
        "SERVICENOW_PM_CLIENT_SECRET": "SERVICENOW_CLIENT_SECRET",  # nosec B105
        "SERVICENOW_DEV_INSTANCE_URL": "SERVICENOW_INSTANCE_URL",
        "SERVICENOW_DEV_CLIENT_ID": "SERVICENOW_CLIENT_ID",
        "SERVICENOW_DEV_CLIENT_SECRET": "SERVICENOW_CLIENT_SECRET",  # nosec B105
    }
    for key, fallback_key in fallback_by_key.items():
        if key in values and _runtime_setting_text(values[key], name=key).strip() == "":
            errors.append(
                f"{key} must not be empty when configured; remove it to use {fallback_key}"
            )
    return errors


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
    blank_split_errors = _blank_split_servicenow_override_errors(values)
    if blank_split_errors:
        raise RuntimeConfigError("; ".join(blank_split_errors))
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
    servicenow_url_errors = _servicenow_instance_url_value_errors(
        values_by_name={
            "SERVICENOW_PM_INSTANCE_URL": pm_instance_url,
            "SERVICENOW_DEV_INSTANCE_URL": dev_instance_url,
        },
        detail="",
    )
    if servicenow_url_errors:
        raise RuntimeConfigError("; ".join(servicenow_url_errors))
    servicenow_credential_errors = _servicenow_oauth_value_errors(
        values_by_name={
            "SERVICENOW_PM_CLIENT_ID": pm_client_id,
            "SERVICENOW_PM_CLIENT_SECRET": pm_client_secret,
            "SERVICENOW_DEV_CLIENT_ID": dev_client_id,
            "SERVICENOW_DEV_CLIENT_SECRET": dev_client_secret,
        },
        detail="",
    )
    if servicenow_credential_errors:
        raise RuntimeConfigError("; ".join(servicenow_credential_errors))
    database_url = _runtime_setting_text(values["DATABASE_URL"], name="DATABASE_URL")
    audit_root = _runtime_setting_text(values["JEDI_AUDIT_ROOT"], name="JEDI_AUDIT_ROOT")
    store_and_audit_errors = _database_url_value_errors(
        database_url,
        detail="",
    )
    store_and_audit_errors.extend(
        _audit_root_value_errors(
            Path(audit_root),
            detail="",
        )
    )
    if store_and_audit_errors:
        raise RuntimeConfigError("; ".join(store_and_audit_errors))

    settings = RuntimeSettings(
        runtime_environment=_runtime_environment_value(values.get("JEDI_ENVIRONMENT")),
        runtime_role=cast(
            Literal["combined", "api", "worker"],
            _enum_value(
                values.get("JEDI_RUNTIME_ROLE"),
                name="JEDI_RUNTIME_ROLE",
                allowed={"combined", "api", "worker"},
                default="combined",
            ),
        ),
        allow_combined_production=_bool_value(
            values.get("JEDI_ALLOW_COMBINED_PRODUCTION"),
            name="JEDI_ALLOW_COMBINED_PRODUCTION",
        ),
        trusted_hosts=_csv_values(
            values.get("JEDI_TRUSTED_HOSTS"),
            name="JEDI_TRUSTED_HOSTS",
        ),
        database_url=database_url,
        servicenow_instance_url=str(dev_instance_url),
        servicenow_client_id=str(dev_client_id),
        servicenow_client_secret=str(dev_client_secret),
        servicenow_pm_instance_url=str(pm_instance_url),
        servicenow_pm_client_id=str(pm_client_id),
        servicenow_pm_client_secret=str(pm_client_secret),
        servicenow_dev_instance_url=str(dev_instance_url),
        servicenow_dev_client_id=str(dev_client_id),
        servicenow_dev_client_secret=str(dev_client_secret),
        worker_id=_optional_unpadded_control_free_str(
            values.get("JEDI_WORKER_ID"),
            name="JEDI_WORKER_ID",
            default="jedi-devproject-worker",
        ),
        audit_root=Path(audit_root),
        build_claim_apply=_bool_value(
            values.get("JEDI_BUILD_CLAIM_APPLY"),
            name="JEDI_BUILD_CLAIM_APPLY",
        ),
        build_claim_from_state=_optional_unpadded_control_free_str(
            values.get("JEDI_BUILD_CLAIM_FROM_STATE"),
            name="JEDI_BUILD_CLAIM_FROM_STATE",
            default="Ready",
        ),
        build_claim_state=_optional_unpadded_control_free_str(
            values.get("JEDI_BUILD_CLAIM_STATE"),
            name="JEDI_BUILD_CLAIM_STATE",
            default="Work in Progress",
        ),
        model_provider=_optional_model_provider(values.get("JEDI_MODEL_PROVIDER")),
        openai_api_key=_optional_openai_provider_value(
            values.get("OPENAI_API_KEY"),
            name="OPENAI_API_KEY",
        ),
        openai_model=_optional_openai_provider_value(
            values.get("OPENAI_MODEL"),
            name="OPENAI_MODEL",
        ),
        admin_api_token=_optional_unpadded_control_free_setting(
            values.get("JEDI_ADMIN_API_TOKEN"),
            name="JEDI_ADMIN_API_TOKEN",
        ),
        admin_auth_mode=cast(
            Literal["disabled", "dev_basic", "oidc", "servicenow_oauth"],
            _enum_value(
                values.get("JEDI_ADMIN_AUTH_MODE"),
                name="JEDI_ADMIN_AUTH_MODE",
                allowed=ADMIN_AUTH_MODES,
                default="disabled",
            ),
        ),
        admin_console_username=_optional_admin_console_credential(
            values.get("JEDI_ADMIN_CONSOLE_USERNAME"),
            name="JEDI_ADMIN_CONSOLE_USERNAME",
        ),
        admin_console_password=_optional_admin_console_credential(
            values.get("JEDI_ADMIN_CONSOLE_PASSWORD"),
            name="JEDI_ADMIN_CONSOLE_PASSWORD",
        ),
        lifecycle_webhook_auth_mode=cast(
            LifecycleWebhookAuthMode,
            _enum_value(
                values.get("JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE"),
                name="JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE",
                allowed={"disabled", "shared_secret", "hmac_sha256", "servicenow_oauth"},
                default="disabled",
            ),
        ),
        lifecycle_webhook_secret=_optional_unpadded_control_free_setting(
            values.get("JEDI_LIFECYCLE_WEBHOOK_SECRET"),
            name="JEDI_LIFECYCLE_WEBHOOK_SECRET",
        ),
        lifecycle_webhook_previous_secret=_optional_unpadded_control_free_setting(
            values.get("JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET"),
            name="JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET",
        ),
        lifecycle_webhook_max_skew_seconds=_int_value(
            values.get("JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS"),
            name="JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS",
            default=300,
        ),
        lifecycle_webhook_max_body_bytes=_int_value(
            values.get("JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES"),
            name="JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES",
            default=64 * 1024,
        ),
        lifecycle_rate_limit_max_requests=_int_value(
            values.get("JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS"),
            name="JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS",
            default=60,
        ),
        lifecycle_rate_limit_window_seconds=_int_value(
            values.get("JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS"),
            name="JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS",
            default=60,
        ),
        lifecycle_rate_limit_max_buckets=_int_value(
            values.get("JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS"),
            name="JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS",
            default=MAX_RATE_LIMIT_BUCKETS,
        ),
        admin_rate_limit_max_requests=_int_value(
            values.get("JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS"),
            name="JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS",
            default=120,
        ),
        admin_rate_limit_window_seconds=_int_value(
            values.get("JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS"),
            name="JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS",
            default=60,
        ),
        admin_rate_limit_max_buckets=_int_value(
            values.get("JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS"),
            name="JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS",
            default=MAX_RATE_LIMIT_BUCKETS,
        ),
        admin_max_body_bytes=_int_value(
            values.get("JEDI_ADMIN_MAX_BODY_BYTES"),
            name="JEDI_ADMIN_MAX_BODY_BYTES",
            default=8 * 1024,
        ),
        strict_transport_security_enabled=_bool_value(
            values.get("JEDI_STRICT_TRANSPORT_SECURITY_ENABLED"),
            name="JEDI_STRICT_TRANSPORT_SECURITY_ENABLED",
        ),
        strict_transport_security_max_age_seconds=_int_value(
            values.get("JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS"),
            name="JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS",
            default=365 * 24 * 60 * 60,
        ),
        running_job_stale_after_seconds=_int_value(
            values.get("JEDI_RUNNING_JOB_STALE_AFTER_SECONDS"),
            name="JEDI_RUNNING_JOB_STALE_AFTER_SECONDS",
            default=60 * 60,
        ),
        alert_webhook_enabled=_bool_value(
            values.get("JEDI_ALERT_WEBHOOK_ENABLED"),
            name="JEDI_ALERT_WEBHOOK_ENABLED",
        ),
        alert_webhook_url=_optional_alert_webhook_url(values.get("JEDI_ALERT_WEBHOOK_URL")),
        alert_webhook_timeout_seconds=_float_value(
            values.get("JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS"),
            name="JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS",
            default=3.0,
        ),
        alert_webhook_max_body_bytes=_int_value(
            values.get("JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES"),
            name="JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES",
            default=16 * 1024,
        ),
        update_set_apply=_bool_value(
            values.get("JEDI_UPDATE_SET_APPLY"),
            name="JEDI_UPDATE_SET_APPLY",
        ),
        update_set_user_name=_optional_unpadded_control_free_setting(
            values.get("JEDI_UPDATE_SET_USER_NAME"),
            name="JEDI_UPDATE_SET_USER_NAME",
        ),
        classifier_gate=_bool_value(
            values.get("JEDI_CLASSIFIER_GATE"),
            name="JEDI_CLASSIFIER_GATE",
            default=True,
        ),
        public_web_access=cast(
            Literal["disabled", "worker"],
            _enum_value(
                values.get("JEDI_PUBLIC_WEB_ACCESS"),
                name="JEDI_PUBLIC_WEB_ACCESS",
                allowed={"disabled", "worker"},
                default="disabled",
            ),
        ),
        public_web_allowed_domains=_csv_values(
            values.get("JEDI_PUBLIC_WEB_ALLOWED_DOMAINS"),
            name="JEDI_PUBLIC_WEB_ALLOWED_DOMAINS",
        ),
        public_web_doc_urls=_csv_values(
            values.get("JEDI_PUBLIC_WEB_DOC_URLS"),
            name="JEDI_PUBLIC_WEB_DOC_URLS",
        ),
        public_web_timeout_seconds=_float_value(
            values.get("JEDI_PUBLIC_WEB_TIMEOUT_SECONDS"),
            name="JEDI_PUBLIC_WEB_TIMEOUT_SECONDS",
            default=3.0,
        ),
        public_web_max_response_bytes=_int_value(
            values.get("JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES"),
            name="JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES",
            default=128 * 1024,
        ),
        public_web_max_excerpt_chars=_int_value(
            values.get("JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS"),
            name="JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS",
            default=4000,
        ),
        public_web_max_results=_int_value(
            values.get("JEDI_PUBLIC_WEB_MAX_RESULTS"),
            name="JEDI_PUBLIC_WEB_MAX_RESULTS",
            default=3,
        ),
    )
    public_web_errors = _public_web_worker_settings_errors(settings)
    if public_web_errors:
        raise RuntimeConfigError("; ".join(public_web_errors))
    return settings


def validate_runtime_settings(
    settings: RuntimeSettings,
    *,
    require_admin_auth: bool = True,
) -> None:
    environment = _runtime_environment(settings)
    runtime_role = _runtime_role(settings)
    if environment not in {"development", "production"}:
        raise RuntimeConfigError("JEDI_ENVIRONMENT must be one of: development, production")
    if environment != "production":
        return

    errors: list[str] = []
    lifecycle_webhook_secret = _direct_optional_runtime_setting_text(
        settings.lifecycle_webhook_secret,
        name="JEDI_LIFECYCLE_WEBHOOK_SECRET",
    )
    lifecycle_webhook_previous_secret = _direct_optional_runtime_setting_text(
        settings.lifecycle_webhook_previous_secret,
        name="JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET",
    )
    lifecycle_webhook_auth_mode = _runtime_setting_text(
        settings.lifecycle_webhook_auth_mode,
        name="JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE",
    )
    admin_api_token = _direct_optional_runtime_setting_text(
        settings.admin_api_token,
        name="JEDI_ADMIN_API_TOKEN",
    )
    admin_auth_mode = _runtime_setting_text(
        settings.admin_auth_mode,
        name="JEDI_ADMIN_AUTH_MODE",
    )
    admin_console_username = _direct_optional_runtime_setting_text(
        settings.admin_console_username,
        name="JEDI_ADMIN_CONSOLE_USERNAME",
    )
    admin_console_password = _direct_optional_runtime_setting_text(
        settings.admin_console_password,
        name="JEDI_ADMIN_CONSOLE_PASSWORD",
    )
    model_provider = _direct_optional_runtime_setting_text(
        settings.model_provider,
        name="JEDI_MODEL_PROVIDER",
    )
    openai_api_key = _direct_optional_runtime_setting_text(
        settings.openai_api_key,
        name="OPENAI_API_KEY",
    )
    openai_model = _direct_optional_runtime_setting_text(
        settings.openai_model,
        name="OPENAI_MODEL",
    )
    public_web_access = _runtime_setting_text(
        settings.public_web_access,
        name="JEDI_PUBLIC_WEB_ACCESS",
    )
    public_web_allowed_domains = _runtime_setting_text_list(
        settings.public_web_allowed_domains,
        name="JEDI_PUBLIC_WEB_ALLOWED_DOMAINS",
    )
    public_web_doc_urls = _runtime_setting_text_list(
        settings.public_web_doc_urls,
        name="JEDI_PUBLIC_WEB_DOC_URLS",
    )
    trusted_hosts = _runtime_setting_text_list(
        settings.trusted_hosts,
        name="JEDI_TRUSTED_HOSTS",
    )
    worker_id = _runtime_setting_text(settings.worker_id, name="JEDI_WORKER_ID")
    update_set_user_name = _direct_optional_runtime_setting_text(
        settings.update_set_user_name,
        name="JEDI_UPDATE_SET_USER_NAME",
    )
    alert_webhook_url = _direct_optional_runtime_setting_text(
        settings.alert_webhook_url,
        name="JEDI_ALERT_WEBHOOK_URL",
    )
    lifecycle_webhook_max_skew_seconds = _runtime_setting_int(
        settings.lifecycle_webhook_max_skew_seconds,
        name="JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS",
    )
    lifecycle_webhook_max_body_bytes = _runtime_setting_int(
        settings.lifecycle_webhook_max_body_bytes,
        name="JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES",
    )
    lifecycle_rate_limit_max_requests = _runtime_setting_int(
        settings.lifecycle_rate_limit_max_requests,
        name="JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS",
    )
    lifecycle_rate_limit_window_seconds = _runtime_setting_int(
        settings.lifecycle_rate_limit_window_seconds,
        name="JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS",
    )
    lifecycle_rate_limit_max_buckets = _runtime_setting_int(
        settings.lifecycle_rate_limit_max_buckets,
        name="JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS",
    )
    admin_rate_limit_max_requests = _runtime_setting_int(
        settings.admin_rate_limit_max_requests,
        name="JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS",
    )
    admin_rate_limit_window_seconds = _runtime_setting_int(
        settings.admin_rate_limit_window_seconds,
        name="JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS",
    )
    admin_rate_limit_max_buckets = _runtime_setting_int(
        settings.admin_rate_limit_max_buckets,
        name="JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS",
    )
    admin_max_body_bytes = _runtime_setting_int(
        settings.admin_max_body_bytes,
        name="JEDI_ADMIN_MAX_BODY_BYTES",
    )
    strict_transport_security_max_age_seconds = _runtime_setting_int(
        settings.strict_transport_security_max_age_seconds,
        name="JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS",
    )
    running_job_stale_after_seconds = _runtime_setting_int(
        settings.running_job_stale_after_seconds,
        name="JEDI_RUNNING_JOB_STALE_AFTER_SECONDS",
    )
    alert_webhook_max_body_bytes = _runtime_setting_int(
        settings.alert_webhook_max_body_bytes,
        name="JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES",
    )
    public_web_max_response_bytes = _runtime_setting_int(
        settings.public_web_max_response_bytes,
        name="JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES",
    )
    public_web_max_excerpt_chars = _runtime_setting_int(
        settings.public_web_max_excerpt_chars,
        name="JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS",
    )
    public_web_max_results = _runtime_setting_int(
        settings.public_web_max_results,
        name="JEDI_PUBLIC_WEB_MAX_RESULTS",
    )
    alert_webhook_timeout_seconds = _runtime_setting_float(
        settings.alert_webhook_timeout_seconds,
        name="JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS",
    )
    public_web_timeout_seconds = _runtime_setting_float(
        settings.public_web_timeout_seconds,
        name="JEDI_PUBLIC_WEB_TIMEOUT_SECONDS",
    )
    allow_combined_production = _runtime_setting_bool(
        settings.allow_combined_production,
        name="JEDI_ALLOW_COMBINED_PRODUCTION",
    )
    build_claim_apply = _runtime_setting_bool(
        settings.build_claim_apply,
        name="JEDI_BUILD_CLAIM_APPLY",
    )
    strict_transport_security_enabled = _runtime_setting_bool(
        settings.strict_transport_security_enabled,
        name="JEDI_STRICT_TRANSPORT_SECURITY_ENABLED",
    )
    alert_webhook_enabled = _runtime_setting_bool(
        settings.alert_webhook_enabled,
        name="JEDI_ALERT_WEBHOOK_ENABLED",
    )
    update_set_apply = _runtime_setting_bool(
        settings.update_set_apply,
        name="JEDI_UPDATE_SET_APPLY",
    )
    classifier_gate = _runtime_setting_bool(
        settings.classifier_gate,
        name="JEDI_CLASSIFIER_GATE",
    )
    if runtime_role == "api":
        errors.extend(
            _api_runtime_role_errors(
                model_provider=model_provider,
                openai_api_key=openai_api_key,
                openai_model=openai_model,
                public_web_access=public_web_access,
                build_claim_apply=build_claim_apply,
                update_set_apply=update_set_apply,
            )
        )
    elif runtime_role == "worker":
        errors.extend(
            _worker_runtime_role_errors(
                lifecycle_webhook_auth_mode=lifecycle_webhook_auth_mode,
                lifecycle_webhook_secret=lifecycle_webhook_secret,
                lifecycle_webhook_previous_secret=lifecycle_webhook_previous_secret,
                trusted_hosts=trusted_hosts,
                admin_api_token=admin_api_token,
                admin_auth_mode=admin_auth_mode,
                admin_console_username=admin_console_username,
                admin_console_password=admin_console_password,
            )
        )
    elif runtime_role == "combined" and not allow_combined_production:
        errors.append(
            "JEDI_ALLOW_COMBINED_PRODUCTION=true is required when "
            "JEDI_RUNTIME_ROLE=combined in production"
        )
    if runtime_role != "combined" and allow_combined_production:
        errors.append(
            "JEDI_ALLOW_COMBINED_PRODUCTION=true is only valid when "
            "JEDI_RUNTIME_ROLE=combined in production"
        )

    if runtime_role in {"combined", "api"}:
        invalid_trusted_hosts = _invalid_trusted_hosts(trusted_hosts)
        if not trusted_hosts:
            errors.append("JEDI_TRUSTED_HOSTS is required for public production runtime roles")
        elif invalid_trusted_hosts:
            errors.append(
                "JEDI_TRUSTED_HOSTS must contain hostnames or wildcard subdomains without "
                "schemes, paths, padding, whitespace, control characters, local hosts, or "
                "wildcard-all entries"
            )
        if lifecycle_webhook_auth_mode != "hmac_sha256":
            errors.append("JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE must be hmac_sha256 in production")
        elif not lifecycle_webhook_secret:
            errors.append("JEDI_LIFECYCLE_WEBHOOK_SECRET is required in production")
        elif len(lifecycle_webhook_secret) < MIN_PRODUCTION_WEBHOOK_SECRET_LENGTH:
            errors.append(
                "JEDI_LIFECYCLE_WEBHOOK_SECRET must be at least "
                f"{MIN_PRODUCTION_WEBHOOK_SECRET_LENGTH} characters in production"
            )
        elif (
            lifecycle_webhook_policy.lifecycle_webhook_credential_byte_length(
                lifecycle_webhook_secret
            )
            > MAX_PRODUCTION_LIFECYCLE_WEBHOOK_SECRET_BYTES
        ):
            errors.append(
                "JEDI_LIFECYCLE_WEBHOOK_SECRET must be at most "
                f"{MAX_PRODUCTION_LIFECYCLE_WEBHOOK_SECRET_BYTES} bytes in production"
            )
        elif has_whitespace_or_control_character(lifecycle_webhook_secret):
            errors.append(
                "JEDI_LIFECYCLE_WEBHOOK_SECRET must not contain whitespace or control "
                "characters in production"
            )
        if lifecycle_webhook_previous_secret is not None:
            if len(lifecycle_webhook_previous_secret) < MIN_PRODUCTION_WEBHOOK_SECRET_LENGTH:
                errors.append(
                    "JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET must be at least "
                    f"{MIN_PRODUCTION_WEBHOOK_SECRET_LENGTH} characters in production"
                )
            elif (
                lifecycle_webhook_policy.lifecycle_webhook_credential_byte_length(
                    lifecycle_webhook_previous_secret
                )
                > MAX_PRODUCTION_LIFECYCLE_WEBHOOK_SECRET_BYTES
            ):
                errors.append(
                    "JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET must be at most "
                    f"{MAX_PRODUCTION_LIFECYCLE_WEBHOOK_SECRET_BYTES} bytes in production"
                )
            elif has_whitespace_or_control_character(lifecycle_webhook_previous_secret):
                errors.append(
                    "JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET must not contain whitespace "
                    "or control characters in production"
                )
            elif lifecycle_webhook_previous_secret == lifecycle_webhook_secret:
                errors.append(
                    "JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET must differ from "
                    "JEDI_LIFECYCLE_WEBHOOK_SECRET in production"
                )
        if (
            lifecycle_webhook_max_skew_seconds > MAX_PRODUCTION_LIFECYCLE_WEBHOOK_SKEW_SECONDS
        ):
            errors.append(
                "JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS must be at most "
                f"{MAX_PRODUCTION_LIFECYCLE_WEBHOOK_SKEW_SECONDS} in production"
            )
    if (
        admin_api_token is not None
        and len(admin_api_token) < MIN_PRODUCTION_ADMIN_API_TOKEN_LENGTH
    ):
        errors.append(
            "JEDI_ADMIN_API_TOKEN must be at least "
            f"{MIN_PRODUCTION_ADMIN_API_TOKEN_LENGTH} characters in production when configured"
        )
    if (
        admin_api_token is not None
        and admin_token_policy.admin_bearer_token_byte_length(admin_api_token)
        > MAX_PRODUCTION_ADMIN_API_TOKEN_BYTES
    ):
        errors.append(
            "JEDI_ADMIN_API_TOKEN must be at most "
            f"{MAX_PRODUCTION_ADMIN_API_TOKEN_BYTES} bytes in production when configured"
        )
    if (
        admin_api_token is not None
        and admin_token_policy.has_non_ascii_admin_bearer_token_character(
            admin_api_token
        )
    ):
        errors.append(
            "JEDI_ADMIN_API_TOKEN must contain only ASCII characters "
            "in production when configured"
        )
    if admin_api_token is not None and has_whitespace_or_control_character(
        admin_api_token
    ):
        errors.append(
            "JEDI_ADMIN_API_TOKEN must not contain whitespace or control characters "
            "in production when configured"
        )
    errors.extend(_database_url_errors(settings))
    errors.extend(_servicenow_instance_url_errors(settings))
    errors.extend(_servicenow_oauth_credential_errors(settings))
    errors.extend(
        _unpadded_control_free_value_errors(
            values_by_name={"JEDI_WORKER_ID": worker_id},
            detail="in production",
        )
    )
    errors.extend(_audit_root_errors(settings))
    if not classifier_gate:
        errors.append("JEDI_CLASSIFIER_GATE=false is development-only")
    if runtime_role in {"combined", "api"} and not strict_transport_security_enabled:
        errors.append(
            "JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=true is required for public "
            "production runtime roles"
        )
    if (
        runtime_role in {"combined", "api"}
        and strict_transport_security_enabled
        and strict_transport_security_max_age_seconds < MIN_PRODUCTION_HSTS_MAX_AGE_SECONDS
    ):
        errors.append(
            "JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS must be at least "
            f"{MIN_PRODUCTION_HSTS_MAX_AGE_SECONDS} for public production runtime roles"
        )
    if runtime_role in {"combined", "api"}:
        if admin_console_username is not None:
            errors.append("JEDI_ADMIN_CONSOLE_USERNAME is development-only in production")
        if admin_console_password is not None:
            errors.append("JEDI_ADMIN_CONSOLE_PASSWORD is development-only in production")
    if build_claim_apply:
        errors.extend(_build_claim_state_errors(settings))

    _append_positive_int_errors(
        errors,
        {
            "JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS": (
                lifecycle_webhook_max_skew_seconds
            ),
            "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES": lifecycle_webhook_max_body_bytes,
            "JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS": lifecycle_rate_limit_max_requests,
            "JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS": (
                lifecycle_rate_limit_window_seconds
            ),
            "JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS": lifecycle_rate_limit_max_buckets,
            "JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS": admin_rate_limit_max_requests,
            "JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS": admin_rate_limit_window_seconds,
            "JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS": admin_rate_limit_max_buckets,
            "JEDI_ADMIN_MAX_BODY_BYTES": admin_max_body_bytes,
            "JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS": (
                strict_transport_security_max_age_seconds
            ),
            "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS": running_job_stale_after_seconds,
            "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES": alert_webhook_max_body_bytes,
            "JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES": public_web_max_response_bytes,
            "JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS": public_web_max_excerpt_chars,
            "JEDI_PUBLIC_WEB_MAX_RESULTS": public_web_max_results,
        },
    )
    if public_web_timeout_seconds <= 0:
        errors.append("JEDI_PUBLIC_WEB_TIMEOUT_SECONDS must be greater than 0")
    if alert_webhook_timeout_seconds <= 0:
        errors.append("JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS must be greater than 0")
    _append_named_max_float_errors(
        errors,
        {
            "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS": (
                alert_webhook_timeout_seconds,
                MAX_PRODUCTION_OUTBOUND_TIMEOUT_SECONDS,
            ),
            "JEDI_PUBLIC_WEB_TIMEOUT_SECONDS": (
                public_web_timeout_seconds,
                MAX_PRODUCTION_OUTBOUND_TIMEOUT_SECONDS,
            ),
        },
    )
    _append_max_int_errors(
        errors,
        {
            "JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS": lifecycle_rate_limit_max_requests,
            "JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS": admin_rate_limit_max_requests,
        },
        maximum=MAX_CONFIGURABLE_RATE_LIMIT_REQUESTS,
    )
    _append_max_int_errors(
        errors,
        {
            "JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS": (
                lifecycle_rate_limit_window_seconds
            ),
            "JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS": admin_rate_limit_window_seconds,
        },
        maximum=MAX_CONFIGURABLE_RATE_LIMIT_WINDOW_SECONDS,
    )
    _append_max_int_errors(
        errors,
        {
            "JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS": lifecycle_rate_limit_max_buckets,
            "JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS": admin_rate_limit_max_buckets,
        },
        maximum=MAX_CONFIGURABLE_RATE_LIMIT_BUCKETS,
    )
    _append_named_max_int_errors(
        errors,
        {
            "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES": (
                lifecycle_webhook_max_body_bytes,
                MAX_PRODUCTION_LIFECYCLE_WEBHOOK_BODY_BYTES,
            ),
            "JEDI_ADMIN_MAX_BODY_BYTES": (
                admin_max_body_bytes,
                MAX_PRODUCTION_ADMIN_BODY_BYTES,
            ),
            "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES": (
                alert_webhook_max_body_bytes,
                MAX_PRODUCTION_ALERT_WEBHOOK_BODY_BYTES,
            ),
            "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS": (
                running_job_stale_after_seconds,
                MAX_PRODUCTION_RUNNING_JOB_STALE_AFTER_SECONDS,
            ),
        },
    )
    _append_named_max_int_errors(
        errors,
        {
            "JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES": (
                public_web_max_response_bytes,
                MAX_PRODUCTION_PUBLIC_WEB_RESPONSE_BYTES,
            ),
            "JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS": (
                public_web_max_excerpt_chars,
                MAX_PRODUCTION_PUBLIC_WEB_EXCERPT_CHARS,
            ),
            "JEDI_PUBLIC_WEB_MAX_RESULTS": (
                public_web_max_results,
                MAX_PRODUCTION_PUBLIC_WEB_RESULTS,
            ),
        },
    )

    if require_admin_auth and runtime_role in {"combined", "api"}:
        if has_whitespace_or_control_character(admin_auth_mode):
            errors.append("JEDI_ADMIN_AUTH_MODE must not contain whitespace or control characters")
        elif admin_auth_mode not in ADMIN_AUTH_MODES:
            errors.append(
                f"JEDI_ADMIN_AUTH_MODE must be one of: {', '.join(sorted(ADMIN_AUTH_MODES))}"
            )
        elif admin_auth_mode == "disabled":
            if admin_api_token is None:
                errors.append(
                    "JEDI_ADMIN_API_TOKEN is required when JEDI_ADMIN_AUTH_MODE=disabled "
                    "in production"
                )
        elif admin_auth_mode == "dev_basic":
            errors.append("JEDI_ADMIN_AUTH_MODE=dev_basic is development-only")
        elif admin_auth_mode in {"oidc", "servicenow_oauth"}:
            errors.append(f"JEDI_ADMIN_AUTH_MODE={admin_auth_mode} is not implemented")

    if runtime_role in {"combined", "worker"}:
        if model_provider is None:
            errors.append("JEDI_MODEL_PROVIDER is required in production")
        elif len(model_provider) > MAX_MODEL_PROVIDER_CHARS:
            errors.append(f"JEDI_MODEL_PROVIDER must be <= {MAX_MODEL_PROVIDER_CHARS} characters")
        elif has_whitespace_or_control_character(model_provider):
            errors.append(JEDI_MODEL_PROVIDER_CONTROL_ERROR)
        elif model_provider != "openai":
            errors.append(JEDI_MODEL_PROVIDER_UNSUPPORTED_ERROR)
        elif not openai_api_key or not openai_model:
            if not openai_api_key:
                errors.append("OPENAI_API_KEY is required when JEDI_MODEL_PROVIDER=openai")
            if not openai_model:
                errors.append("OPENAI_MODEL is required when JEDI_MODEL_PROVIDER=openai")
        elif has_whitespace_or_control_character(openai_api_key):
            errors.append(
                "OPENAI_API_KEY must not contain whitespace or control characters "
                "when JEDI_MODEL_PROVIDER=openai in production"
            )
        elif has_whitespace_or_control_character(openai_model):
            errors.append(
                "OPENAI_MODEL must not contain whitespace or control characters "
                "when JEDI_MODEL_PROVIDER=openai in production"
            )

    if public_web_access == "worker" and not public_web_allowed_domains:
        errors.append(
            "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS is required when public web access is enabled"
        )
    if public_web_access == "worker" and not public_web_doc_urls:
        errors.append("JEDI_PUBLIC_WEB_DOC_URLS is required when public web access is enabled")
    if public_web_access == "worker":
        invalid_allowed_domains = _invalid_public_web_allowed_domains(
            public_web_allowed_domains
        )
        if invalid_allowed_domains:
            errors.append(
                "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS must contain non-local hostnames without "
                "padding, whitespace, or control characters"
            )
        invalid_doc_urls = _public_web_doc_urls_outside_allowlist(
            allowed_domains=public_web_allowed_domains,
            doc_urls=public_web_doc_urls,
        )
        if invalid_doc_urls:
            errors.append(
                "JEDI_PUBLIC_WEB_DOC_URLS must use HTTPS URLs whose hosts match "
                "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS and must not contain credentials, fragments, "
                "whitespace, control characters, encoded whitespace/control characters, or "
                "sensitive query parameters"
            )

    if update_set_apply:
        if not update_set_user_name:
            errors.append("JEDI_UPDATE_SET_USER_NAME is required when JEDI_UPDATE_SET_APPLY=true")
        elif has_whitespace_or_control_character(update_set_user_name):
            errors.append(
                "JEDI_UPDATE_SET_USER_NAME must not contain whitespace or control characters "
                "when JEDI_UPDATE_SET_APPLY=true in production"
            )

    if alert_webhook_enabled:
        if not alert_webhook_url:
            errors.append("JEDI_ALERT_WEBHOOK_URL is required when alert webhook is enabled")
        else:
            errors.extend(
                validate_alert_webhook_url(
                    alert_webhook_url,
                    subject="JEDI_ALERT_WEBHOOK_URL",
                )
            )

    if errors:
        raise RuntimeConfigError("; ".join(errors))


def _runtime_environment(settings: RuntimeSettings) -> str:
    value = _runtime_setting_text(settings.runtime_environment, name="JEDI_ENVIRONMENT")
    if value != value.strip() or has_whitespace_or_control_character(value):
        raise RuntimeConfigError(
            "JEDI_ENVIRONMENT must not contain whitespace or control characters"
        )
    return value.lower()


def _runtime_role(settings: RuntimeSettings) -> str:
    value = _runtime_setting_text(settings.runtime_role, name="JEDI_RUNTIME_ROLE")
    if value != value.strip() or has_whitespace_or_control_character(value):
        raise RuntimeConfigError(
            "JEDI_RUNTIME_ROLE must not contain whitespace or control characters"
        )
    if value not in {"combined", "api", "worker"}:
        raise RuntimeConfigError("JEDI_RUNTIME_ROLE must be one of: api, combined, worker")
    return value


def _api_runtime_role_errors(
    *,
    model_provider: str | None,
    openai_api_key: str | None,
    openai_model: str | None,
    public_web_access: str,
    build_claim_apply: bool,
    update_set_apply: bool,
) -> list[str]:
    errors: list[str] = []
    if model_provider is not None:
        errors.append("JEDI_MODEL_PROVIDER is worker-only when JEDI_RUNTIME_ROLE=api")
    if openai_api_key is not None:
        errors.append("OPENAI_API_KEY is worker-only when JEDI_RUNTIME_ROLE=api")
    if openai_model is not None:
        errors.append("OPENAI_MODEL is worker-only when JEDI_RUNTIME_ROLE=api")
    if public_web_access == "worker":
        errors.append("JEDI_PUBLIC_WEB_ACCESS=worker is worker-only when JEDI_RUNTIME_ROLE=api")
    if build_claim_apply:
        errors.append("JEDI_BUILD_CLAIM_APPLY=true is worker-only when JEDI_RUNTIME_ROLE=api")
    if update_set_apply:
        errors.append("JEDI_UPDATE_SET_APPLY=true is worker-only when JEDI_RUNTIME_ROLE=api")
    return errors


def _worker_runtime_role_errors(
    *,
    lifecycle_webhook_auth_mode: str,
    lifecycle_webhook_secret: str | None,
    lifecycle_webhook_previous_secret: str | None,
    trusted_hosts: list[str],
    admin_api_token: str | None,
    admin_auth_mode: str,
    admin_console_username: str | None,
    admin_console_password: str | None,
) -> list[str]:
    errors: list[str] = []
    if lifecycle_webhook_auth_mode != "disabled":
        errors.append(
            "JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE is api-only when JEDI_RUNTIME_ROLE=worker"
        )
    if lifecycle_webhook_secret is not None:
        errors.append("JEDI_LIFECYCLE_WEBHOOK_SECRET is api-only when JEDI_RUNTIME_ROLE=worker")
    if lifecycle_webhook_previous_secret is not None:
        errors.append(
            "JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET is api-only "
            "when JEDI_RUNTIME_ROLE=worker"
        )
    if trusted_hosts:
        errors.append("JEDI_TRUSTED_HOSTS is api-only when JEDI_RUNTIME_ROLE=worker")
    if admin_api_token is not None:
        errors.append("JEDI_ADMIN_API_TOKEN is api-only when JEDI_RUNTIME_ROLE=worker")
    if admin_auth_mode != "disabled":
        errors.append("JEDI_ADMIN_AUTH_MODE is api-only when JEDI_RUNTIME_ROLE=worker")
    if admin_console_username is not None:
        errors.append("JEDI_ADMIN_CONSOLE_USERNAME is api-only when JEDI_RUNTIME_ROLE=worker")
    if admin_console_password is not None:
        errors.append("JEDI_ADMIN_CONSOLE_PASSWORD is api-only when JEDI_RUNTIME_ROLE=worker")
    return errors


def _public_web_worker_settings_errors(settings: RuntimeSettings) -> list[str]:
    errors: list[str] = []
    if settings.public_web_allowed_domains and _invalid_public_web_allowed_domains(
        settings.public_web_allowed_domains
    ):
        errors.append(
            "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS must contain non-local hostnames without "
            "padding, whitespace, or control characters"
        )
    if settings.public_web_doc_urls and _public_web_doc_urls_outside_allowlist(
        allowed_domains=settings.public_web_allowed_domains,
        doc_urls=settings.public_web_doc_urls,
    ):
        errors.append(
            "JEDI_PUBLIC_WEB_DOC_URLS must use HTTPS URLs whose hosts match "
            "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS and must not contain credentials, fragments, "
            "whitespace, control characters, or sensitive query parameters"
        )
    if settings.public_web_access != "worker":
        return errors
    if not settings.public_web_allowed_domains:
        errors.append(
            "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS is required when public web access is enabled"
        )
    if not settings.public_web_doc_urls:
        errors.append("JEDI_PUBLIC_WEB_DOC_URLS is required when public web access is enabled")
    if settings.public_web_timeout_seconds <= 0:
        errors.append("JEDI_PUBLIC_WEB_TIMEOUT_SECONDS must be greater than 0")
    _append_positive_int_errors(
        errors,
        {
            "JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES": settings.public_web_max_response_bytes,
            "JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS": settings.public_web_max_excerpt_chars,
            "JEDI_PUBLIC_WEB_MAX_RESULTS": settings.public_web_max_results,
        },
    )
    return errors


def _audit_root_errors(settings: RuntimeSettings) -> list[str]:
    audit_root = _runtime_setting_path(settings.audit_root, name="JEDI_AUDIT_ROOT")
    return _audit_root_value_errors(audit_root, detail="in production")


def _audit_root_value_errors(audit_root: Path, *, detail: str) -> list[str]:
    audit_root_text = str(audit_root)
    if (
        not audit_root_text
        or has_whitespace_or_control_character(audit_root_text)
        or not audit_root.is_absolute()
    ):
        return [
            (
                "JEDI_AUDIT_ROOT must be an absolute path without whitespace or control "
                f"characters {detail}"
            ).strip()
        ]
    return []


def _unpadded_control_free_value_errors(
    *,
    values_by_name: dict[str, str],
    detail: str,
) -> list[str]:
    errors: list[str] = []
    for name, value in values_by_name.items():
        if (
            not value
            or value != value.strip()
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            errors.append(
                f"{name} must not be empty, padded, or contain control characters {detail}"
            )
    return errors


def _build_claim_state_errors(settings: RuntimeSettings) -> list[str]:
    build_claim_from_state = _runtime_setting_text(
        settings.build_claim_from_state,
        name="JEDI_BUILD_CLAIM_FROM_STATE",
    )
    build_claim_state = _runtime_setting_text(
        settings.build_claim_state,
        name="JEDI_BUILD_CLAIM_STATE",
    )
    return _unpadded_control_free_value_errors(
        values_by_name={
            "JEDI_BUILD_CLAIM_FROM_STATE": build_claim_from_state,
            "JEDI_BUILD_CLAIM_STATE": build_claim_state,
        },
        detail="when JEDI_BUILD_CLAIM_APPLY=true in production",
    )


def _database_url_errors(settings: RuntimeSettings) -> list[str]:
    database_url = _runtime_setting_text(settings.database_url, name="DATABASE_URL")
    return _database_url_value_errors(database_url, detail="in production")


def _database_url_value_errors(database_url: str, *, detail: str) -> list[str]:
    parsed = urlparse(database_url)
    if (
        has_whitespace_or_control_character(database_url)
        or has_encoded_whitespace_or_control_character(database_url)
        or parsed.scheme.lower() not in {"postgresql", "postgres"}
        or bool(parsed.fragment)
        or not parsed.hostname
    ):
        return [
            (
                "DATABASE_URL must be a PostgreSQL URL without whitespace or control "
                "characters, encoded whitespace/control characters, or URL fragments "
                f"{detail}"
            ).strip()
        ]
    return []


def _servicenow_instance_url_errors(settings: RuntimeSettings) -> list[str]:
    return _servicenow_instance_url_value_errors(
        values_by_name={
            "SERVICENOW_INSTANCE_URL": _runtime_setting_text(
                settings.servicenow_instance_url,
                name="SERVICENOW_INSTANCE_URL",
            ),
            "SERVICENOW_PM_INSTANCE_URL": _runtime_setting_text(
                settings.servicenow_pm_instance_url,
                name="SERVICENOW_PM_INSTANCE_URL",
            ),
            "SERVICENOW_DEV_INSTANCE_URL": _runtime_setting_text(
                settings.servicenow_dev_instance_url,
                name="SERVICENOW_DEV_INSTANCE_URL",
            ),
        },
        detail="in production",
    )


def _servicenow_instance_url_value_errors(
    *,
    values_by_name: dict[str, str],
    detail: str,
) -> list[str]:
    errors: list[str] = []
    for name, value in values_by_name.items():
        if not value:
            continue
        parsed = urlparse(value)
        if (
            has_whitespace_or_control_character(value)
            or has_encoded_whitespace_or_control_character(value)
            or parsed.scheme.lower() != "https"
            or parsed.username
            or parsed.password
            or parsed.fragment
            or not parsed.hostname
        ):
            errors.append(
                f"{name} must be an HTTPS ServiceNow instance URL without "
                f"credentials, fragments, whitespace, or control characters {detail}"
            )
    return errors


def _servicenow_oauth_credential_errors(settings: RuntimeSettings) -> list[str]:
    return _servicenow_oauth_value_errors(
        values_by_name={
            "SERVICENOW_CLIENT_ID": _runtime_setting_text(
                settings.servicenow_client_id,
                name="SERVICENOW_CLIENT_ID",
            ),
            "SERVICENOW_CLIENT_SECRET": _runtime_setting_text(
                settings.servicenow_client_secret,
                name="SERVICENOW_CLIENT_SECRET",
            ),
            "SERVICENOW_PM_CLIENT_ID": _runtime_setting_text(
                settings.servicenow_pm_client_id,
                name="SERVICENOW_PM_CLIENT_ID",
            ),
            "SERVICENOW_PM_CLIENT_SECRET": _runtime_setting_text(
                settings.servicenow_pm_client_secret,
                name="SERVICENOW_PM_CLIENT_SECRET",
            ),
            "SERVICENOW_DEV_CLIENT_ID": _runtime_setting_text(
                settings.servicenow_dev_client_id,
                name="SERVICENOW_DEV_CLIENT_ID",
            ),
            "SERVICENOW_DEV_CLIENT_SECRET": _runtime_setting_text(
                settings.servicenow_dev_client_secret,
                name="SERVICENOW_DEV_CLIENT_SECRET",
            ),
        },
        detail="in production",
    )


def _servicenow_oauth_value_errors(
    *,
    values_by_name: dict[str, str],
    detail: str,
) -> list[str]:
    errors: list[str] = []
    for name, value in values_by_name.items():
        if not value:
            continue
        if value != value.strip() or has_whitespace_or_control_character(value):
            errors.append(
                f"{name} must not be empty, padded, or contain control characters {detail}"
            )
    return errors


def _append_positive_int_errors(errors: list[str], values_by_name: dict[str, int]) -> None:
    for name, value in values_by_name.items():
        if value <= 0:
            errors.append(f"{name} must be greater than 0")


def _append_max_int_errors(
    errors: list[str],
    values_by_name: dict[str, int],
    *,
    maximum: int,
) -> None:
    for name, value in values_by_name.items():
        if value > maximum:
            errors.append(f"{name} must be at most {maximum}")


def _append_named_max_int_errors(
    errors: list[str],
    values_by_name: dict[str, tuple[int, int]],
) -> None:
    for name, (value, maximum) in values_by_name.items():
        if value > maximum:
            errors.append(f"{name} must be at most {maximum}")


def _append_named_max_float_errors(
    errors: list[str],
    values_by_name: dict[str, tuple[float, float]],
) -> None:
    for name, (value, maximum) in values_by_name.items():
        if value > maximum:
            errors.append(f"{name} must be at most {maximum:g}")


def _invalid_public_web_allowed_domains(allowed_domains: list[str]) -> list[str]:
    invalid: list[str] = []
    for domain in allowed_domains:
        normalized = _normalize_host(domain)
        if (
            not domain
            or domain != domain.strip()
            or has_whitespace_or_control_character(domain)
            or has_encoded_whitespace_or_control_character(domain)
            or not normalized
            or is_non_public_hostname(normalized)
        ):
            invalid.append(domain)
    return invalid


def _invalid_trusted_hosts(trusted_hosts: list[str]) -> list[str]:
    invalid: list[str] = []
    for trusted_host in trusted_hosts:
        normalized = _trusted_host_hostname(trusted_host)
        if (
            not trusted_host
            or trusted_host == "*"
            or trusted_host != trusted_host.strip()
            or has_whitespace_or_control_character(trusted_host)
            or has_encoded_whitespace_or_control_character(trusted_host)
            or not normalized
            or is_non_public_hostname(normalized)
            or _trusted_host_has_unsafe_delimiter(trusted_host)
        ):
            invalid.append(trusted_host)
    return invalid


def _trusted_host_hostname(trusted_host: str) -> str:
    candidate = trusted_host[2:] if trusted_host.startswith("*.") else trusted_host
    if candidate.startswith("."):
        return ""
    host, separator, port = candidate.partition(":")
    if separator and (not port.isdigit() or int(port) < 1 or int(port) > 65535):
        return ""
    return _normalize_host(host)


def _trusted_host_has_unsafe_delimiter(trusted_host: str) -> bool:
    return any(character in trusted_host for character in ("/", "\\", "@", "#", "?"))


def _public_web_doc_urls_outside_allowlist(
    *,
    allowed_domains: list[str],
    doc_urls: list[str],
) -> list[str]:
    allowed = {_normalize_host(domain) for domain in allowed_domains}
    invalid: list[str] = []
    for doc_url in doc_urls:
        parsed = urlparse(doc_url)
        host = _normalize_host(parsed.hostname or "")
        if (
            has_whitespace_or_control_character(doc_url)
            or has_encoded_whitespace_or_control_character(doc_url)
            or parsed.fragment
            or sensitive_query_keys(parsed.query)
            or parsed.scheme.lower() != "https"
            or parsed.username
            or parsed.password
            or not host
            or is_non_public_hostname(host)
            or host not in allowed
        ):
            invalid.append(doc_url)
    return invalid


def _normalize_host(value: str) -> str:
    return normalize_hostname(value)


def _runtime_setting_text(value: object, *, name: str) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    raise RuntimeConfigError(f"{name} must be a string runtime setting")


def _runtime_setting_text_list(value: object, *, name: str) -> list[str]:
    if type(value) is not list:
        raise RuntimeConfigError(f"{name} must be a string list setting")
    values: list[str] = []
    for item in value:
        if type(item) is not str:
            raise RuntimeConfigError(f"{name} must be a string list setting")
        values.append(item)
    return values


def _runtime_setting_int(value: object, *, name: str) -> int:
    if type(value) is int:
        return value
    raise RuntimeConfigError(f"{name} must be an integer runtime setting")


def _runtime_setting_float(value: object, *, name: str) -> float:
    if type(value) is int:
        return float(value)
    if type(value) is float and isfinite(value):
        return value
    raise RuntimeConfigError(f"{name} must be a finite number runtime setting")


def _runtime_setting_bool(value: object, *, name: str) -> bool:
    if type(value) is bool:
        return value
    raise RuntimeConfigError(f"{name} must be a boolean runtime setting")


def _runtime_setting_path(value: object, *, name: str) -> Path:
    if type(value) is RUNTIME_PATH_SETTING_TYPE:
        return value
    raise RuntimeConfigError(f"{name} must be a path runtime setting")


def _direct_optional_runtime_setting_text(value: object, *, name: str) -> str | None:
    if value is None:
        return None
    return _runtime_setting_text(value, name=name)


def _bool_value(value: str | None, *, name: str, default: bool = False) -> bool:
    raw = _runtime_setting_text(value, name=name)
    if raw == "":
        return default
    if raw != raw.strip() or has_whitespace_or_control_character(raw):
        raise RuntimeConfigError(
            f"{name} must be a boolean value without padding or control characters"
        )
    text = raw.lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise RuntimeConfigError(f"{name} must be a boolean value: true/false, 1/0, yes/no, or on/off")


def _enum_value(
    value: str | None,
    *,
    name: str,
    allowed: set[str],
    default: str,
) -> str:
    raw = _runtime_setting_text(value, name=name)
    if raw.strip() == "":
        return default
    if raw != raw.strip() or has_whitespace_or_control_character(raw):
        raise RuntimeConfigError(f"{name} must not contain whitespace or control characters")
    if raw in allowed:
        return raw
    allowed_values = ", ".join(sorted(allowed))
    raise RuntimeConfigError(f"{name} must be one of: {allowed_values}")


def _runtime_environment_value(value: str | None) -> str:
    raw = _runtime_setting_text(value, name="JEDI_ENVIRONMENT")
    if raw.strip() == "":
        return "development"
    if raw != raw.strip() or has_whitespace_or_control_character(raw):
        raise RuntimeConfigError(
            "JEDI_ENVIRONMENT must not contain whitespace or control characters"
        )
    text = raw.lower()
    if text in {"development", "production"}:
        return text
    raise RuntimeConfigError("JEDI_ENVIRONMENT must be one of: development, production")


def _int_value(value: str | None, *, name: str, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = parse_optional_base10_int(value, name=name)
    except ValueError as exc:
        raise RuntimeConfigError(
            exception_diagnostic_message(exc, fallback_subject="runtime config")
        ) from None
    if parsed is None:
        return default
    return parsed


def _float_value(value: str | None, *, name: str, default: float) -> float:
    if value is None or value == "":
        return default
    try:
        parsed = parse_optional_ascii_decimal_float(value, name=name)
    except ValueError as exc:
        raise RuntimeConfigError(
            exception_diagnostic_message(exc, fallback_subject="runtime config")
        ) from None
    if parsed is None:
        return default
    return parsed


def _csv_values(value: str | None, *, name: str) -> list[str]:
    raw = _runtime_setting_text(value, name=name)
    if raw == "":
        return []
    items = raw.split(",")
    if any(item.strip() == "" for item in items):
        raise RuntimeConfigError(f"{name} must not contain empty CSV items")
    return items


def _optional_str(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    return value.strip()


def _optional_alert_webhook_url(value: str | None) -> str | None:
    raw = _runtime_setting_text(value, name="JEDI_ALERT_WEBHOOK_URL")
    if raw == "":
        return None
    errors = _unpadded_control_free_value_errors(
        values_by_name={"JEDI_ALERT_WEBHOOK_URL": raw},
        detail="",
    )
    if errors:
        raise RuntimeConfigError(errors[0])
    url_errors = validate_alert_webhook_url(raw, subject="JEDI_ALERT_WEBHOOK_URL")
    if url_errors:
        raise RuntimeConfigError("; ".join(url_errors))
    return raw


def _optional_model_provider(value: str | None) -> str | None:
    raw = _runtime_setting_text(value, name="JEDI_MODEL_PROVIDER")
    if raw.strip() == "":
        return None
    if len(raw) > MAX_MODEL_PROVIDER_CHARS:
        raise RuntimeConfigError(
            f"JEDI_MODEL_PROVIDER must be <= {MAX_MODEL_PROVIDER_CHARS} characters"
        )
    if has_whitespace_or_control_character(raw):
        raise RuntimeConfigError(JEDI_MODEL_PROVIDER_CONTROL_ERROR)
    return raw


def _optional_unpadded_control_free_str(
    value: str | None,
    *,
    name: str,
    default: str,
) -> str:
    raw = _runtime_setting_text(value, name=name)
    if raw == "":
        return default
    errors = _unpadded_control_free_value_errors(
        values_by_name={name: raw},
        detail="",
    )
    if errors:
        raise RuntimeConfigError(errors[0])
    return raw


def _optional_unpadded_control_free_setting(value: str | None, *, name: str) -> str | None:
    raw = _runtime_setting_text(value, name=name)
    if raw == "":
        return None
    errors = _unpadded_control_free_value_errors(
        values_by_name={name: raw},
        detail="",
    )
    if errors:
        raise RuntimeConfigError(errors[0])
    return raw


def _optional_admin_console_credential(value: str | None, *, name: str) -> str | None:
    raw = _runtime_setting_text(value, name=name)
    if raw == "":
        return None
    errors = _unpadded_control_free_value_errors(
        values_by_name={name: raw},
        detail="",
    )
    if errors:
        raise RuntimeConfigError(errors[0])
    if (
        admin_basic_auth_policy.basic_auth_credential_byte_length(raw)
        > MAX_ADMIN_CONSOLE_CREDENTIAL_BYTES
    ):
        raise RuntimeConfigError(
            f"{name} must be at most {MAX_ADMIN_CONSOLE_CREDENTIAL_BYTES} bytes"
        )
    return raw


def _optional_openai_provider_value(value: str | None, *, name: str) -> str | None:
    raw = _runtime_setting_text(value, name=name)
    if raw.strip() == "":
        return None
    if raw != raw.strip():
        raise RuntimeConfigError(f"{name} must not contain leading or trailing whitespace")
    try:
        if name == "OPENAI_API_KEY":
            return validate_provider_api_key(raw)
        if name == "OPENAI_MODEL":
            return validate_provider_model(raw)
    except ValueError as exc:
        diagnostic = exception_diagnostic_message(
            exc,
            fallback_subject=f"{name} provider setting",
        )
        raise RuntimeConfigError(diagnostic) from None
    raise RuntimeConfigError(f"Unsupported OpenAI provider setting: {name}")
