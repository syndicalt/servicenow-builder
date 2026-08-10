from __future__ import annotations

from jedi_devproject.alert_webhook_url import validate_alert_webhook_url


def test_validate_alert_webhook_url_accepts_https_url_without_credentials() -> None:
    assert validate_alert_webhook_url("https://alerts.example.gov/jedi") == ()


def test_validate_alert_webhook_url_rejects_non_https_url() -> None:
    assert validate_alert_webhook_url("http://alerts.example.gov/jedi") == (
        "alert webhook URL must use HTTPS",
    )


def test_validate_alert_webhook_url_rejects_embedded_credentials() -> None:
    assert validate_alert_webhook_url(
        "https://alert-user:alert-secret@alerts.example.gov/jedi"
    ) == ("alert webhook URL must not include credentials",)


def test_validate_alert_webhook_url_rejects_localhost_targets() -> None:
    assert validate_alert_webhook_url("https://localhost/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_unicode_dot_localhost_targets() -> None:
    assert validate_alert_webhook_url("https://localhost。/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_localhost_subdomain_targets() -> None:
    assert validate_alert_webhook_url("https://alerts.localhost/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_loopback_ip_targets() -> None:
    assert validate_alert_webhook_url("https://127.0.0.1/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_unicode_dot_loopback_ip_targets() -> None:
    assert validate_alert_webhook_url("https://127。0。0。1/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_ipv6_loopback_targets() -> None:
    assert validate_alert_webhook_url("https://[::1]/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_unspecified_ipv4_targets() -> None:
    assert validate_alert_webhook_url("https://0.0.0.0/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_unspecified_ipv6_targets() -> None:
    assert validate_alert_webhook_url("https://[::]/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_link_local_metadata_targets() -> None:
    assert validate_alert_webhook_url("https://169.254.169.254/latest/meta-data") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_short_form_loopback_ipv4_targets() -> None:
    assert validate_alert_webhook_url("https://127.1/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_three_part_loopback_ipv4_targets() -> None:
    assert validate_alert_webhook_url("https://127.0.1/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_integer_loopback_ipv4_targets() -> None:
    assert validate_alert_webhook_url("https://2130706433/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_octal_loopback_ipv4_targets() -> None:
    assert validate_alert_webhook_url("https://0177.0.0.1/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_hex_loopback_ipv4_targets() -> None:
    assert validate_alert_webhook_url("https://0x7f000001/jedi") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_rejects_integer_link_local_ipv4_targets() -> None:
    assert validate_alert_webhook_url("https://2852039166/latest/meta-data") == (
        "alert webhook URL must not target local or link-local addresses",
    )


def test_validate_alert_webhook_url_accepts_public_legacy_numeric_ipv4_targets() -> None:
    assert validate_alert_webhook_url("https://134744072/jedi") == ()


def test_validate_alert_webhook_url_ignores_out_of_range_legacy_ipv4_components() -> None:
    assert validate_alert_webhook_url("https://4294967296/jedi") == ()
    assert validate_alert_webhook_url("https://256.1/jedi") == ()
    assert validate_alert_webhook_url("https://1.256.1/jedi") == ()
    assert validate_alert_webhook_url("https://1.1.1.256/jedi") == ()


def test_validate_alert_webhook_url_ignores_invalid_legacy_ipv4_components() -> None:
    assert validate_alert_webhook_url("https://127..1/jedi") == ()
    assert validate_alert_webhook_url("https://0xzzzz/jedi") == ()
    assert validate_alert_webhook_url("https://09.0.0.1/jedi") == ()


def test_validate_alert_webhook_url_rejects_sensitive_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?token=secret&team=platform"
    ) == ("alert webhook URL must not include sensitive query parameters: token",)


def test_validate_alert_webhook_url_rejects_semicolon_sensitive_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?team=platform;token=secret"
    ) == ("alert webhook URL must not include sensitive query parameters: token",)


def test_validate_alert_webhook_url_rejects_semicolon_client_secret_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?team=platform;client_secret=secret"
    ) == ("alert webhook URL must not include sensitive query parameters: client_secret",)


def test_validate_alert_webhook_url_rejects_encoded_ampersand_sensitive_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?team=platform%26token=secret"
    ) == ("alert webhook URL must not include sensitive query parameters: token",)


def test_validate_alert_webhook_url_rejects_encoded_semicolon_sensitive_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?team=platform%3Bclient_secret=secret"
    ) == ("alert webhook URL must not include sensitive query parameters: client_secret",)


def test_validate_alert_webhook_url_rejects_double_encoded_ampersand_sensitive_query() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?team=platform%2526token=secret"
    ) == ("alert webhook URL must not include sensitive query parameters: token",)


def test_validate_alert_webhook_url_rejects_double_encoded_semicolon_sensitive_query() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?team=platform%253Bclient_secret=secret"
    ) == ("alert webhook URL must not include sensitive query parameters: client_secret",)


def test_validate_alert_webhook_url_accepts_benign_encoded_query_separators() -> None:
    assert validate_alert_webhook_url("https://alerts.example.gov/jedi?note=fish%26chips") == ()
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?note=uses%3Bsemicolon"
    ) == ()


def test_validate_alert_webhook_url_accepts_benign_double_encoded_query_separators() -> None:
    assert validate_alert_webhook_url("https://alerts.example.gov/jedi?note=fish%2526chips") == ()
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?note=uses%253Bsemicolon"
    ) == ()


def test_validate_alert_webhook_url_rejects_hyphenated_sensitive_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?api-key=secret&team=platform"
    ) == ("alert webhook URL must not include sensitive query parameters: api-key",)


def test_validate_alert_webhook_url_rejects_x_prefixed_sensitive_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?x-api-key=secret&team=platform"
    ) == ("alert webhook URL must not include sensitive query parameters: x-api-key",)


def test_validate_alert_webhook_url_rejects_camel_case_sensitive_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?clientSecret=secret&team=platform"
    ) == ("alert webhook URL must not include sensitive query parameters: clientsecret",)


def test_validate_alert_webhook_url_rejects_cookie_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?cookie=session-secret&team=platform"
    ) == ("alert webhook URL must not include sensitive query parameters: cookie",)


def test_validate_alert_webhook_url_rejects_private_key_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?private_key=secret&team=platform"
    ) == ("alert webhook URL must not include sensitive query parameters: private_key",)


def test_validate_alert_webhook_url_rejects_cloud_credential_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?awsSecretAccessKey=secret&team=platform"
    ) == (
        "alert webhook URL must not include sensitive query parameters: "
        "awssecretaccesskey",
    )


def test_validate_alert_webhook_url_reports_multiple_sensitive_query_parameters() -> None:
    assert validate_alert_webhook_url(
        "https://alerts.example.gov/jedi?access_token=one&signature=two",
        subject="JEDI_ALERT_WEBHOOK_URL",
    ) == (
        "JEDI_ALERT_WEBHOOK_URL must not include sensitive query parameters: "
        "access_token, signature",
    )


def test_validate_alert_webhook_url_rejects_fragments() -> None:
    assert validate_alert_webhook_url("https://alerts.example.gov/jedi#ignored") == (
        "alert webhook URL must not include fragments",
    )


def test_validate_alert_webhook_url_rejects_control_characters() -> None:
    assert validate_alert_webhook_url("https://alerts.example.gov/jedi\nX-Injected: value") == (
        "alert webhook URL must not include whitespace or control characters",
    )


def test_validate_alert_webhook_url_rejects_raw_whitespace() -> None:
    assert validate_alert_webhook_url("https://alerts.example.gov/jedi path") == (
        "alert webhook URL must not include whitespace or control characters",
    )


def test_validate_alert_webhook_url_rejects_percent_encoded_control_characters() -> None:
    assert validate_alert_webhook_url("https://alerts.example.gov/jedi%0d%0aX-Injected") == (
        "alert webhook URL must not include encoded whitespace or control characters",
    )


def test_validate_alert_webhook_url_rejects_percent_encoded_whitespace() -> None:
    assert validate_alert_webhook_url("https://alerts.example.gov/jedi%20path") == (
        "alert webhook URL must not include encoded whitespace or control characters",
    )


def test_validate_alert_webhook_url_uses_caller_subject_in_error_messages() -> None:
    assert validate_alert_webhook_url(
        "https://alert-user:alert-secret@alerts.example.gov/jedi",
        subject="JEDI_ALERT_WEBHOOK_URL",
    ) == ("JEDI_ALERT_WEBHOOK_URL must not include credentials",)
