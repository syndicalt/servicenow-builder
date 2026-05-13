from pathlib import Path

from jedi_devproject.models import DataClassification, ProviderStatus
from jedi_devproject.security_defaults import default_provider_policies


def test_default_provider_policies_do_not_enable_public_model_endpoints() -> None:
    policies = default_provider_policies()

    assert policies
    assert all(policy.deployment_boundary != "public-commercial" for policy in policies)
    assert all("public" not in policy.provider_id for policy in policies)


def test_rules_only_default_allows_public_classification_without_external_model() -> None:
    policies = default_provider_policies()
    rules_only = next(policy for policy in policies if policy.provider_id == "rules-only")

    assert rules_only.status is ProviderStatus.APPROVED
    assert rules_only.allows(task="classify_story", data_class=DataClassification.PUBLIC)
    assert not rules_only.allows(task="generate_candidate", data_class=DataClassification.CUI)


def test_generated_artifacts_are_ignored_by_default() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "artifacts/" in gitignore
