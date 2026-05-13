from jedi_devproject.fulfillment import FulfillmentRoute, determine_fulfillment_route
from jedi_devproject.models import CandidateStatus, UpdateSetCandidate


def _candidate(*, confidence: float, risk_score: float) -> UpdateSetCandidate:
    return UpdateSetCandidate(
        story_number="STRY0010013",
        name="UPD_STRY0010013_AI_Review_Notes_Field",
        eligibility_decision="eligible",
        eligibility_reasons=["story type allowed: dictionary_form"],
        confidence=confidence,
        risk_score=risk_score,
        status=CandidateStatus.READY_FOR_REVIEW,
    )


def test_dictionary_form_profile_routes_to_automated_development_fulfillment() -> None:
    route = determine_fulfillment_route(_candidate(confidence=0.82, risk_score=0.12))

    assert route is FulfillmentRoute.AUTOMATED_DEVELOPMENT


def test_low_confidence_candidate_stays_in_human_review() -> None:
    route = determine_fulfillment_route(_candidate(confidence=0.79, risk_score=0.35))

    assert route is FulfillmentRoute.HUMAN_REVIEW


def test_high_risk_candidate_stays_in_human_review() -> None:
    route = determine_fulfillment_route(_candidate(confidence=0.82, risk_score=0.41))

    assert route is FulfillmentRoute.HUMAN_REVIEW


def test_non_reviewable_candidate_is_not_routed_to_automation() -> None:
    candidate = _candidate(confidence=0.95, risk_score=0.1)
    candidate = candidate.model_copy(update={"status": CandidateStatus.MANUAL_BUILD})

    assert determine_fulfillment_route(candidate) is FulfillmentRoute.HUMAN_REVIEW
