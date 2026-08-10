from __future__ import annotations

import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from itertools import islice
from pathlib import Path
from types import TracebackType
from typing import Any, Protocol, cast

from pydantic import BaseModel, ConfigDict

from jedi_devproject.artifacts import (
    ArtifactReadError,
    open_regular_artifact_file,
    read_regular_artifact_bytes,
)
from jedi_devproject.diagnostic_redaction import _redact_diagnostic_text
from jedi_devproject.models import DataClassification, Story
from jedi_devproject.sensitive_keys import is_sensitive_key
from jedi_devproject.url_query_safety import has_whitespace_or_control_character

MAX_HTTP_ERROR_DIAGNOSTIC_CHARS = 4096
HTTP_ERROR_TRUNCATION_MARKER = "...[truncated]"
MAX_HTTP_ERROR_DIAGNOSTIC_COLLECTION_ITEMS = 100
MAX_SERVICENOW_DIAGNOSTIC_COLLECTION_ITEMS = 100
MAX_SECRET_REDACTION_COLLECTION_ITEMS = 100
MAX_OAUTH_ACCESS_TOKEN_BYTES = 8192
MAX_HTTP_RESPONSE_BODY_BYTES = 10 * 1024 * 1024
MAX_ATTACHMENT_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_SERVICENOW_TRANSPORT_TIMEOUT_SECONDS = 300.0
SERVICENOW_NON_JSON_DIAGNOSTIC_KEY = "[non-json key]"
SERVICENOW_NON_JSON_DIAGNOSTIC_VALUE = "[non-json value]"
SERVICENOW_CIRCULAR_DIAGNOSTIC_VALUE = "[circular reference]"
SERVICENOW_TRUNCATED_DIAGNOSTIC_KEY = "__jedi_response_truncated__"
MAX_SERVICENOW_RECORD_ID_CHARS = 128
MAX_SERVICENOW_TABLE_NAME_CHARS = 128
MAX_SERVICENOW_FIELD_NAME_CHARS = 256
MAX_SERVICENOW_OPERATION_URI_CHARS = 256
MAX_SERVICENOW_LOOKUP_PART_CHARS = 1024
MAX_SERVICENOW_ATTACHMENT_CONTENT_TYPE_CHARS = 255
MAX_SERVICENOW_DICTIONARY_COLUMN_LABEL_CHARS = 255
MAX_SERVICENOW_DICTIONARY_INTERNAL_TYPE_CHARS = 128
MAX_SERVICENOW_DICTIONARY_MAX_LENGTH = 65535
MAX_SERVICENOW_RESULT_LIMIT = 500
MAX_SERVICENOW_STORY_ADDITIONAL_CONTEXT_CHARS = 1024
MAX_SERVICENOW_METADATA_RESPONSE_TEXT_CHARS = 1024
MAX_SERVICENOW_METADATA_RESPONSE_SEQUENCE = 2_147_483_647
MAX_SERVICENOW_JSON_REQUEST_BODY_DEPTH = 100
MAX_SERVICENOW_REQUEST_URL_CHARS = 4096
DOTENV_INPUT_MAX_BYTES = 1024 * 1024
SERVICENOW_LOOKUP_NON_JSON_DIAGNOSTIC = "ServiceNow API lookup contains non-JSON value"
SERVICENOW_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC = "ServiceNow API lookup query is unsafe"
SERVICENOW_METADATA_RESPONSE_FIELD_UNSAFE_DIAGNOSTIC = (
    "ServiceNow API metadata response field is unsafe"
)
SERVICENOW_OPERATION_URI_UNSAFE_DIAGNOSTIC = (
    "ServiceNow API operation URI is unsafe"
)
SERVICENOW_ATTACHMENT_CONTENT_TYPE_UNSAFE_DIAGNOSTIC = (
    "ServiceNow attachment content type is unsafe"
)
SERVICENOW_ATTACHMENT_FILE_NAME_UNSAFE_DIAGNOSTIC = (
    "ServiceNow attachment file name is unsafe"
)
SERVICENOW_BOOLEAN_VALUE_UNSAFE_DIAGNOSTIC = "ServiceNow API boolean value is unsafe"
SERVICENOW_DICTIONARY_COLUMN_LABEL_UNSAFE_DIAGNOSTIC = (
    "ServiceNow dictionary column label is unsafe"
)
SERVICENOW_DICTIONARY_INTERNAL_TYPE_UNSAFE_DIAGNOSTIC = (
    "ServiceNow dictionary internal type is unsafe"
)
SERVICENOW_DICTIONARY_MAX_LENGTH_UNSAFE_DIAGNOSTIC = (
    "ServiceNow dictionary max length is unsafe"
)
SERVICENOW_FIELD_NAME_UNSAFE_DIAGNOSTIC = "ServiceNow API field name is unsafe"
SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC = "ServiceNow API record id is unsafe"
SERVICENOW_RESULT_LIMIT_UNSAFE_DIAGNOSTIC = "ServiceNow API result limit is unsafe"
SERVICENOW_RESULT_MISSING_DIAGNOSTIC = "ServiceNow API response result is missing"
SERVICENOW_STORY_QUERY_UNSAFE_DIAGNOSTIC = "ServiceNow API story query is unsafe"
SERVICENOW_STORY_RESPONSE_FIELD_UNSAFE_DIAGNOSTIC = (
    "ServiceNow API story response field is unsafe"
)
SERVICENOW_CICD_PROBE_ACTION_UNSAFE_DIAGNOSTIC = "ServiceNow CI/CD probe action is unsafe"
SERVICENOW_CICD_REQUEST_ACTION_UNSAFE_DIAGNOSTIC = (
    "ServiceNow CI/CD request action is unsafe"
)
SERVICENOW_TABLE_NAME_UNSAFE_DIAGNOSTIC = "ServiceNow API table name is unsafe"
_SERVICENOW_CICD_PROBE_ACTIONS = frozenset({"create", "retrieve"})
_ATTACHMENT_CONTENT_TYPE_PATTERN = re.compile(
    r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$"
)
_SERVICENOW_FIELD_NAME_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*$"
)
_SERVICENOW_OPERATION_URI_PATTERN = re.compile(r"^/api/[A-Za-z0-9_]+/[A-Za-z0-9_]+$")
_SERVICENOW_RECORD_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_SERVICENOW_CICD_REQUEST_ACTION_PATTERN = re.compile(
    r"^(?:retrieve|preview/[A-Za-z0-9_-]+|commit/[A-Za-z0-9_-]+)$"
)
_SERVICENOW_TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_SERVICENOW_DECIMAL_NUMBER_PATTERN = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")
_SERVICENOW_ALLOWED_TRANSPORT_METHODS = frozenset({"DELETE", "GET", "PATCH", "POST", "PUT"})


class ServiceNowApiError(RuntimeError):
    """Raised when ServiceNow returns an unsuccessful response."""


class HttpRequest(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    method: str
    url: str
    headers: dict[str, str] = {}
    params: dict[str, str] = {}
    body: dict[str, Any] = {}
    body_bytes: bytes | None = None

    def sanitized(self) -> HttpRequest:
        return self.model_copy(
            update={
                "url": _redact_diagnostic_text(self.url),
                "headers": redact_secrets(self.headers),
                "params": redact_secrets(self.params),
                "body": redact_secrets(self.body),
                "body_bytes": b"***REDACTED***" if self.body_bytes is not None else None,
            }
        )


class HttpResponse(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    status_code: int
    json_body: dict[str, Any]


class StoryStateChoice(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    label: str
    value: str
    sequence: int = 0
    inactive: bool = False


class StoryDictionaryField(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    element: str
    column_label: str
    internal_type: str
    active: bool = True
    read_only: bool = False


class HttpTransport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse:
        """Send an HTTP request and return a JSON response."""


class _NoServiceNowRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        raise ServiceNowApiError("ServiceNow API redirects are not allowed")


class UrllibTransport:
    def __init__(self, *, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = _servicenow_transport_timeout_seconds(timeout_seconds)

    @property
    def redirect_handler(self) -> urllib.request.HTTPRedirectHandler:
        return _NoServiceNowRedirectHandler()

    def send(self, request: HttpRequest) -> HttpResponse:
        method = _servicenow_request_method(request.method)
        url = _url_with_params(_servicenow_request_url(request.url), request.params)
        encoded_body = None
        request_body_for_encoding: dict[str, Any] | None = None
        if type(request.headers) is not dict:
            raise ServiceNowApiError("ServiceNow request headers must be an exact dictionary")
        headers = _servicenow_request_headers(request.headers)

        request_body_bytes = request.body_bytes
        if request_body_bytes is not None:
            if type(request_body_bytes) is not bytes:
                raise ServiceNowApiError("ServiceNow request body bytes must be exact bytes")
            encoded_body = request_body_bytes
        else:
            request_body = request.body
            if type(request_body) is not dict:
                raise ServiceNowApiError("ServiceNow request body must be an exact dictionary")
            request_body_for_encoding = request_body
            if not request_body_for_encoding:
                request_body_for_encoding = None

        if request_body_bytes is None and request_body_for_encoding is not None:
            if headers.get("Content-Type") == "application/json":
                try:
                    encoded_body = json.dumps(
                        _servicenow_json_body(request_body_for_encoding),
                        allow_nan=False,
                    ).encode("utf-8")
                except ValueError:
                    raise ServiceNowApiError(
                        "ServiceNow JSON request body contains non-finite numeric values"
                    ) from None
                except TypeError:
                    raise ServiceNowApiError(
                        "ServiceNow JSON request body contains non-JSON values"
                    ) from None
            else:
                encoded_body = _servicenow_transport_urlencode(
                    _servicenow_form_body(request_body_for_encoding)
                ).encode("utf-8")
                headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

        raw_request = _servicenow_transport_request(
            url,
            data=encoded_body,
            headers=headers,
            method=method,
        )
        opener = _servicenow_transport_build_opener(self.redirect_handler)

        try:
            response_context = _servicenow_transport_open(
                opener,
                raw_request,
                self.timeout_seconds,
            )
            response = _servicenow_transport_enter_response_context(response_context)
            try:
                status_code = _servicenow_transport_response_status_attribute(response, "status")
                body = _servicenow_transport_read_response_body(response)
                if len(body) > MAX_HTTP_RESPONSE_BODY_BYTES:
                    raise ServiceNowApiError(
                        "ServiceNow API response body exceeded "
                        f"{MAX_HTTP_RESPONSE_BODY_BYTES} bytes"
                    )
                payload = _success_response_body_to_json(body)
                response_result = HttpResponse(
                    status_code=status_code,
                    json_body=payload,
                )
            except Exception as exc:
                _servicenow_transport_exit_response_context(
                    response_context,
                    type(exc),
                    exc,
                    exc.__traceback__,
                )
                raise
            _servicenow_transport_exit_response_context(response_context, None, None, None)
            return response_result
        except urllib.error.HTTPError as exc:
            status_code = _servicenow_transport_response_status_attribute(exc, "code")
            body = _servicenow_transport_read_response_body(exc)
            if len(body) > MAX_HTTP_RESPONSE_BODY_BYTES:
                message = (
                    "ServiceNow API error response body exceeded "
                    f"{MAX_HTTP_RESPONSE_BODY_BYTES} bytes"
                )
                return HttpResponse(
                    status_code=status_code,
                    json_body={"error": {"message": message}},
                )
            return HttpResponse(
                status_code=status_code,
                json_body=_http_error_body_to_json(body),
            )
        except (urllib.error.URLError, OSError):
            raise ServiceNowApiError("ServiceNow transport request failed") from None


class ServiceNowSettings(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    instance_url: str

    @property
    def base_url(self) -> str:
        return self.instance_url.rstrip("/")


def _http_error_body_to_json(body: bytes) -> dict[str, Any]:
    raw_body = body.decode("utf-8", errors="replace")
    try:
        payload = _loads_servicenow_json(raw_body)
    except json.JSONDecodeError:
        return {"error": {"message": _truncate_http_error_diagnostic(raw_body)}}
    except ValueError:
        return {"error": {"message": "ServiceNow API error response body is not valid JSON"}}
    if isinstance(payload, dict):
        return cast(dict[str, Any], _bound_http_error_diagnostics(payload))
    return {"error": {"message": _truncate_http_error_diagnostic(raw_body)}}


def _success_response_body_to_json(body: bytes) -> dict[str, Any]:
    try:
        raw_body = body.decode("utf-8")
    except UnicodeDecodeError:
        raise ServiceNowApiError("ServiceNow API response body is not valid UTF-8 JSON") from None
    try:
        payload = _loads_servicenow_json(raw_body)
    except (json.JSONDecodeError, ValueError):
        raise ServiceNowApiError("ServiceNow API response body is not valid JSON") from None
    if not isinstance(payload, dict):
        raise ServiceNowApiError("ServiceNow API response body must be a JSON object")
    return cast(dict[str, Any], payload)


def _servicenow_transport_response_status(status_code: Any) -> int:
    if type(status_code) is not int or status_code < 100 or status_code > 599:
        raise ServiceNowApiError(
            "ServiceNow transport response status must be an exact HTTP status code"
        )
    return status_code


def _servicenow_transport_response_status_attribute(source: Any, attribute_name: str) -> int:
    try:
        status_code = getattr(source, attribute_name)
    except Exception:
        raise ServiceNowApiError(
            "ServiceNow transport response status must be an exact HTTP status code"
        ) from None
    return _servicenow_transport_response_status(status_code)


def _servicenow_transport_response_body(body: Any) -> bytes:
    if type(body) is not bytes:
        raise ServiceNowApiError("ServiceNow transport response body must be exact bytes")
    return body


def _servicenow_transport_urlencode(values: dict[str, str]) -> str:
    try:
        return urllib.parse.urlencode(values)
    except Exception:
        raise ServiceNowApiError("ServiceNow transport URL encoding failed") from None


def _servicenow_transport_build_opener(redirect_handler: Any) -> Any:
    try:
        return urllib.request.build_opener(redirect_handler)
    except Exception:
        raise ServiceNowApiError("ServiceNow transport request failed") from None


def _servicenow_transport_request(
    url: str,
    *,
    data: bytes | None,
    headers: dict[str, str],
    method: str,
) -> urllib.request.Request:
    try:
        return urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method=method,
        )
    except Exception:
        raise ServiceNowApiError("ServiceNow transport request failed") from None


def _servicenow_transport_open(
    opener: Any,
    raw_request: urllib.request.Request,
    timeout_seconds: float,
) -> Any:
    try:
        return opener.open(raw_request, timeout=timeout_seconds)
    except urllib.error.HTTPError:
        raise
    except Exception:
        raise ServiceNowApiError("ServiceNow transport request failed") from None


def _servicenow_transport_read_response_body(source: Any) -> bytes:
    try:
        body = source.read(MAX_HTTP_RESPONSE_BODY_BYTES + 1)
    except Exception:
        raise ServiceNowApiError("ServiceNow transport response body read failed") from None
    return _servicenow_transport_response_body(body)


def _servicenow_transport_enter_response_context(context: Any) -> Any:
    try:
        return context.__enter__()
    except Exception:
        raise ServiceNowApiError("ServiceNow transport response context failed") from None


def _servicenow_transport_exit_response_context(
    context: Any,
    exc_type: type[BaseException] | None,
    exc: BaseException | None,
    traceback: TracebackType | None,
) -> None:
    try:
        context.__exit__(exc_type, exc, traceback)
    except Exception:
        raise ServiceNowApiError("ServiceNow transport response context failed") from None


def _servicenow_transport_timeout_seconds(timeout_seconds: Any) -> float:
    if type(timeout_seconds) not in {float, int}:
        raise ServiceNowApiError("ServiceNow transport timeout must be a finite positive number")
    safe_timeout = float(timeout_seconds)
    if (
        not math.isfinite(safe_timeout)
        or safe_timeout <= 0
        or safe_timeout > MAX_SERVICENOW_TRANSPORT_TIMEOUT_SECONDS
    ):
        raise ServiceNowApiError("ServiceNow transport timeout must be a finite positive number")
    return safe_timeout


def _loads_servicenow_json(raw_body: str) -> Any:
    return json.loads(raw_body, parse_constant=_reject_servicenow_json_constant)


def _reject_servicenow_json_constant(_value: str) -> None:
    raise ValueError("non-finite JSON number")


def _servicenow_result_body(response_body: Any) -> dict[str, Any]:
    if type(response_body) is not dict:
        raise ServiceNowApiError("ServiceNow API response body must be an exact dictionary")
    return response_body


def _required_result_record_list(response_body: Any) -> list[dict[str, Any]]:
    body = _servicenow_result_body(response_body)
    if "result" not in body:
        raise ServiceNowApiError(SERVICENOW_RESULT_MISSING_DIAGNOSTIC)
    records = body["result"]
    if not isinstance(records, list):
        raise ServiceNowApiError("ServiceNow API response result must be a list")
    if type(records) is not list:
        raise ServiceNowApiError("ServiceNow API response result must be an exact list")
    if not all(isinstance(record, dict) for record in records):
        raise ServiceNowApiError("ServiceNow API response result entries must be objects")
    if not all(type(record) is dict for record in records):
        raise ServiceNowApiError("ServiceNow API response result entries must be exact objects")
    return cast(list[dict[str, Any]], records)


def _required_result_object(response_body: Any) -> dict[str, Any]:
    body = _servicenow_result_body(response_body)
    if "result" not in body:
        raise ServiceNowApiError(SERVICENOW_RESULT_MISSING_DIAGNOSTIC)
    result = body["result"]
    if not isinstance(result, dict):
        raise ServiceNowApiError("ServiceNow API response result must be an object")
    if type(result) is not dict:
        raise ServiceNowApiError("ServiceNow API response result must be an exact object")
    return cast(dict[str, Any], result)


def _servicenow_lookup_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) is bool or type(value) is int:
        return str(value)
    raise ServiceNowApiError(SERVICENOW_LOOKUP_NON_JSON_DIAGNOSTIC)


def _servicenow_lookup_query(lookup: dict[str, str], *, allow_empty: bool = False) -> str:
    if type(lookup) is not dict:
        raise ServiceNowApiError("ServiceNow API lookup body must be an exact dictionary")
    if lookup == {} and not allow_empty:
        raise ServiceNowApiError("ServiceNow API lookup body must not be empty")
    parts: list[str] = []
    for key, value in lookup.items():
        if _is_unsafe_servicenow_lookup_part(key) or _is_unsafe_servicenow_lookup_part(value):
            raise ServiceNowApiError(SERVICENOW_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC)
        parts.append(f"{key}={value}")
    return "^".join(parts)


def _servicenow_story_query(value: Any) -> str:
    if (
        type(value) is not str
        or value == ""
        or value.strip() != value
        or len(value) > MAX_SERVICENOW_LOOKUP_PART_CHARS
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ServiceNowApiError(SERVICENOW_STORY_QUERY_UNSAFE_DIAGNOSTIC)
    return value


def _servicenow_cicd_probe_action(value: Any) -> str:
    if type(value) is not str or value not in _SERVICENOW_CICD_PROBE_ACTIONS:
        raise ServiceNowApiError(SERVICENOW_CICD_PROBE_ACTION_UNSAFE_DIAGNOSTIC)
    return value


def _servicenow_table_name(table: Any) -> str:
    if (
        type(table) is not str
        or table.strip() != table
        or len(table) > MAX_SERVICENOW_TABLE_NAME_CHARS
        or not _SERVICENOW_TABLE_NAME_PATTERN.fullmatch(table)
    ):
        raise ServiceNowApiError(SERVICENOW_TABLE_NAME_UNSAFE_DIAGNOSTIC)
    return table


def _servicenow_record_id(value: Any) -> str:
    if (
        type(value) is not str
        or value.strip() != value
        or len(value) > MAX_SERVICENOW_RECORD_ID_CHARS
        or not _SERVICENOW_RECORD_ID_PATTERN.fullmatch(value)
    ):
        raise ServiceNowApiError(SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC)
    return value


def _servicenow_operation_uri(value: Any) -> str:
    if type(value) is not str:
        raise ServiceNowApiError(SERVICENOW_OPERATION_URI_UNSAFE_DIAGNOSTIC)
    if (
        value.strip() != value
        or len(value) > MAX_SERVICENOW_OPERATION_URI_CHARS
        or not _SERVICENOW_OPERATION_URI_PATTERN.fullmatch(value)
    ):
        raise ServiceNowApiError(SERVICENOW_OPERATION_URI_UNSAFE_DIAGNOSTIC)
    return value


def _servicenow_field_name(value: Any) -> str:
    if (
        type(value) is not str
        or value.strip() != value
        or len(value) > MAX_SERVICENOW_FIELD_NAME_CHARS
        or not _SERVICENOW_FIELD_NAME_PATTERN.fullmatch(value)
    ):
        raise ServiceNowApiError(SERVICENOW_FIELD_NAME_UNSAFE_DIAGNOSTIC)
    return value


def _servicenow_field_list(values: list[str]) -> str:
    if type(values) is not list:
        raise ServiceNowApiError("ServiceNow API field list must be an exact list")
    if values == []:
        raise ServiceNowApiError("ServiceNow API field list must not be empty")
    return ",".join(_servicenow_field_name(value) for value in values)


def _servicenow_field_body(fields: dict[str, Any]) -> dict[str, Any]:
    if type(fields) is not dict:
        raise ServiceNowApiError("ServiceNow API field body must be an exact dictionary")
    return {_servicenow_field_name(field_name): value for field_name, value in fields.items()}


def _servicenow_dictionary_column_label(value: Any) -> str:
    if (
        type(value) is not str
        or value == ""
        or value.strip() != value
        or len(value) > MAX_SERVICENOW_DICTIONARY_COLUMN_LABEL_CHARS
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ServiceNowApiError(SERVICENOW_DICTIONARY_COLUMN_LABEL_UNSAFE_DIAGNOSTIC)
    return value


def _servicenow_dictionary_internal_type(value: Any) -> str:
    if (
        type(value) is not str
        or value.strip() != value
        or len(value) > MAX_SERVICENOW_DICTIONARY_INTERNAL_TYPE_CHARS
        or not _SERVICENOW_TABLE_NAME_PATTERN.fullmatch(value)
    ):
        raise ServiceNowApiError(SERVICENOW_DICTIONARY_INTERNAL_TYPE_UNSAFE_DIAGNOSTIC)
    return value


def _servicenow_dictionary_max_length(value: Any) -> str:
    if (
        type(value) is not int
        or value < 1
        or value > MAX_SERVICENOW_DICTIONARY_MAX_LENGTH
    ):
        raise ServiceNowApiError(SERVICENOW_DICTIONARY_MAX_LENGTH_UNSAFE_DIAGNOSTIC)
    return str(value)


def _servicenow_result_limit(value: Any) -> str:
    if (
        type(value) is not int
        or value < 1
        or value > MAX_SERVICENOW_RESULT_LIMIT
    ):
        raise ServiceNowApiError(SERVICENOW_RESULT_LIMIT_UNSAFE_DIAGNOSTIC)
    return str(value)


def _servicenow_attachment_file_name(value: Any) -> str:
    if (
        type(value) is not str
        or value.strip() != value
        or value in {"", ".", ".."}
        or len(value) > 255
        or "/" in value
        or "\\" in value
        or has_whitespace_or_control_character(value.replace(" ", ""))
    ):
        raise ServiceNowApiError(SERVICENOW_ATTACHMENT_FILE_NAME_UNSAFE_DIAGNOSTIC)
    return value


def _servicenow_attachment_content_type(value: Any) -> str:
    if (
        type(value) is not str
        or value.strip() != value
        or len(value) > MAX_SERVICENOW_ATTACHMENT_CONTENT_TYPE_CHARS
        or not _ATTACHMENT_CONTENT_TYPE_PATTERN.fullmatch(value)
    ):
        raise ServiceNowApiError(SERVICENOW_ATTACHMENT_CONTENT_TYPE_UNSAFE_DIAGNOSTIC)
    return value


def _is_unsafe_servicenow_lookup_part(value: Any) -> bool:
    if type(value) is not str:
        return True
    return (
        len(value) > MAX_SERVICENOW_LOOKUP_PART_CHARS
        or "^" in value
        or "=" in value
        or any(ord(character) < 32 for character in value)
    )


def _bound_http_error_diagnostics(value: Any) -> Any:
    return _bound_http_error_diagnostics_inner(value, active_container_ids=set())


def _bound_http_error_diagnostics_inner(
    value: Any,
    *,
    active_container_ids: set[int],
) -> Any:
    if type(value) is dict:
        container_id = id(value)
        if container_id in active_container_ids:
            return SERVICENOW_CIRCULAR_DIAGNOSTIC_VALUE
        active_container_ids.add(container_id)
        diagnostic: dict[str, Any] = {}
        try:
            for key, item in islice(
                value.items(),
                MAX_HTTP_ERROR_DIAGNOSTIC_COLLECTION_ITEMS,
            ):
                diagnostic_key = _unique_servicenow_diagnostic_key(
                    diagnostic,
                    _http_error_diagnostic_key(key),
                )
                diagnostic[diagnostic_key] = _bound_http_error_diagnostics_inner(
                    item,
                    active_container_ids=active_container_ids,
                )
            omitted_fields = len(value) - MAX_HTTP_ERROR_DIAGNOSTIC_COLLECTION_ITEMS
            if omitted_fields > 0:
                _add_servicenow_truncation_marker(diagnostic, omitted_fields=omitted_fields)
            return diagnostic
        finally:
            active_container_ids.remove(container_id)
    if type(value) is list:
        container_id = id(value)
        if container_id in active_container_ids:
            return SERVICENOW_CIRCULAR_DIAGNOSTIC_VALUE
        active_container_ids.add(container_id)
        try:
            diagnostic_items = [
                _bound_http_error_diagnostics_inner(
                    item,
                    active_container_ids=active_container_ids,
                )
                for item in islice(value, MAX_HTTP_ERROR_DIAGNOSTIC_COLLECTION_ITEMS)
            ]
            omitted_items = len(value) - MAX_HTTP_ERROR_DIAGNOSTIC_COLLECTION_ITEMS
            if omitted_items > 0:
                diagnostic_items.append({"truncated": True, "omitted_items": omitted_items})
            return diagnostic_items
        finally:
            active_container_ids.remove(container_id)
    if type(value) is tuple:
        container_id = id(value)
        if container_id in active_container_ids:
            return SERVICENOW_CIRCULAR_DIAGNOSTIC_VALUE
        active_container_ids.add(container_id)
        try:
            diagnostic_items = [
                _bound_http_error_diagnostics_inner(
                    item,
                    active_container_ids=active_container_ids,
                )
                for item in islice(value, MAX_HTTP_ERROR_DIAGNOSTIC_COLLECTION_ITEMS)
            ]
            omitted_items = len(value) - MAX_HTTP_ERROR_DIAGNOSTIC_COLLECTION_ITEMS
            if omitted_items > 0:
                diagnostic_items.append({"truncated": True, "omitted_items": omitted_items})
            return diagnostic_items
        finally:
            active_container_ids.remove(container_id)
    if type(value) is str:
        return _safe_http_error_diagnostic_text(value)
    if isinstance(value, str):
        return SERVICENOW_NON_JSON_DIAGNOSTIC_VALUE
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    return SERVICENOW_NON_JSON_DIAGNOSTIC_VALUE


def _http_error_diagnostic_key(key: Any) -> str:
    if type(key) is str:
        diagnostic_key = _safe_http_error_diagnostic_text(key)
        return diagnostic_key or "[empty key]"
    return SERVICENOW_NON_JSON_DIAGNOSTIC_KEY


def _safe_http_error_diagnostic_text(value: str) -> str:
    normalized = " ".join(value.split())
    return _truncate_http_error_diagnostic(normalized)


def _truncate_http_error_diagnostic(value: str) -> str:
    if len(value) <= MAX_HTTP_ERROR_DIAGNOSTIC_CHARS:
        return value
    retained_chars = MAX_HTTP_ERROR_DIAGNOSTIC_CHARS - len(HTTP_ERROR_TRUNCATION_MARKER)
    return f"{value[:retained_chars]}{HTTP_ERROR_TRUNCATION_MARKER}"


def _servicenow_response_body_or_raise(
    *,
    response: Any,
    context: str,
) -> dict[str, Any]:
    status_code = _servicenow_response_status_code(response)
    if status_code >= 400:
        raise ServiceNowApiError(
            _servicenow_api_error_message(
                response,
                context=context,
                status_code=status_code,
            )
        )
    if type(response.json_body) is not dict:
        raise ServiceNowApiError("ServiceNow API response body must be an exact dictionary")
    body = response.json_body.copy()
    body["status_code"] = status_code
    return body


def _servicenow_probe_response_body(response: Any) -> dict[str, Any]:
    status_code = _servicenow_response_status_code(response)
    if type(response.json_body) is not dict:
        raise ServiceNowApiError("ServiceNow API response body must be an exact dictionary")
    body = response.json_body.copy()
    body["status_code"] = status_code
    return body


def _servicenow_raise_for_error(response: Any, *, context: str | None = None) -> None:
    status_code = _servicenow_response_status_code(response)
    if status_code >= 400:
        raise ServiceNowApiError(
            _servicenow_api_error_message(
                response,
                context=context,
                status_code=status_code,
            )
        )


def _servicenow_response_status_code(response: Any) -> int:
    if type(response) is not HttpResponse:
        raise ServiceNowApiError("ServiceNow API response must be an exact HttpResponse")
    status_code = response.status_code
    if type(status_code) is not int:
        raise ServiceNowApiError("ServiceNow API response status code must be an exact integer")
    if status_code < 100 or status_code > 599:
        raise ServiceNowApiError("ServiceNow API response status code must be in the HTTP range")
    return status_code


def _servicenow_api_error_message(
    response: HttpResponse,
    *,
    context: str | None = None,
    status_code: int | None = None,
) -> str:
    if status_code is None:
        raise ServiceNowApiError("ServiceNow API error status code must be prevalidated")
    operation = f" {context}" if context else ""
    diagnostic = _truncate_http_error_diagnostic(
        repr(_servicenow_api_error_diagnostic_body(response.json_body))
    )
    return f"ServiceNow API{operation} failed with status {status_code}: {diagnostic}"


def _servicenow_api_error_diagnostic_body(value: Any) -> Any:
    if type(value) is not dict:
        return SERVICENOW_NON_JSON_DIAGNOSTIC_VALUE
    return _servicenow_diagnostic_value(value)


def _servicenow_diagnostic_value(value: Any) -> Any:
    return _servicenow_diagnostic_value_inner(value, active_container_ids=set())


def _servicenow_diagnostic_value_inner(
    value: Any,
    *,
    active_container_ids: set[int],
) -> Any:
    if type(value) is dict:
        container_id = id(value)
        if container_id in active_container_ids:
            return SERVICENOW_CIRCULAR_DIAGNOSTIC_VALUE
        active_container_ids.add(container_id)
        redacted: dict[str, Any] = {}
        try:
            for key, item in islice(value.items(), MAX_SERVICENOW_DIAGNOSTIC_COLLECTION_ITEMS):
                diagnostic_key = _unique_servicenow_diagnostic_key(
                    redacted,
                    _servicenow_diagnostic_key(key),
                )
                redacted[diagnostic_key] = (
                    "***REDACTED***"
                    if type(key) is str and is_sensitive_key(key)
                    else _servicenow_diagnostic_value_inner(
                        item,
                        active_container_ids=active_container_ids,
                    )
                )
            omitted_fields = len(value) - MAX_SERVICENOW_DIAGNOSTIC_COLLECTION_ITEMS
            if omitted_fields > 0:
                _add_servicenow_truncation_marker(redacted, omitted_fields=omitted_fields)
            return redacted
        finally:
            active_container_ids.remove(container_id)
    if type(value) is list:
        container_id = id(value)
        if container_id in active_container_ids:
            return SERVICENOW_CIRCULAR_DIAGNOSTIC_VALUE
        active_container_ids.add(container_id)
        try:
            redacted_items = [
                _servicenow_diagnostic_value_inner(
                    item,
                    active_container_ids=active_container_ids,
                )
                for item in islice(value, MAX_SERVICENOW_DIAGNOSTIC_COLLECTION_ITEMS)
            ]
            omitted_items = len(value) - MAX_SERVICENOW_DIAGNOSTIC_COLLECTION_ITEMS
            if omitted_items > 0:
                redacted_items.append({"truncated": True, "omitted_items": omitted_items})
            return redacted_items
        finally:
            active_container_ids.remove(container_id)
    if type(value) is tuple:
        container_id = id(value)
        if container_id in active_container_ids:
            return SERVICENOW_CIRCULAR_DIAGNOSTIC_VALUE
        active_container_ids.add(container_id)
        try:
            redacted_items = [
                _servicenow_diagnostic_value_inner(
                    item,
                    active_container_ids=active_container_ids,
                )
                for item in islice(value, MAX_SERVICENOW_DIAGNOSTIC_COLLECTION_ITEMS)
            ]
            omitted_items = len(value) - MAX_SERVICENOW_DIAGNOSTIC_COLLECTION_ITEMS
            if omitted_items > 0:
                redacted_items.append({"truncated": True, "omitted_items": omitted_items})
            return redacted_items
        finally:
            active_container_ids.remove(container_id)
    if type(value) is str:
        return _safe_servicenow_diagnostic_text(value)
    if isinstance(value, str):
        return SERVICENOW_NON_JSON_DIAGNOSTIC_VALUE
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    return SERVICENOW_NON_JSON_DIAGNOSTIC_VALUE


def _servicenow_diagnostic_key(key: Any) -> str:
    if type(key) is str:
        diagnostic_key = _safe_servicenow_diagnostic_text(key)
        return diagnostic_key or "[empty key]"
    return SERVICENOW_NON_JSON_DIAGNOSTIC_KEY


def _unique_servicenow_diagnostic_key(diagnostic: dict[str, Any], key: str) -> str:
    if key not in diagnostic:
        return key
    suffix = 2
    candidate = _servicenow_diagnostic_key_with_suffix(key, suffix)
    while candidate in diagnostic:
        suffix += 1
        candidate = _servicenow_diagnostic_key_with_suffix(key, suffix)
    return candidate


def _servicenow_diagnostic_key_with_suffix(key: str, suffix: int) -> str:
    suffix_label = f" ({suffix})"
    candidate = f"{key}{suffix_label}"
    if len(candidate) <= MAX_HTTP_ERROR_DIAGNOSTIC_CHARS:
        return candidate
    base_key = (
        key[: -len(HTTP_ERROR_TRUNCATION_MARKER)]
        if key.endswith(HTTP_ERROR_TRUNCATION_MARKER)
        else key
    )
    retained_chars = (
        MAX_HTTP_ERROR_DIAGNOSTIC_CHARS
        - len(HTTP_ERROR_TRUNCATION_MARKER)
        - len(suffix_label)
    )
    return f"{base_key[:retained_chars]}{HTTP_ERROR_TRUNCATION_MARKER}{suffix_label}"


def _add_servicenow_truncation_marker(
    diagnostic: dict[str, Any],
    *,
    omitted_fields: int,
) -> None:
    marker_key = _unique_servicenow_diagnostic_key(
        diagnostic,
        SERVICENOW_TRUNCATED_DIAGNOSTIC_KEY,
    )
    diagnostic[marker_key] = {
        "truncated": True,
        "omitted_fields": omitted_fields,
    }


def _safe_servicenow_diagnostic_text(value: str) -> str:
    redacted = _redact_diagnostic_text(value)
    if redacted is None:
        return ""
    normalized = " ".join(redacted.split())
    return _truncate_http_error_diagnostic(normalized)


def _bool_query_value(value: bool) -> str:
    if not isinstance(value, bool):
        raise ServiceNowApiError(SERVICENOW_BOOLEAN_VALUE_UNSAFE_DIAGNOSTIC)
    return "true" if value else "false"


def _servicenow_cicd_request_params(params: dict[str, str] | None) -> dict[str, str]:
    if params is None:
        return {}
    if type(params) is not dict:
        raise ServiceNowApiError("ServiceNow CI/CD request params must be an exact dictionary")
    return params


def _servicenow_cicd_request_body(body: dict[str, Any] | None) -> dict[str, Any]:
    if body is None:
        return {}
    if type(body) is not dict:
        raise ServiceNowApiError("ServiceNow CI/CD request body must be an exact dictionary")
    return body


def _servicenow_cicd_request_action(action: Any) -> str:
    if (
        type(action) is not str
        or len(action) > MAX_SERVICENOW_OPERATION_URI_CHARS
        or not _SERVICENOW_CICD_REQUEST_ACTION_PATTERN.fullmatch(action)
    ):
        raise ServiceNowApiError(SERVICENOW_CICD_REQUEST_ACTION_UNSAFE_DIAGNOSTIC)
    return action


def _oauth_response_status_code(response: Any) -> int:
    if type(response) is not HttpResponse:
        raise ServiceNowApiError("ServiceNow OAuth response must be an exact HttpResponse")
    status_code = response.status_code
    if type(status_code) is not int:
        raise ServiceNowApiError("ServiceNow OAuth response status code must be an exact integer")
    if status_code < 100 or status_code > 599:
        raise ServiceNowApiError("ServiceNow OAuth response status code must be in the HTTP range")
    return status_code


def _oauth_response_json_body(response: HttpResponse) -> dict[str, Any]:
    body = response.json_body
    if type(body) is not dict:
        raise ServiceNowApiError("ServiceNow OAuth response body must be an exact dictionary")
    return body


class OAuthClientCredentials:
    def __init__(
        self,
        *,
        instance_url: str,
        client_id: str,
        client_secret: str,
        transport: HttpTransport,
    ) -> None:
        self._instance_url = instance_url.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._transport = transport
        self._access_token: str | None = None

    def authorization_header(self) -> str:
        if self._access_token is None:
            self._access_token = self._fetch_token()
        return f"Bearer {self._access_token}"

    def _fetch_token(self) -> str:
        response = self._transport.send(
            HttpRequest(
                method="POST",
                url=f"{self._instance_url}/oauth_token.do",
                body={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )
        )
        status_code = _oauth_response_status_code(response)
        if status_code >= 400:
            raise ServiceNowApiError(f"ServiceNow OAuth failed with status {status_code}")
        body = _oauth_response_json_body(response)
        token = body.get("access_token")
        if (
            type(token) is not str
            # Empty token is rejected; this is not a hardcoded secret.
            or token == ""  # nosec B105
            or not token.isascii()
            or len(token.encode("ascii")) > MAX_OAUTH_ACCESS_TOKEN_BYTES
            or token != token.strip()
            or has_whitespace_or_control_character(token)
        ):
            raise ServiceNowApiError("ServiceNow OAuth response did not include access_token")
        return token


class ServiceNowClient:
    def __init__(
        self,
        *,
        settings: ServiceNowSettings,
        auth: OAuthClientCredentials,
        transport: HttpTransport,
    ) -> None:
        self._settings = settings
        self._auth = auth
        self._transport = transport

    def fetch_ready_stories(
        self,
        project_sys_id: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Story]:
        query = "state=Ready"
        if project_sys_id is not None:
            query = f"{query}^project={_servicenow_record_id(project_sys_id)}"
        return self.fetch_stories(sysparm_query=query, limit=limit)

    def fetch_stories(
        self,
        sysparm_query: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Story]:
        safe_limit = _servicenow_result_limit(limit)
        params = {
            "sysparm_limit": safe_limit,
            "sysparm_fields": ",".join(
                [
                    "sys_id",
                    "number",
                    "short_description",
                    "description",
                    "acceptance_criteria",
                    "story_points",
                    "priority",
                    "state",
                    "u_ai_status",
                    "u_ai_handoff_type",
                    "u_ai_handoff_reference",
                    "u_ai_artifact_reference",
                    "u_ai_build_reference",
                    "u_ai_candidate_artifact",
                ]
            ),
        }
        if sysparm_query is not None:
            params["sysparm_query"] = _servicenow_story_query(sysparm_query)

        request = HttpRequest(
            method="GET",
            url=f"{self._settings.base_url}/api/now/table/rm_story",
            headers={
                "Authorization": self._auth.authorization_header(),
                "Accept": "application/json",
            },
            params=params,
        )
        response = self._transport.send(request)
        _servicenow_raise_for_error(response)
        return [
            _story_from_record(record)
            for record in _required_result_record_list(response.json_body)
        ]

    def fetch_story_state_choices(self) -> list[StoryStateChoice]:
        request = HttpRequest(
            method="GET",
            url=f"{self._settings.base_url}/api/now/table/sys_choice",
            headers={
                "Authorization": self._auth.authorization_header(),
                "Accept": "application/json",
            },
            params={
                "sysparm_query": "name=rm_story^element=state^inactive=false",
                "sysparm_fields": "label,value,sequence,inactive",
            },
        )
        response = self._transport.send(request)
        _servicenow_raise_for_error(response)
        choices = [
            _state_choice_from_record(record)
            for record in _required_result_record_list(response.json_body)
        ]
        return sorted(
            [choice for choice in choices if not choice.inactive],
            key=lambda choice: choice.sequence,
        )

    def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
        request = HttpRequest(
            method="GET",
            url=f"{self._settings.base_url}/api/now/table/sys_dictionary",
            headers={
                "Authorization": self._auth.authorization_header(),
                "Accept": "application/json",
            },
            params={
                "sysparm_query": "name=rm_story^active=true",
                "sysparm_fields": "element,column_label,internal_type,active,read_only",
            },
        )
        response = self._transport.send(request)
        _servicenow_raise_for_error(response)
        return [
            field
            for field in (
                _dictionary_field_from_record(record)
                for record in _required_result_record_list(response.json_body)
            )
            if field.active
        ]

    def create_story_dictionary_field(
        self,
        *,
        element: str,
        column_label: str,
        internal_type: str,
        max_length: int | None,
        read_only: bool,
    ) -> dict[str, Any]:
        safe_element = _servicenow_field_name(element)
        safe_column_label = _servicenow_dictionary_column_label(column_label)
        safe_internal_type = _servicenow_dictionary_internal_type(internal_type)
        body = {
            "name": "rm_story",
            "element": safe_element,
            "column_label": safe_column_label,
            "internal_type": safe_internal_type,
            "active": "true",
            "read_only": _bool_query_value(read_only),
        }
        if max_length is not None:
            body["max_length"] = _servicenow_dictionary_max_length(max_length)

        request = HttpRequest(
            method="POST",
            url=f"{self._settings.base_url}/api/now/table/sys_dictionary",
            headers={
                "Authorization": self._auth.authorization_header(),
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            body=body,
        )
        response = self._transport.send(request)
        _servicenow_raise_for_error(response)
        return _required_result_object(response.json_body)

    def update_story_fields(self, story_sys_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        safe_story_sys_id = _servicenow_record_id(story_sys_id)
        safe_fields = _servicenow_field_body(fields)
        request = HttpRequest(
            method="PATCH",
            url=f"{self._settings.base_url}/api/now/table/rm_story/{safe_story_sys_id}",
            headers={
                "Authorization": self._auth.authorization_header(),
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            body=safe_fields,
        )
        response = self._transport.send(request)
        _servicenow_raise_for_error(response)
        return _required_result_object(response.json_body)

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        table_name = _servicenow_table_name(table)
        safe_fields = _servicenow_field_body(fields)
        existing_record = self.fetch_table_record(table=table, lookup=lookup)
        if existing_record is not None:
            sys_id = _servicenow_record_id(
                _servicenow_lookup_text(existing_record.get("sys_id"))
            )
            operation = f"PATCH {table_name}"
            response = self._transport.send(
                HttpRequest(
                    method="PATCH",
                    url=f"{self._settings.base_url}/api/now/table/{table_name}/{sys_id}",
                    headers={
                        "Authorization": self._auth.authorization_header(),
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    body=safe_fields,
                )
            )
        else:
            operation = f"POST {table_name}"
            response = self._transport.send(
                HttpRequest(
                    method="POST",
                    url=f"{self._settings.base_url}/api/now/table/{table_name}",
                    headers={
                        "Authorization": self._auth.authorization_header(),
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    body=safe_fields,
                )
            )
        _servicenow_raise_for_error(response, context=operation)
        return _required_result_object(response.json_body)

    def fetch_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
    ) -> dict[str, Any] | None:
        table_name = _servicenow_table_name(table)
        query = _servicenow_lookup_query(lookup)
        response = self._transport.send(
            HttpRequest(
                method="GET",
                url=f"{self._settings.base_url}/api/now/table/{table_name}",
                headers={
                    "Authorization": self._auth.authorization_header(),
                    "Accept": "application/json",
                },
                params={
                    "sysparm_query": query,
                    "sysparm_limit": "1",
                },
            )
        )
        _servicenow_raise_for_error(response)
        records = _required_result_record_list(response.json_body)
        if records:
            return records[0]
        return None

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        table_name = _servicenow_table_name(table)
        query = _servicenow_lookup_query(lookup, allow_empty=True)
        safe_limit = _servicenow_result_limit(limit)
        params = {
            "sysparm_query": query,
            "sysparm_limit": safe_limit,
        }
        if fields is not None:
            params["sysparm_fields"] = _servicenow_field_list(fields)
        response = self._transport.send(
            HttpRequest(
                method="GET",
                url=f"{self._settings.base_url}/api/now/table/{table_name}",
                headers={
                    "Authorization": self._auth.authorization_header(),
                    "Accept": "application/json",
                },
                params=params,
            )
        )
        _servicenow_raise_for_error(response)
        return _required_result_record_list(response.json_body)

    def probe_cicd_update_set_endpoint(self, *, action: str) -> dict[str, Any]:
        safe_action = _servicenow_cicd_probe_action(action)
        response = self._transport.send(
            HttpRequest(
                method="POST",
                url=f"{self._settings.base_url}/api/sn_cicd/update_set/{safe_action}",
                headers={
                    "Authorization": self._auth.authorization_header(),
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
        )
        return _servicenow_probe_response_body(response)

    def retrieve_cicd_update_set(
        self,
        *,
        update_set_id: str,
        update_source_id: str | None = None,
        update_source_instance_id: str | None = None,
        auto_preview: bool = False,
        cleanup_retrieved: bool = False,
    ) -> dict[str, Any]:
        params = {
            "update_set_id": _servicenow_record_id(update_set_id),
            "auto_preview": _bool_query_value(auto_preview),
            "cleanup_retrieved": _bool_query_value(cleanup_retrieved),
        }
        if update_source_id is not None:
            params["update_source_id"] = _servicenow_record_id(update_source_id)
        if update_source_instance_id is not None:
            params["update_source_instance_id"] = _servicenow_record_id(
                update_source_instance_id
            )
        return self._send_cicd_update_set_request(
            method="POST",
            action="retrieve",
            params=params,
        )

    def preview_cicd_update_set(self, *, remote_update_set_id: str) -> dict[str, Any]:
        safe_remote_update_set_id = _servicenow_record_id(remote_update_set_id)
        return self._send_cicd_update_set_request(
            method="POST",
            action=f"preview/{safe_remote_update_set_id}",
        )

    def commit_cicd_update_set(
        self,
        *,
        remote_update_set_id: str,
        force_commit: bool = False,
    ) -> dict[str, Any]:
        safe_remote_update_set_id = _servicenow_record_id(remote_update_set_id)
        return self._send_cicd_update_set_request(
            method="POST",
            action=f"commit/{safe_remote_update_set_id}",
            body={"force_commit": _bool_query_value(force_commit)},
        )

    def fetch_cicd_progress(self, *, progress_id: str) -> dict[str, Any]:
        safe_progress_id = _servicenow_record_id(progress_id)
        response = self._transport.send(
            HttpRequest(
                method="GET",
                url=f"{self._settings.base_url}/api/sn_cicd/progress/{safe_progress_id}",
                headers={
                    "Authorization": self._auth.authorization_header(),
                    "Accept": "application/json",
                },
            )
        )
        return _servicenow_response_body_or_raise(
            response=response,
            context=f"GET sn_cicd/progress/{safe_progress_id}",
        )

    def import_update_set_xml(
        self,
        *,
        service_id: str,
        update_set_xml: str,
    ) -> dict[str, Any]:
        operation_uri = self._fetch_update_set_importer_operation_uri(service_id=service_id)
        response = self._transport.send(
            HttpRequest(
                method="POST",
                url=f"{self._settings.base_url}{operation_uri}",
                headers={
                    "Authorization": self._auth.authorization_header(),
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                body={"update_set_xml": update_set_xml},
            )
        )
        return _servicenow_response_body_or_raise(
            response=response,
            context=f"POST {operation_uri}",
        )

    def _fetch_update_set_importer_operation_uri(self, *, service_id: str) -> str:
        records = self.fetch_table_records(
            table="sys_ws_operation",
            lookup={
                "web_service_definition.service_id": service_id,
                "name": "import_update_set_xml",
                "active": "true",
            },
            fields=["operation_uri"],
            limit=1,
        )
        if not records:
            raise ServiceNowApiError(
                f"ServiceNow Update Set importer operation not found for service_id={service_id}"  # nosec B608
            )
        return _servicenow_operation_uri(records[0].get("operation_uri"))

    def _send_cicd_update_set_request(
        self,
        *,
        method: str,
        action: str,
        params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        safe_method = _servicenow_request_method(method)
        safe_action = _servicenow_cicd_request_action(action)
        safe_params = _servicenow_cicd_request_params(params)
        safe_body = _servicenow_cicd_request_body(body)
        response = self._transport.send(
            HttpRequest(
                method=safe_method,
                url=f"{self._settings.base_url}/api/sn_cicd/update_set/{safe_action}",
                headers={
                    "Authorization": self._auth.authorization_header(),
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                params=safe_params,
                body=safe_body,
            )
        )
        return _servicenow_response_body_or_raise(
            response=response,
            context=f"{safe_method} sn_cicd/update_set/{safe_action}",
        )

    def attach_story_file(
        self,
        story_sys_id: str,
        *,
        file_path: Path,
        file_name: str,
        content_type: str,
    ) -> dict[str, Any]:
        safe_story_sys_id = _servicenow_record_id(story_sys_id)
        safe_file_name = _servicenow_attachment_file_name(file_name)
        safe_content_type = _servicenow_attachment_content_type(content_type)
        try:
            body_bytes = read_regular_artifact_bytes(
                file_path,
                max_bytes=MAX_ATTACHMENT_UPLOAD_BYTES,
            )
        except ArtifactReadError as exc:
            if exc.reason == "too_large":
                raise ServiceNowApiError(
                    f"ServiceNow attachment file exceeds {MAX_ATTACHMENT_UPLOAD_BYTES} bytes"
                ) from None
            raise ServiceNowApiError("ServiceNow attachment file must be a regular file") from None
        request = HttpRequest(
            method="POST",
            url=f"{self._settings.base_url}/api/now/attachment/file",
            headers={
                "Authorization": self._auth.authorization_header(),
                "Accept": "application/json",
                "Content-Type": safe_content_type,
            },
            params={
                "table_name": "rm_story",
                "table_sys_id": safe_story_sys_id,
                "file_name": safe_file_name,
            },
            body_bytes=body_bytes,
        )
        response = self._transport.send(request)
        _servicenow_raise_for_error(response)
        return _required_result_object(response.json_body)


def load_dotenv_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in _read_bounded_dotenv_text(path).splitlines():
        stripped_line = raw_line.strip()
        if stripped_line == "" or stripped_line.startswith("#") or "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        _validate_dotenv_key(key)
        if key in values:
            raise ValueError(f"dotenv_duplicate_key: {key}")
        values[key] = _parse_dotenv_value(key=key, raw_value=value)
    return values


def _validate_dotenv_key(key: str) -> None:
    if (
        key == ""
        or key != key.strip()
        or not (key[0].isalpha() or key[0] == "_")
        or not all(
            character.isupper() or character.isdigit() or character == "_" for character in key
        )
        or any(
            character.isspace() or ord(character) < 32 or ord(character) == 127 for character in key
        )
    ):
        raise ValueError("dotenv_invalid_key")


def _parse_dotenv_value(*, key: str, raw_value: str) -> str:
    value = raw_value.strip()
    if value == "":
        return ""
    starts_single = value.startswith("'")
    ends_single = value.endswith("'")
    starts_double = value.startswith('"')
    ends_double = value.endswith('"')
    if starts_single or ends_single or starts_double or ends_double:
        if starts_single and ends_single and not starts_double and not ends_double:
            return value[1:-1]
        if starts_double and ends_double and not starts_single and not ends_single:
            return value[1:-1]
        raise ValueError(f"dotenv_invalid_value_quotes: {key}")
    return value


def _servicenow_form_body(body: dict[str, Any]) -> dict[str, str]:
    form_body: dict[str, str] = {}
    for key, value in body.items():
        if type(key) is not str or type(value) is not str:
            raise ServiceNowApiError(
                "ServiceNow form request body must contain exact string keys and values"
            )
        form_body[key] = value
    return form_body


def _servicenow_json_body(
    value: Any,
    *,
    depth: int = 0,
    active_container_ids: set[int] | None = None,
) -> Any:
    if depth > MAX_SERVICENOW_JSON_REQUEST_BODY_DEPTH:
        raise ServiceNowApiError("ServiceNow JSON request body is too deeply nested")
    if value is None or type(value) is str or type(value) is bool or type(value) is int:
        return value
    if type(value) is float:
        if math.isfinite(value):
            return value
        raise ValueError("non-finite ServiceNow JSON request body value")
    if type(value) is list:
        active_container_ids = _servicenow_active_json_container_ids(
            value, active_container_ids
        )
        try:
            return [
                _servicenow_json_body(
                    item,
                    depth=depth + 1,
                    active_container_ids=active_container_ids,
                )
                for item in value
            ]
        finally:
            active_container_ids.remove(id(value))
    if type(value) is dict:
        active_container_ids = _servicenow_active_json_container_ids(
            value, active_container_ids
        )
        json_body: dict[str, Any] = {}
        try:
            for key, item in value.items():
                if type(key) is not str:
                    raise TypeError("non-JSON ServiceNow JSON request body key")
                json_body[key] = _servicenow_json_body(
                    item,
                    depth=depth + 1,
                    active_container_ids=active_container_ids,
                )
            return json_body
        finally:
            active_container_ids.remove(id(value))
    raise TypeError("non-JSON ServiceNow JSON request body value")


def _servicenow_active_json_container_ids(
    value: dict[str, Any] | list[Any],
    active_container_ids: set[int] | None,
) -> set[int]:
    if active_container_ids is None:
        active_container_ids = set()
    container_id = id(value)
    if container_id in active_container_ids:
        raise ServiceNowApiError("ServiceNow JSON request body contains circular references")
    active_container_ids.add(container_id)
    return active_container_ids


def _read_bounded_dotenv_text(path: Path) -> str:
    try:
        with open_regular_artifact_file(path) as env_file:
            payload = env_file.read(DOTENV_INPUT_MAX_BYTES + 1)
    except ArtifactReadError:
        raise ValueError("dotenv_must_be_regular_file") from None
    if len(payload) > DOTENV_INPUT_MAX_BYTES:
        raise ValueError(f"dotenv_input_too_large: exceeds {DOTENV_INPUT_MAX_BYTES} bytes")
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("dotenv_invalid_utf8") from None


def oauth_auth_from_env(
    path: Path,
    *,
    instance_url: str,
    transport: HttpTransport,
) -> OAuthClientCredentials:
    values = load_dotenv_values(path)
    client_id = values.get("SERVICENOW_CLIENT_ID")
    client_secret = values.get("SERVICENOW_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ServiceNowApiError("Missing SERVICENOW_CLIENT_ID or SERVICENOW_CLIENT_SECRET in .env")

    return OAuthClientCredentials(
        instance_url=instance_url,
        client_id=client_id,
        client_secret=client_secret,
        transport=transport,
    )


def servicenow_client_from_env(path: Path, *, transport: HttpTransport) -> ServiceNowClient:
    values = load_dotenv_values(path)
    instance_url = values.get("SERVICENOW_INSTANCE_URL")

    if not instance_url:
        raise ServiceNowApiError("Missing SERVICENOW_INSTANCE_URL in .env")

    auth = oauth_auth_from_env(path, instance_url=instance_url, transport=transport)
    return ServiceNowClient(
        settings=ServiceNowSettings(instance_url=instance_url),
        auth=auth,
        transport=transport,
    )


def redact_secrets(value: Any) -> Any:
    return _redact_secrets_inner(value, active_container_ids=set())


def _redact_secrets_inner(
    value: Any,
    *,
    active_container_ids: set[int],
) -> Any:
    if type(value) is dict:
        container_id = id(value)
        if container_id in active_container_ids:
            return SERVICENOW_CIRCULAR_DIAGNOSTIC_VALUE
        active_container_ids.add(container_id)
        redacted: dict[str, Any] = {}
        try:
            for key, item in islice(value.items(), MAX_SECRET_REDACTION_COLLECTION_ITEMS):
                redacted_key = _unique_servicenow_diagnostic_key(
                    redacted,
                    _servicenow_diagnostic_key(key),
                )
                redacted[redacted_key] = (
                    "***REDACTED***"
                    if type(key) is str and is_sensitive_key(key)
                    else _redact_secrets_inner(
                        item,
                        active_container_ids=active_container_ids,
                    )
                )
            omitted_fields = len(value) - MAX_SECRET_REDACTION_COLLECTION_ITEMS
            if omitted_fields > 0:
                _add_servicenow_truncation_marker(redacted, omitted_fields=omitted_fields)
            return redacted
        finally:
            active_container_ids.remove(container_id)
    if type(value) is list:
        container_id = id(value)
        if container_id in active_container_ids:
            return SERVICENOW_CIRCULAR_DIAGNOSTIC_VALUE
        active_container_ids.add(container_id)
        try:
            redacted_items = [
                _redact_secrets_inner(
                    item,
                    active_container_ids=active_container_ids,
                )
                for item in islice(value, MAX_SECRET_REDACTION_COLLECTION_ITEMS)
            ]
            omitted_items = len(value) - MAX_SECRET_REDACTION_COLLECTION_ITEMS
            if omitted_items > 0:
                redacted_items.append({"truncated": True, "omitted_items": omitted_items})
            return redacted_items
        finally:
            active_container_ids.remove(container_id)
    if type(value) is tuple:
        container_id = id(value)
        if container_id in active_container_ids:
            return SERVICENOW_CIRCULAR_DIAGNOSTIC_VALUE
        active_container_ids.add(container_id)
        try:
            redacted_items = [
                _redact_secrets_inner(
                    item,
                    active_container_ids=active_container_ids,
                )
                for item in islice(value, MAX_SECRET_REDACTION_COLLECTION_ITEMS)
            ]
            omitted_items = len(value) - MAX_SECRET_REDACTION_COLLECTION_ITEMS
            if omitted_items > 0:
                redacted_items.append({"truncated": True, "omitted_items": omitted_items})
            return redacted_items
        finally:
            active_container_ids.remove(container_id)
    if type(value) is str:
        redacted_text = _redact_diagnostic_text(value)
        if redacted_text is None:
            return ""
        normalized_text = " ".join(redacted_text.split())
        return _truncate_http_error_diagnostic(normalized_text)
    if isinstance(value, str):
        return SERVICENOW_NON_JSON_DIAGNOSTIC_VALUE
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    return SERVICENOW_NON_JSON_DIAGNOSTIC_VALUE


def _story_from_record(record: dict[str, Any]) -> Story:
    description = record.get("description")
    if description is None or description == "":
        description = record["short_description"]
    return Story(
        sys_id=_servicenow_story_response_text(record["sys_id"]),
        number=_servicenow_story_response_text(record["number"]),
        short_description=_servicenow_story_response_text(record["short_description"]),
        description=_servicenow_story_response_text(description),
        acceptance_criteria=_optional_servicenow_story_response_text(
            record.get("acceptance_criteria")
        ),
        story_points=_servicenow_story_response_float(
            record.get("story_points", 0), default=0.0
        ),
        priority=_servicenow_story_response_int(record.get("priority", 5), default=5),
        state=_servicenow_story_response_text(record["state"]),
        data_classification=DataClassification.PUBLIC,
        additional_context={
            key: _servicenow_story_additional_context_text(record[key])
            for key in [
                "u_ai_status",
                "u_ai_handoff_type",
                "u_ai_handoff_reference",
                "u_ai_artifact_reference",
                "u_ai_build_reference",
                "u_ai_candidate_artifact",
            ]
            if record.get(key)
        },
    )


def _servicenow_story_response_text(value: Any) -> str:
    if type(value) is not str:
        raise ServiceNowApiError(SERVICENOW_STORY_RESPONSE_FIELD_UNSAFE_DIAGNOSTIC)
    return value


def _servicenow_story_additional_context_text(value: Any) -> str:
    text = _servicenow_story_response_text(value)
    if len(text) > MAX_SERVICENOW_STORY_ADDITIONAL_CONTEXT_CHARS:
        raise ServiceNowApiError(SERVICENOW_STORY_RESPONSE_FIELD_UNSAFE_DIAGNOSTIC)
    return text


def _optional_servicenow_story_response_text(value: Any) -> str | None:
    if value is None:
        return None
    text = _servicenow_story_response_text(value)
    return text if text.strip() else None


def _servicenow_story_response_int(value: Any, *, default: int) -> int:
    if value is None:
        return default
    if type(value) is int:
        return value
    if type(value) is str:
        if value == "":
            return default
        if value.isascii() and value.isdecimal():
            return int(value)
    raise ServiceNowApiError(SERVICENOW_STORY_RESPONSE_FIELD_UNSAFE_DIAGNOSTIC)


def _servicenow_story_response_float(value: Any, *, default: float) -> float:
    if value is None:
        return default
    if type(value) is int or type(value) is float:
        if math.isfinite(value) and value >= 0:
            return float(value)
        raise ServiceNowApiError(SERVICENOW_STORY_RESPONSE_FIELD_UNSAFE_DIAGNOSTIC)
    if type(value) is str:
        if value == "":
            return default
        if _SERVICENOW_DECIMAL_NUMBER_PATTERN.fullmatch(value):
            return float(value)
    raise ServiceNowApiError(SERVICENOW_STORY_RESPONSE_FIELD_UNSAFE_DIAGNOSTIC)


def _state_choice_from_record(record: dict[str, Any]) -> StoryStateChoice:
    return StoryStateChoice(
        label=_servicenow_metadata_response_text(record["label"]),
        value=_servicenow_metadata_response_text(record["value"]),
        sequence=_servicenow_metadata_response_int(record.get("sequence", 0)),
        inactive=_servicenow_metadata_response_bool(record.get("inactive", False)),
    )


def _dictionary_field_from_record(record: dict[str, Any]) -> StoryDictionaryField:
    column_label = record.get("column_label")
    if column_label is None or column_label == "":
        column_label = record["element"]
    internal_type = record.get("internal_type")
    if internal_type is None:
        internal_type = ""
    return StoryDictionaryField(
        element=_servicenow_metadata_response_text(record["element"]),
        column_label=_servicenow_metadata_response_text(column_label),
        internal_type=_servicenow_metadata_response_text(internal_type),
        active=_servicenow_metadata_response_bool(record.get("active", True)),
        read_only=_servicenow_metadata_response_bool(record.get("read_only", False)),
    )


def _servicenow_metadata_response_text(value: Any) -> str:
    if (
        type(value) is not str
        or len(value) > MAX_SERVICENOW_METADATA_RESPONSE_TEXT_CHARS
        or _contains_ascii_control_character(value)
    ):
        raise ServiceNowApiError(SERVICENOW_METADATA_RESPONSE_FIELD_UNSAFE_DIAGNOSTIC)
    return value


def _contains_ascii_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _servicenow_metadata_response_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if type(value) is str:
        normalized = value.lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no", ""}:
            return False
    raise ServiceNowApiError(SERVICENOW_METADATA_RESPONSE_FIELD_UNSAFE_DIAGNOSTIC)


def _servicenow_metadata_response_int(value: Any) -> int:
    if type(value) is int:
        if 0 <= value <= MAX_SERVICENOW_METADATA_RESPONSE_SEQUENCE:
            return value
        raise ServiceNowApiError(SERVICENOW_METADATA_RESPONSE_FIELD_UNSAFE_DIAGNOSTIC)
    if type(value) is str:
        if value == "":
            return 0
        if value.isascii() and value.isdecimal() and len(value) <= 10:
            parsed_value = int(value)
            if parsed_value <= MAX_SERVICENOW_METADATA_RESPONSE_SEQUENCE:
                return parsed_value
    raise ServiceNowApiError(SERVICENOW_METADATA_RESPONSE_FIELD_UNSAFE_DIAGNOSTIC)


def _url_with_params(url: str, params: dict[str, str]) -> str:
    if type(params) is not dict:
        raise ServiceNowApiError("ServiceNow request query params must be an exact dictionary")
    if not params:
        return url
    return f"{url}?{_servicenow_transport_urlencode(_servicenow_query_params(params))}"


def _servicenow_query_params(params: dict[str, str]) -> dict[str, str]:
    safe_params: dict[str, str] = {}
    for key, value in params.items():
        if type(key) is not str or type(value) is not str:
            raise ServiceNowApiError(
                "ServiceNow query params must contain exact string keys and values"
            )
        safe_params[key] = value
    return safe_params


def _servicenow_request_method(method: str) -> str:
    if type(method) is not str or method not in _SERVICENOW_ALLOWED_TRANSPORT_METHODS:
        raise ServiceNowApiError("ServiceNow request method is unsafe")
    return method


def _servicenow_request_url(url: str) -> str:
    if (
        type(url) is not str
        or url == ""
        or len(url) > MAX_SERVICENOW_REQUEST_URL_CHARS
        or has_whitespace_or_control_character(url)
    ):
        raise ServiceNowApiError("ServiceNow request URL is unsafe")
    parsed_url = urllib.parse.urlsplit(url)
    if (
        parsed_url.scheme not in {"http", "https"}
        or parsed_url.netloc == ""
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.fragment != ""
        or has_whitespace_or_control_character(urllib.parse.unquote(url))
    ):
        raise ServiceNowApiError("ServiceNow request URL is unsafe")
    return url


def _servicenow_request_headers(headers: dict[str, str]) -> dict[str, str]:
    safe_headers: dict[str, str] = {}
    for key, value in headers.items():
        if type(key) is not str or type(value) is not str:
            raise ServiceNowApiError(
                "ServiceNow request headers must contain exact string keys and values"
            )
        safe_headers[key] = value
    return safe_headers
