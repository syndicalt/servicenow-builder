"""Shared builders for the hand-crafted customer-update XML emitted by generation modules.

Output preserves the previous inline f-string payloads: text and attribute values are
escaped with XML-aware entities, attributes render in call order, and pre-rendered parts
are joined without separators. Values containing characters illegal in XML 1.0 are
rejected before rendering so generation modules cannot emit malformed payloads.
"""

from __future__ import annotations

import re
from xml.sax.saxutils import escape as _xml_escape

XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>'
SYS_SCOPE_GLOBAL = '<sys_scope display_value="Global">global</sys_scope>'

# XML 1.0 (5th edition) allowed characters:
#   #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
# Everything else is rejected, including most C0/C1 controls, surrogates, and
# the noncharacters at the end of each plane.
_INVALID_XML_CHAR = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F\uD800-\uDFFF\uFFFE\uFFFF]"
)


def _validate_xml_characters(value: str) -> None:
    """Raise ValueError if *value* contains characters that are illegal in XML 1.0."""
    match = _INVALID_XML_CHAR.search(value)
    if match is not None:
        char = match.group()
        raise ValueError(
            f"Invalid XML character at index {match.start()}: U+{ord(char):04X}"
        )


def _escape_xml(value: str) -> str:
    """Escape XML text/attribute content and reject invalid characters up front."""
    _validate_xml_characters(value)
    return _xml_escape(
        value,
        entities={"'": "&#x27;", '"': "&quot;"},
    )


def text_element(name: str, value: str, /, **attributes: str) -> str:
    return f"<{name}{_render_attributes(attributes)}>{_escape_xml(value)}</{name}>"


def bool_element(name: str, value: bool) -> str:
    return f"<{name}>{'true' if value else 'false'}</{name}>"


def container_element(name: str, /, *parts: str, **attributes: str) -> str:
    return f"<{name}{_render_attributes(attributes)}>{''.join(parts)}</{name}>"


def record_update(*parts: str, table: str | None = None) -> str:
    body = "".join(parts)
    if table is None:
        return f"{XML_DECLARATION}<record_update>{body}</record_update>"
    return f'{XML_DECLARATION}<record_update table="{_escape_xml(table)}">{body}</record_update>'


def cdata(value: str) -> str:
    _validate_xml_characters(value)
    return f"<![CDATA[{value.replace(']]>', ']]]]><![CDATA[>')}]]>"


def reference_qualifier_elements(*, reference_table: str, reference_qualifier: str) -> str:
    return (
        text_element("reference", reference_table)
        + text_element("reference_qual", reference_qualifier)
        + text_element("reference_qual_condition", reference_qualifier)
        + text_element("use_reference_qualifier", "simple" if reference_qualifier else "")
    )


def _render_attributes(attributes: dict[str, str]) -> str:
    return "".join(f' {key}="{_escape_xml(value)}"' for key, value in attributes.items())
