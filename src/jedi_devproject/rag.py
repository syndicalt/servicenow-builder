from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from jedi_devproject.models import RetrievalCitation, stable_artifact_hash


class RetrievalBlocked(RuntimeError):
    """Raised when required retrieval context is unavailable."""


class RagDomain(StrEnum):
    SERVICENOW_PLATFORM = "servicenow_platform"
    INSTANCE_METADATA = "instance_metadata"
    PROJECT_CONTEXT = "project_context"
    COMPLIANCE = "compliance"


class Document(BaseModel):
    domain: RagDomain
    source: str
    content: str
    version: str


class RetrievalResult(BaseModel):
    content: str
    citation: RetrievalCitation


class LocalRagIndex:
    def __init__(self, *, domain: RagDomain, documents: list[Document]) -> None:
        self._domain = domain
        self._documents = [document for document in documents if document.domain is domain]

    def retrieve(self, query: str) -> list[RetrievalResult]:
        query_terms = _terms(query)
        results: list[RetrievalResult] = []
        for document in self._documents:
            document_terms = _terms(document.content)
            if not query_terms.intersection(document_terms):
                continue

            content_hash = stable_artifact_hash(
                {
                    "domain": document.domain.value,
                    "source": document.source,
                    "content": document.content,
                    "version": document.version,
                }
            )
            results.append(
                RetrievalResult(
                    content=document.content,
                    citation=RetrievalCitation(
                        source=document.source,
                        content_hash=content_hash,
                        confidence=1.0,
                        version=document.version,
                    ),
                )
            )
        return results


class SpecializedRags:
    def __init__(self, indexes: dict[RagDomain, LocalRagIndex]) -> None:
        self._indexes = indexes

    @classmethod
    def from_documents(cls, documents: list[Document]) -> SpecializedRags:
        return cls(
            indexes={
                domain: LocalRagIndex(domain=domain, documents=documents)
                for domain in RagDomain
            }
        )

    def retrieve(self, domain: RagDomain, query: str) -> list[RetrievalResult]:
        return self._indexes[domain].retrieve(query)

    def retrieve_required_context(self, query: str) -> dict[RagDomain, list[RetrievalResult]]:
        context = {domain: self.retrieve(domain, query) for domain in RagDomain}
        if not context[RagDomain.COMPLIANCE]:
            raise RetrievalBlocked("missing compliance context")
        return context


def cache_key(
    *,
    domain: RagDomain,
    query: str,
    source_hash: str,
    prompt_version: str,
    schema_version: str,
) -> str:
    return "|".join([domain.value, query, source_hash, prompt_version, schema_version])


def _terms(text: str) -> set[str]:
    return {term.strip(".,:;()[]").lower() for term in text.split() if term.strip(".,:;()[]")}
