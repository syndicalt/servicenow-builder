from jedi_devproject.context_escalation import plan_context_escalation


class _HostileContextText(str):
    def __str__(self) -> str:
        raise AssertionError("client_secret=context-string-secret")


class _HostileContextValue:
    def __str__(self) -> str:
        raise AssertionError("client_secret=context-object-secret")


def test_context_escalation_retrieves_when_live_instance_context_is_missing() -> None:
    plan = plan_context_escalation(
        {
            "status": "needs_retrieval",
            "score": 0.35,
            "missing_context": ["live_instance_context"],
            "evidence": [],
        }
    )

    assert plan.action == "retrieve_live_instance_context"
    assert plan.should_call_model is False
    assert plan.should_retrieve is True
    assert plan.reasons == ["live_instance_context_missing"]


def test_context_escalation_blocks_model_when_retrieved_context_is_insufficient() -> None:
    plan = plan_context_escalation(
        {
            "status": "insufficient",
            "score": 0.2,
            "missing_context": ["form_sections"],
            "evidence": ["sys_dictionary:incident"],
        }
    )

    assert plan.action == "manual_review"
    assert plan.should_call_model is False
    assert plan.should_retrieve is False
    assert plan.reasons == ["context_insufficient:form_sections"]


def test_context_escalation_allows_model_when_context_is_sufficient() -> None:
    plan = plan_context_escalation(
        {
            "status": "sufficient",
            "score": 0.95,
            "missing_context": [],
            "evidence": ["sys_dictionary:incident", "sys_ui_section:incident"],
        }
    )

    assert plan.action == "proceed_to_model"
    assert plan.should_call_model is True
    assert plan.should_retrieve is False
    assert plan.reasons == []


def test_context_escalation_fails_closed_for_string_subclass_status() -> None:
    plan = plan_context_escalation(
        {
            "status": _HostileContextText("sufficient"),
            "missing_context": ["form_sections"],
        }
    )

    assert plan.action == "manual_review"
    assert plan.should_call_model is False
    assert plan.should_retrieve is False
    assert plan.reasons == ["context_insufficient:form_sections"]


def test_context_escalation_skips_unsafe_missing_context_without_coercion() -> None:
    plan = plan_context_escalation(
        {
            "status": "insufficient",
            "missing_context": [
                _HostileContextText("form_sections"),
                _HostileContextValue(),
                "form_layout",
            ],
        }
    )

    assert plan.action == "manual_review"
    assert plan.should_call_model is False
    assert plan.reasons == ["context_insufficient:form_layout"]
