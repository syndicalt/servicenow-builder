"""Classification of story text into requested capabilities and detail checks."""

from __future__ import annotations

import re

from jedi_devproject.capabilities import Capability
from jedi_devproject.story_features import (
    _field_label,
    _field_name,
    _field_type,
    _form_section_names,
    _is_cmdb_ire_analysis_request,
    _record_producer_field_mappings,
    _target_table,
)


def _is_catalog_ui_policy_request(text: str) -> bool:
    return "catalog ui policy" in text or "catalog ui policies" in text


def _is_record_producer_request(text: str) -> bool:
    return "record producer" in text


def _is_catalog_item_creation_request(text: str) -> bool:
    """A catalog item request: drives request fulfillment, not record creation."""
    return "catalog item" in text


def _is_catalog_client_script_request(text: str) -> bool:
    return "catalog client script" in text or "catalog client scripts" in text


def _requested_capabilities(text: str) -> set[Capability]:
    capabilities: set[Capability] = set()
    if _is_catalog_ui_policy_request(text):
        capabilities.add(Capability.CATALOG_UI_POLICY_GENERATE)
    if _is_catalog_client_script_request(text):
        capabilities.add(Capability.CATALOG_CLIENT_SCRIPT_GENERATE)
    if _is_record_producer_request(text):
        capabilities.add(Capability.RECORD_PRODUCER_CREATE)
    if _is_dictionary_form_request(text):
        capabilities.update(
            {
                Capability.DICTIONARY_FIELD_CREATE,
                Capability.FIELD_LABEL_CREATE,
                Capability.FORM_LAYOUT_PLACE_FIELD,
            }
        )
    if _is_form_section_request(text):
        capabilities.add(Capability.FORM_SECTION_REMOVE)
    if _is_cmdb_ire_analysis_request(text):
        capabilities.update({Capability.CMDB_IRE_ANALYZE, Capability.CMDB_IRE_GENERATE})
    if "acl" in text or "only admins" in text or "only admin" in text:
        capabilities.add(Capability.ACL_MODIFY)
    if "workflow" in text or "flow designer" in text:
        capabilities.add(Capability.FLOW_MODIFY)
    if _is_business_rule_generation_request(text):
        capabilities.add(Capability.BUSINESS_RULE_GENERATE)
    elif "business rule" in text or "server script" in text:
        capabilities.add(Capability.BUSINESS_RULE_ANALYZE)
    if _is_client_script_generation_request(text):
        capabilities.add(Capability.CLIENT_SCRIPT_GENERATE)
    elif "client script" in text or "onchange" in text or "onsubmit" in text or "onload" in text:
        capabilities.add(Capability.CLIENT_SCRIPT_ANALYZE)
    if _is_script_include_generation_request(text):
        capabilities.add(Capability.SCRIPT_INCLUDE_GENERATE)
    elif "script include" in text:
        capabilities.add(Capability.SCRIPT_INCLUDE_ANALYZE)
    if _is_ui_policy_generation_request(text):
        capabilities.add(Capability.UI_POLICY_GENERATE)
    if "migrat" in text:
        capabilities.add(Capability.DATA_MIGRATION)
    if _is_integration_request(text):
        capabilities.add(Capability.INTEGRATION_MODIFY)
    if not capabilities:
        capabilities.add(Capability.UNKNOWN)
    return capabilities


def _missing_details(text: str) -> list[str]:
    missing: list[str] = []
    if _is_dictionary_form_request(text) and _target_table(text) is None:
        missing.append("target table")
    if (
        _is_dictionary_form_request(text)
        and _field_label(text) is None
        and _field_name(text) is None
    ):
        missing.append("field label or field name")
    if _is_dictionary_form_request(text) and _field_type(text) is None:
        missing.append("field type")
    if _is_form_section_request(text):
        if _target_table(text) is None:
            missing.append("target table")
        if not _form_section_names(text):
            missing.append("sections")
    if _is_record_producer_request(text):
        missing.extend(_missing_record_producer_details(text))
    if _is_business_rule_generation_request(text):
        missing.extend(_missing_business_rule_generation_details(text))
    elif _is_business_rule_request(text) and _target_table(text) is None:
        missing.append("target table")
    if _is_client_script_generation_request(text):
        missing.extend(_missing_client_script_generation_details(text))
    elif _is_client_script_request(text) and _target_table(text) is None:
        missing.append("target table")
    if _is_script_include_generation_request(text):
        missing.extend(_missing_script_include_generation_details(text))
    if _is_ui_policy_generation_request(text):
        missing.extend(_missing_ui_policy_generation_details(text))
    return missing


def _missing_record_producer_details(text: str) -> list[str]:
    mappings = _record_producer_field_mappings(text)
    checks = [
        ("target table", _target_table(text) is not None),
        ("variables", bool(mappings) or "variables:" in text),
        ("variable field mappings", bool(mappings)),
    ]
    return [label for label, present in checks if not present]


def _is_business_rule_request(text: str) -> bool:
    return "business rule" in text or "server script" in text


def _is_business_rule_generation_request(text: str) -> bool:
    if not _is_business_rule_request(text):
        return False
    if any(token in text for token in ["analyze", "analysis", "existing", "determine whether"]):
        return False
    return any(token in text for token in ["create", "add", "generate", "implement", "build"])


def _missing_business_rule_generation_details(text: str) -> list[str]:
    checks = [
        ("target table", _target_table(text) is not None),
        ("trigger timing", "before" in text or "after" in text),
        ("trigger operations", "insert" in text or "update" in text),
        ("explicit condition", "condition:" in text or "when " in text),
        ("expected behavior", "expected behavior:" in text or "set " in text),
        ("fields read", _has_business_rule_fields_read_detail(text)),
        ("fields written", _has_business_rule_fields_written_detail(text)),
    ]
    return [label for label, present in checks if not present]


def _has_business_rule_fields_read_detail(text: str) -> bool:
    return "fields read:" in text or (
        ("condition:" in text or "when " in text)
        and any(field in text for field in _mentioned_service_now_fields(text))
    )


def _has_business_rule_fields_written_detail(text: str) -> bool:
    return (
        "fields written:" in text
        or re.search(r"\bwrites? only [a-zA-Z0-9_]+", text) is not None
        or re.search(r"\bset field [a-zA-Z0-9_]+", text) is not None
        or re.search(r"\bset [a-zA-Z0-9_]+ to\b", text) is not None
    )


def _mentioned_service_now_fields(text: str) -> set[str]:
    field_pattern = r"\b[a-z][a-z0-9]*_[a-z0-9_]+\b|\bcategory\b|\bstate\b|\bpriority\b"
    return set(re.findall(field_pattern, text))


def _business_rule_forbidden_details(text: str) -> list[str]:
    if not _is_business_rule_generation_request(text):
        return []
    forbidden_patterns = {
        "delete rules": ["delete rule", "delete business rule", "on delete"],
        "async/display rules": ["async", "display business rule"],
        "scheduled jobs": ["scheduled job", "schedule"],
        "outbound calls": ["rest", "soap", "endpoint", "api call", "http://", "https://"],
        "credentials": ["credential", "password", "token", "api key", "secret"],
        "cross-table writes": ["gliderecord", "another table", "other table", "cross-table"],
    }
    return [
        label
        for label, tokens in forbidden_patterns.items()
        if any(token in text for token in tokens)
    ]


def _is_client_script_request(text: str) -> bool:
    return "client script" in text or "onchange" in text or "onsubmit" in text or "onload" in text


def _is_client_script_generation_request(text: str) -> bool:
    if not _is_client_script_request(text):
        return False
    if any(token in text for token in ["analyze", "analysis", "existing", "determine whether"]):
        return False
    return any(token in text for token in ["create", "add", "generate", "implement", "build"])


def _missing_client_script_generation_details(text: str) -> list[str]:
    checks = [
        ("target table", _target_table(text) is not None),
        ("client script type", any(token in text for token in ["onchange", "onload", "onsubmit"])),
        ("explicit condition", "condition:" in text or "when " in text),
        ("expected behavior", "expected behavior:" in text or "show " in text or "set " in text),
        ("fields read", _has_field_detail(text, "read")),
        ("fields written", _has_field_detail(text, "written")),
    ]
    if "onchange" in text and _client_script_target_field(text) is None:
        checks.append(("target field", False))
    return [label for label, present in checks if not present]


def _has_field_detail(text: str, action: str) -> bool:
    return bool(
        re.search(rf"\bfields?\s+{action}\b", text)
        or re.search(rf"\bscript\s+{action}s?\b", text)
    )


def _client_script_forbidden_details(text: str) -> list[str]:
    if not _is_client_script_generation_request(text):
        return []
    forbidden_patterns = {
        "DOM manipulation outside g_form APIs": ["document.", "window.", "dom"],
        "browser storage": ["localstorage", "sessionstorage"],
        "external calls": ["fetch", "xmlhttprequest", "endpoint", "api call", "http://", "https://"],
        "GlideAjax dependency creation": ["glideajax"],
        "credentials": ["credential", "password", "token", "api key", "secret"],
    }
    return [
        label
        for label, tokens in forbidden_patterns.items()
        if any(token in text for token in tokens)
    ]


def _client_script_target_field(text: str) -> str | None:
    match = re.search(r"for the ([a-zA-Z0-9_]+) field", text)
    if match:
        return match.group(1).lower()
    match = re.search(r"onchange .*? ([a-zA-Z0-9_]+) field", text)
    if match:
        return match.group(1).lower()
    return None


def _is_integration_request(text: str) -> bool:
    return any(
        token in text
        for token in [
            "integrat",
            "rest api",
            "api call",
            "external api",
            "outbound api",
            "endpoint",
        ]
    )


def _is_script_include_generation_request(text: str) -> bool:
    if "script include" not in text:
        return False
    if any(token in text for token in ["analyze", "analysis", "existing", "determine whether"]):
        return False
    return any(token in text for token in ["create", "add", "generate", "implement", "build"])


def _is_ui_policy_generation_request(text: str) -> bool:
    if "ui policy" not in text and "ui policies" not in text:
        return False
    if any(token in text for token in ["analyze", "analysis", "existing", "determine whether"]):
        return False
    return any(token in text for token in ["create", "add", "generate", "implement", "build"])


def _missing_ui_policy_generation_details(text: str) -> list[str]:
    checks = [
        ("target table", _target_table(text) is not None),
        ("condition", "condition:" in text or "when " in text or "condition is" in text),
        (
            "expected behavior",
            "expected behavior:" in text
            or "mandatory" in text
            or "visible" in text
            or "read only" in text,
        ),
        ("fields read", "fields read:" in text or "category" in text),
        (
            "fields affected",
            "fields affected:" in text
            or "field affected:" in text
            or "actions:" in text
            or "assignment_group" in text
            or "assignment group" in text,
        ),
        (
            "reverse if false decision",
            "reverse if false:" in text
            or "reverse if false is enabled" in text
            or "condition is false" in text
            or "policy must reverse" in text,
        ),
    ]
    return [label for label, present in checks if not present]


def _ui_policy_forbidden_details(text: str) -> list[str]:
    if not _is_ui_policy_generation_request(text):
        return []
    forbidden_patterns = {
        "run scripts": ["run scripts: true", "run script: true", "advanced script"],
        "Client Script behavior": ["client script", "g_form", "glideajax"],
        "Business Rule creation": ["business rule"],
        "Script Include creation": ["script include"],
        "Flow creation": [" flow ", "flow designer"],
        "ACL changes": [" acl", " role"],
        "integration calls": ["rest", "soap", "endpoint", "api call", "http://", "https://"],
        "credentials": ["credential", "password", "token", "api key", "secret"],
        "cross-table behavior": ["another table", "other table", "cross-table"],
    }
    return [
        label
        for label, tokens in forbidden_patterns.items()
        if any(token in text for token in tokens)
    ]


def _missing_script_include_generation_details(text: str) -> list[str]:
    checks = [
        ("script include name", _script_include_name(text) is not None),
        ("scope", "scope" in text or "global" in text),
        ("client callable decision", "client callable:" in text or "not client callable" in text),
        ("expected behavior", "expected server-side behavior:" in text),
        ("tables read", "tables read:" in text),
        ("tables written", "tables written:" in text),
        ("fields read", "fields read:" in text),
        ("fields written", "fields written:" in text),
    ]
    return [label for label, present in checks if not present]


def _script_include_forbidden_details(text: str) -> list[str]:
    if not _is_script_include_generation_request(text):
        return []
    forbidden_patterns = {
        "client callable Script Includes": ["client callable: true"],
        "global privilege escalation": ["privilege escalation", "elevated privilege"],
        "cross-scope access changes": ["cross-scope", "cross scope"],
        "security changes": [" acl", " role", "system property"],
        "outbound calls": ["rest", "soap", "endpoint", "api call", "http://", "https://"],
        "credentials": ["credential", "password", "token", "api key", "secret"],
        "broad GlideRecord mutation": ["deleterecord", "deletemultiple", "updatemultiple"],
        "caller creation": ["business rule", "client script", "flow", "scheduled job"],
    }
    return [
        label
        for label, tokens in forbidden_patterns.items()
        if any(token in text for token in tokens)
    ]


def _script_include_name(text: str) -> str | None:
    match = re.search(r"script include named ([a-zA-Z][a-zA-Z0-9_]*)", text)
    if match:
        return match.group(1)
    return None


def _code_surface_capability(requested: set[Capability]) -> Capability | None:
    for capability in [
        Capability.BUSINESS_RULE_ANALYZE,
        Capability.CLIENT_SCRIPT_ANALYZE,
        Capability.SCRIPT_INCLUDE_ANALYZE,
    ]:
        if capability in requested:
            return capability
    return None


def _is_dictionary_form_request(text: str) -> bool:
    if (
        _is_business_rule_request(text)
        or _is_client_script_request(text)
        or "script include" in text
        or "ui policy" in text
        or "ui policies" in text
        or _is_record_producer_request(text)
        or _is_form_section_request(text)
    ):
        return False
    return ("field" in text or "column" in text) and re.search(r"\bform\b", text) is not None


def _is_form_section_request(text: str) -> bool:
    if _is_client_script_request(text) or "ui policy" in text or "ui policies" in text:
        return False
    form_surface = bool(
        re.search(
            r"\bform\s+layout\b|\bform\s+sections?\b|\bform\s+tabs?\b|\btabs?\b|\bsections?\b",
            text,
        )
    )
    removal_action = bool(
        re.search(
            r"\bhide\b|\bhidden\b|\bremove\b|\bremoved\b|\bnot\s+display\b|"
            r"\bwill\s+not\s+display\b|\bdo\s+not\s+display\b",
            text,
        )
    )
    return form_surface and removal_action
