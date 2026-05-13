from __future__ import annotations

from jedi_devproject.models import DataClassification, ProviderPolicy, ProviderStatus


def default_provider_policies() -> list[ProviderPolicy]:
    return [
        ProviderPolicy(
            provider_id="rules-only",
            deployment_boundary="local-controlled",
            authorization_level="no-external-model",
            allowed_data_classes={DataClassification.PUBLIC},
            allowed_tasks={"classify_story"},
            max_context_policy="no model context",
            retention_policy="no external retention",
            status=ProviderStatus.APPROVED,
        )
    ]
