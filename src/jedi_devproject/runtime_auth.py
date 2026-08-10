"""Admin authentication and rate-limit guards for the runtime API.

Security-sensitive compliance controls: fail-closed admin token checks,
dev-only basic-auth console credentials, and admin rate limiting.
"""

from __future__ import annotations

import base64
import binascii
import secrets

from fastapi import HTTPException, status

from jedi_devproject import admin_basic_auth_policy, admin_token_policy
from jedi_devproject.rate_limit import InMemoryRateLimiter, is_valid_rate_limit_decision
from jedi_devproject.runtime_config import (
    RuntimeConfigError,
    RuntimeSettings,
    _direct_optional_runtime_setting_text,
    _runtime_setting_text,
)

MAX_BASIC_AUTH_ENCODED_BYTES = admin_basic_auth_policy.MAX_BASIC_AUTH_ENCODED_BYTES
MAX_ADMIN_BEARER_TOKEN_BYTES = admin_token_policy.MAX_ADMIN_BEARER_TOKEN_BYTES


def _has_malformed_admin_bearer_token(value: str) -> bool:
    return admin_token_policy.is_malformed_admin_bearer_token(value)


def _require_admin_token(
    *,
    settings: RuntimeSettings,
    authorization: str | None,
) -> None:
    admin_api_token = _admin_api_token_from_settings(settings)
    if not admin_api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin artifact API is not configured",
        )
    if _has_malformed_admin_bearer_token(admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin artifact API token is invalid",
        )
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin bearer token required",
        )
    token = authorization.removeprefix("Bearer ")
    if _has_malformed_admin_bearer_token(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin bearer token rejected",
        )
    if not secrets.compare_digest(token, admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin bearer token rejected",
        )


def _require_admin_rate_limit(
    *,
    admin_rate_limiter: InMemoryRateLimiter | None,
    key: str,
) -> None:
    if admin_rate_limiter is None:
        return
    decision = admin_rate_limiter.check(key)
    _validate_admin_rate_limit_decision(decision)
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="rate limit exceeded",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )


def _validate_admin_rate_limit_decision(decision: object) -> None:
    if not is_valid_rate_limit_decision(decision):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin rate limiter is invalid",
        )


def _require_admin_console_credentials(
    *,
    settings: RuntimeSettings,
    authorization: str | None,
) -> None:
    admin_auth_mode, runtime_environment, username_config, password_config = (
        _admin_console_settings_from_runtime(settings)
    )
    if admin_auth_mode == "disabled":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin console authentication is disabled",
        )
    if admin_auth_mode in {"oidc", "servicenow_oauth"}:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"admin auth mode is not implemented: {admin_auth_mode}",
        )
    if admin_auth_mode != "dev_basic":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin auth mode is not supported",
        )
    if runtime_environment != "development":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="dev_basic admin auth is development-only",
        )
    if not username_config or not password_config:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin console is not configured",
        )
    if _has_malformed_admin_console_credential_part(
        username_config
    ) or _has_malformed_admin_console_credential_part(password_config):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin console credentials are invalid",
        )
    credentials = _basic_auth_credentials(authorization)
    if credentials is None:
        raise _admin_console_unauthorized()
    username, password = credentials
    username_ok = secrets.compare_digest(username, username_config)
    password_ok = secrets.compare_digest(password, password_config)
    if not (username_ok and password_ok):
        raise _admin_console_unauthorized()


def _admin_api_token_from_settings(settings: RuntimeSettings) -> str | None:
    try:
        return _direct_optional_runtime_setting_text(
            settings.admin_api_token,
            name="JEDI_ADMIN_API_TOKEN",
        )
    except RuntimeConfigError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin artifact API token is invalid",
        ) from None


def _admin_console_settings_from_runtime(
    settings: RuntimeSettings,
) -> tuple[str, str, str | None, str | None]:
    try:
        return (
            _runtime_setting_text(
                settings.admin_auth_mode,
                name="JEDI_ADMIN_AUTH_MODE",
            ),
            _runtime_setting_text(
                settings.runtime_environment,
                name="JEDI_ENVIRONMENT",
            ),
            _direct_optional_runtime_setting_text(
                settings.admin_console_username,
                name="JEDI_ADMIN_CONSOLE_USERNAME",
            ),
            _direct_optional_runtime_setting_text(
                settings.admin_console_password,
                name="JEDI_ADMIN_CONSOLE_PASSWORD",
            ),
        )
    except RuntimeConfigError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin console configuration is invalid",
        ) from None


def _basic_auth_credentials(authorization: str | None) -> tuple[str, str] | None:
    if authorization is None or not authorization.startswith("Basic "):
        return None
    encoded = authorization.removeprefix("Basic ")
    if admin_basic_auth_policy.is_malformed_basic_auth_encoded_section(encoded):
        return None
    encoded_bytes = encoded.encode("ascii")
    try:
        decoded = base64.b64decode(encoded_bytes, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None
    username, separator, password = decoded.partition(":")
    if separator != ":":
        return None
    if _has_malformed_admin_console_credential_part(
        username
    ) or _has_malformed_admin_console_credential_part(password):
        return None
    return username, password


def _has_malformed_admin_console_credential_part(value: str) -> bool:
    return admin_basic_auth_policy.is_malformed_admin_console_credential_part(value)


def _admin_console_unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="admin console credentials required",
        headers={"WWW-Authenticate": 'Basic realm="jedi-admin"'},
    )
