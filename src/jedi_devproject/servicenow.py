from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel

from jedi_devproject.models import DataClassification, Story

SENSITIVE_KEYS = {"authorization", "client_secret", "access_token", "refresh_token", "password"}


class ServiceNowApiError(RuntimeError):
    """Raised when ServiceNow returns an unsuccessful response."""


class HttpRequest(BaseModel):
    method: str
    url: str
    headers: dict[str, str] = {}
    params: dict[str, str] = {}
    body: dict[str, Any] = {}
    body_bytes: bytes | None = None

    def sanitized(self) -> HttpRequest:
        return self.model_copy(
            update={
                "headers": redact_secrets(self.headers),
                "params": redact_secrets(self.params),
                "body": redact_secrets(self.body),
            }
        )


class HttpResponse(BaseModel):
    status_code: int
    json_body: dict[str, Any]


class StoryStateChoice(BaseModel):
    label: str
    value: str
    sequence: int = 0
    inactive: bool = False


class StoryDictionaryField(BaseModel):
    element: str
    column_label: str
    internal_type: str
    active: bool = True
    read_only: bool = False


class HttpTransport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse:
        """Send an HTTP request and return a JSON response."""


class UrllibTransport:
    def send(self, request: HttpRequest) -> HttpResponse:
        url = _url_with_params(request.url, request.params)
        encoded_body = None
        headers = dict(request.headers)

        if request.body_bytes is not None:
            encoded_body = request.body_bytes
        elif request.body:
            if headers.get("Content-Type") == "application/json":
                encoded_body = json.dumps(request.body).encode("utf-8")
            else:
                encoded_body = urllib.parse.urlencode(request.body).encode("utf-8")
                headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

        raw_request = urllib.request.Request(
            url,
            data=encoded_body,
            headers=headers,
            method=request.method,
        )

        try:
            with urllib.request.urlopen(raw_request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return HttpResponse(status_code=response.status, json_body=payload)
        except urllib.error.HTTPError as exc:
            return HttpResponse(
                status_code=exc.code,
                json_body=_http_error_body_to_json(exc.read()),
            )


class ServiceNowSettings(BaseModel):
    instance_url: str

    @property
    def base_url(self) -> str:
        return self.instance_url.rstrip("/")


def _http_error_body_to_json(body: bytes) -> dict[str, Any]:
    raw_body = body.decode("utf-8", errors="replace")
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return {"error": {"message": raw_body}}
    if isinstance(payload, dict):
        return payload
    return {"error": {"message": raw_body}}


def _servicenow_response_body_or_raise(
    *,
    response: HttpResponse,
    context: str,
) -> dict[str, Any]:
    if response.status_code >= 400:
        raise ServiceNowApiError(
            f"ServiceNow API {context} failed with status {response.status_code}: "
            f"{redact_secrets(response.json_body)}"
        )
    body = dict(response.json_body)
    body["status_code"] = response.status_code
    return body


def _bool_query_value(value: bool) -> str:
    return "true" if value else "false"


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
        if response.status_code >= 400:
            raise ServiceNowApiError(f"ServiceNow OAuth failed with status {response.status_code}")
        token = response.json_body.get("access_token")
        if not isinstance(token, str) or token.strip() == "":
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
        if project_sys_id:
            query = f"{query}^project={project_sys_id}"
        return self.fetch_stories(sysparm_query=query, limit=limit)

    def fetch_stories(
        self,
        sysparm_query: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Story]:
        params = {
            "sysparm_limit": str(limit),
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
        if sysparm_query:
            params["sysparm_query"] = sysparm_query

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
        if response.status_code >= 400:
            raise ServiceNowApiError(
                f"ServiceNow API failed with status {response.status_code}: "
                f"{redact_secrets(response.json_body)}"
            )
        return [_story_from_record(record) for record in response.json_body.get("result", [])]

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
        if response.status_code >= 400:
            raise ServiceNowApiError(
                f"ServiceNow API failed with status {response.status_code}: "
                f"{redact_secrets(response.json_body)}"
            )
        choices = [
            _state_choice_from_record(record) for record in response.json_body.get("result", [])
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
        if response.status_code >= 400:
            raise ServiceNowApiError(
                f"ServiceNow API failed with status {response.status_code}: "
                f"{redact_secrets(response.json_body)}"
            )
        return [
            field
            for field in (
                _dictionary_field_from_record(record)
                for record in response.json_body.get("result", [])
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
        body = {
            "name": "rm_story",
            "element": element,
            "column_label": column_label,
            "internal_type": internal_type,
            "active": "true",
            "read_only": _bool_query_value(read_only),
        }
        if max_length is not None:
            body["max_length"] = str(max_length)

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
        if response.status_code >= 400:
            raise ServiceNowApiError(
                f"ServiceNow API failed with status {response.status_code}: "
                f"{redact_secrets(response.json_body)}"
            )
        result = response.json_body.get("result", {})
        return result if isinstance(result, dict) else {}

    def update_story_fields(self, story_sys_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        request = HttpRequest(
            method="PATCH",
            url=f"{self._settings.base_url}/api/now/table/rm_story/{story_sys_id}",
            headers={
                "Authorization": self._auth.authorization_header(),
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            body=fields,
        )
        response = self._transport.send(request)
        if response.status_code >= 400:
            raise ServiceNowApiError(
                f"ServiceNow API failed with status {response.status_code}: "
                f"{redact_secrets(response.json_body)}"
            )
        result = response.json_body.get("result", {})
        return result if isinstance(result, dict) else {}

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        existing_record = self.fetch_table_record(table=table, lookup=lookup)
        if existing_record is not None:
            sys_id = str(existing_record.get("sys_id", ""))
            operation = f"PATCH {table}"
            response = self._transport.send(
                HttpRequest(
                    method="PATCH",
                    url=f"{self._settings.base_url}/api/now/table/{table}/{sys_id}",
                    headers={
                        "Authorization": self._auth.authorization_header(),
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    body=fields,
                )
            )
        else:
            operation = f"POST {table}"
            response = self._transport.send(
                HttpRequest(
                    method="POST",
                    url=f"{self._settings.base_url}/api/now/table/{table}",
                    headers={
                        "Authorization": self._auth.authorization_header(),
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    body=fields,
                )
            )
        if response.status_code >= 400:
            raise ServiceNowApiError(
                f"ServiceNow API {operation} failed with status {response.status_code}: "
                f"{redact_secrets(response.json_body)}"
            )
        result = response.json_body.get("result", {})
        return result if isinstance(result, dict) else {}

    def fetch_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
    ) -> dict[str, Any] | None:
        query = "^".join(f"{key}={value}" for key, value in lookup.items())
        response = self._transport.send(
            HttpRequest(
                method="GET",
                url=f"{self._settings.base_url}/api/now/table/{table}",
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
        if response.status_code >= 400:
            raise ServiceNowApiError(
                f"ServiceNow API failed with status {response.status_code}: "
                f"{redact_secrets(response.json_body)}"
            )
        records = response.json_body.get("result", [])
        if isinstance(records, list) and records:
            record = records[0]
            return record if isinstance(record, dict) else None
        return None

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "^".join(f"{key}={value}" for key, value in lookup.items())
        params = {
            "sysparm_query": query,
            "sysparm_limit": str(limit),
        }
        if fields:
            params["sysparm_fields"] = ",".join(fields)
        response = self._transport.send(
            HttpRequest(
                method="GET",
                url=f"{self._settings.base_url}/api/now/table/{table}",
                headers={
                    "Authorization": self._auth.authorization_header(),
                    "Accept": "application/json",
                },
                params=params,
            )
        )
        if response.status_code >= 400:
            raise ServiceNowApiError(
                f"ServiceNow API failed with status {response.status_code}: "
                f"{redact_secrets(response.json_body)}"
            )
        records = response.json_body.get("result", [])
        if not isinstance(records, list):
            return []
        return [record for record in records if isinstance(record, dict)]

    def probe_cicd_update_set_endpoint(self, *, action: str) -> dict[str, Any]:
        if action not in {"create", "retrieve"}:
            raise ValueError(f"unsupported CI/CD Update Set probe action: {action}")
        response = self._transport.send(
            HttpRequest(
                method="POST",
                url=f"{self._settings.base_url}/api/sn_cicd/update_set/{action}",
                headers={
                    "Authorization": self._auth.authorization_header(),
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
        )
        body = dict(response.json_body)
        body["status_code"] = response.status_code
        return body

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
            "update_set_id": update_set_id,
            "auto_preview": _bool_query_value(auto_preview),
            "cleanup_retrieved": _bool_query_value(cleanup_retrieved),
        }
        if update_source_id:
            params["update_source_id"] = update_source_id
        if update_source_instance_id:
            params["update_source_instance_id"] = update_source_instance_id
        return self._send_cicd_update_set_request(
            method="POST",
            action="retrieve",
            params=params,
        )

    def preview_cicd_update_set(self, *, remote_update_set_id: str) -> dict[str, Any]:
        return self._send_cicd_update_set_request(
            method="POST",
            action=f"preview/{remote_update_set_id}",
        )

    def commit_cicd_update_set(
        self,
        *,
        remote_update_set_id: str,
        force_commit: bool = False,
    ) -> dict[str, Any]:
        return self._send_cicd_update_set_request(
            method="POST",
            action=f"commit/{remote_update_set_id}",
            body={"force_commit": _bool_query_value(force_commit)},
        )

    def fetch_cicd_progress(self, *, progress_id: str) -> dict[str, Any]:
        response = self._transport.send(
            HttpRequest(
                method="GET",
                url=f"{self._settings.base_url}/api/sn_cicd/progress/{progress_id}",
                headers={
                    "Authorization": self._auth.authorization_header(),
                    "Accept": "application/json",
                },
            )
        )
        return _servicenow_response_body_or_raise(
            response=response,
            context=f"GET sn_cicd/progress/{progress_id}",
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
                f"ServiceNow Update Set importer operation not found for service_id={service_id}"
            )
        operation_uri = str(records[0].get("operation_uri") or "")
        if not operation_uri.startswith("/api/"):
            raise ServiceNowApiError(
                "ServiceNow Update Set importer operation did not include operation_uri"
            )
        return operation_uri

    def _send_cicd_update_set_request(
        self,
        *,
        method: str,
        action: str,
        params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._transport.send(
            HttpRequest(
                method=method,
                url=f"{self._settings.base_url}/api/sn_cicd/update_set/{action}",
                headers={
                    "Authorization": self._auth.authorization_header(),
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                params=params or {},
                body=body or {},
            )
        )
        return _servicenow_response_body_or_raise(
            response=response,
            context=f"{method} sn_cicd/update_set/{action}",
        )

    def attach_story_file(
        self,
        story_sys_id: str,
        *,
        file_path: Path,
        file_name: str,
        content_type: str,
    ) -> dict[str, Any]:
        request = HttpRequest(
            method="POST",
            url=f"{self._settings.base_url}/api/now/attachment/file",
            headers={
                "Authorization": self._auth.authorization_header(),
                "Accept": "application/json",
                "Content-Type": content_type,
            },
            params={
                "table_name": "rm_story",
                "table_sys_id": story_sys_id,
                "file_name": file_name,
            },
            body_bytes=file_path.read_bytes(),
        )
        response = self._transport.send(request)
        if response.status_code >= 400:
            raise ServiceNowApiError(
                f"ServiceNow API failed with status {response.status_code}: "
                f"{redact_secrets(response.json_body)}"
            )
        result = response.json_body.get("result", {})
        return result if isinstance(result, dict) else {}


def load_dotenv_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "" or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


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
    if isinstance(value, dict):
        return {
            key: "***REDACTED***" if str(key).lower() in SENSITIVE_KEYS else redact_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    return value


def _story_from_record(record: dict[str, Any]) -> Story:
    return Story(
        sys_id=str(record["sys_id"]),
        number=str(record["number"]),
        short_description=str(record["short_description"]),
        description=str(record.get("description") or record["short_description"]),
        acceptance_criteria=_optional_text(record.get("acceptance_criteria")),
        story_points=float(record.get("story_points") or 0),
        priority=int(record.get("priority") or 5),
        state=str(record["state"]),
        data_classification=DataClassification.PUBLIC,
        additional_context={
            key: str(record[key])
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


def _state_choice_from_record(record: dict[str, Any]) -> StoryStateChoice:
    return StoryStateChoice(
        label=str(record["label"]),
        value=str(record["value"]),
        sequence=int(record.get("sequence") or 0),
        inactive=_truthy(record.get("inactive")),
    )


def _dictionary_field_from_record(record: dict[str, Any]) -> StoryDictionaryField:
    return StoryDictionaryField(
        element=str(record["element"]),
        column_label=str(record.get("column_label") or record["element"]),
        internal_type=str(record.get("internal_type") or ""),
        active=_truthy(record.get("active", True)),
        read_only=_truthy(record.get("read_only")),
    )


def _url_with_params(url: str, params: dict[str, str]) -> str:
    if not params:
        return url
    return f"{url}?{urllib.parse.urlencode(params)}"


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text.strip() else None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}
