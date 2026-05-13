from __future__ import annotations

from enum import StrEnum

from jedi_devproject.models import CandidateStatus, UpdateSetCandidate


class FulfillmentRoute(StrEnum):
    AUTOMATED_DEVELOPMENT = "automated_development"
    HUMAN_REVIEW = "human_review"


AUTOMATED_DEVELOPMENT_MIN_CONFIDENCE = 0.80
AUTOMATED_DEVELOPMENT_MAX_RISK = 0.40


def determine_fulfillment_route(candidate: UpdateSetCandidate) -> FulfillmentRoute:
    if candidate.status is not CandidateStatus.READY_FOR_REVIEW:
        return FulfillmentRoute.HUMAN_REVIEW

    if (
        candidate.confidence >= AUTOMATED_DEVELOPMENT_MIN_CONFIDENCE
        and candidate.risk_score <= AUTOMATED_DEVELOPMENT_MAX_RISK
    ):
        return FulfillmentRoute.AUTOMATED_DEVELOPMENT

    return FulfillmentRoute.HUMAN_REVIEW
