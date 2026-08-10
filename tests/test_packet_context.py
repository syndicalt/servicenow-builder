import math
from typing import Any

import pytest

from jedi_devproject.instance_discovery import ServiceNowSurfaceContext
from jedi_devproject.packet_context import (
    _context_model_payload,
    _ensure_context_dto_payload_json_safe,
)


def test_context_model_payload_rejects_non_finite_dto_without_payload_leak() -> None:
    surface_context = ServiceNowSurfaceContext.model_construct(
        surface="form_layout",
        source_table="sys_ui_element",
        required=True,
        records=[],
        evidence=["client_secret=do-not-echo-this"],
        confidence=math.nan,
        citations=[],
    )

    with pytest.raises(ValueError) as exc_info:
        _context_model_payload(
            surface_context,
            diagnostic="context dossier DTO payload contains non-finite numeric values",
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "context dossier DTO payload contains non-finite numeric values"
    assert "confidence" not in diagnostic
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_context_model_payload_rejects_non_json_dto_without_payload_leak() -> None:
    class SecretBearingObject:
        def __str__(self) -> str:
            return "client_secret=context-secret"

    surface_context = ServiceNowSurfaceContext.model_construct(
        surface="form_layout",
        source_table="sys_ui_element",
        required=True,
        records=[],
        evidence=["client_secret=do-not-echo-this"],
        confidence=0.95,
        citations=[SecretBearingObject()],
    )

    with pytest.raises(ValueError) as exc_info:
        _context_model_payload(
            surface_context,
            diagnostic="context dossier DTO payload contains non-JSON values",
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "context dossier DTO payload contains non-JSON values"
    assert "citations" not in diagnostic
    assert "SecretBearingObject" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "context-secret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_context_model_payload_rejects_string_subclass_dto_without_payload_leak() -> None:
    class HostileContextText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=context-str-secret")

    surface_context = ServiceNowSurfaceContext.model_construct(
        surface="form_layout",
        source_table="sys_ui_element",
        required=True,
        records=[],
        evidence=[
            "client_secret=do-not-echo-this",
            HostileContextText("context-secret"),
        ],
        confidence=0.95,
        citations=[],
    )

    with pytest.raises(ValueError) as exc_info:
        _context_model_payload(
            surface_context,
            diagnostic="context dossier DTO payload contains non-JSON values",
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "context dossier DTO payload contains non-JSON values"
    assert "evidence" not in diagnostic
    assert "HostileContextText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "context-secret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_context_dto_payload_rejects_scalar_subclasses_without_payload_leak() -> None:
    class HostileContextOrder(int):
        def __str__(self) -> str:
            raise AssertionError("client_secret=context-int-subclass-secret")

    class HostileContextScore(float):
        def __str__(self) -> str:
            raise AssertionError("client_secret=context-float-subclass-secret")

    for value in (HostileContextOrder(3), HostileContextScore(0.95)):
        with pytest.raises(TypeError) as exc_info:
            _ensure_context_dto_payload_json_safe(value)

        diagnostic = str(exc_info.value)
        assert diagnostic == "non-JSON context dossier DTO payload value"
        assert "HostileContext" not in diagnostic
        assert "client_secret" not in diagnostic
        assert "subclass-secret" not in diagnostic


def test_context_dto_payload_rejects_container_subclasses_without_payload_leak() -> None:
    class HostileContextDict(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=context-dict-subclass-secret")

    class HostileContextList(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=context-list-subclass-secret")

    class HostileContextTuple(tuple[Any, ...]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=context-tuple-subclass-secret")

    for value in (
        HostileContextDict({"secret": "hidden dict"}),
        HostileContextList(["hidden list"]),
        HostileContextTuple(("hidden tuple",)),
    ):
        with pytest.raises(TypeError) as exc_info:
            _ensure_context_dto_payload_json_safe(value)

        diagnostic = str(exc_info.value)
        assert diagnostic == "non-JSON context dossier DTO payload value"
        assert "HostileContext" not in diagnostic
        assert "client_secret" not in diagnostic
        assert "subclass-secret" not in diagnostic
        assert "hidden" not in diagnostic
