"""Specialized retrieval (RAG) domains with bounded retrieval-result caching.

Caching policy: local, deterministic retrieval domains (ServiceNow platform,
instance metadata, project context, compliance) are served from a bounded LRU
cache keyed by domain, query, and a corpus fingerprint covering every indexed
document's source, content, and version — any corpus or query change misses.
Live public-web retrieval (``PublicWebRetriever``) and the
``PUBLIC_DOCUMENTATION`` domain are never cached: public web access is
fail-closed, allowlist-gated, and audit-sensitive, and a cached entry could
otherwise be served after an allowlist or access-config change revoked the
fetch that produced it. Excluding the domain entirely is the safer option
versus config-keyed caching, so every public-docs retrieval re-runs the full
allowlist and SSRF validation path.
"""

from __future__ import annotations

import re
from enum import StrEnum
from html import unescape
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pydantic import BaseModel, ConfigDict, Field, field_validator

from jedi_devproject.models import RetrievalCitation, stable_artifact_hash
from jedi_devproject.rag_cache import RetrievalCache, RetrievalCacheStats
from jedi_devproject.url_host_safety import is_non_public_hostname, normalize_hostname
from jedi_devproject.url_query_safety import (
    has_encoded_whitespace_or_control_character,
    has_whitespace_or_control_character,
    sensitive_query_keys,
)


class RetrievalBlocked(RuntimeError):
    """Raised when required retrieval context is unavailable."""


class PublicWebRetrievalBlocked(RetrievalBlocked):
    """Raised when live public documentation retrieval is unsafe or unavailable."""


class RagDomain(StrEnum):
    SERVICENOW_PLATFORM = "servicenow_platform"
    INSTANCE_METADATA = "instance_metadata"
    PROJECT_CONTEXT = "project_context"
    COMPLIANCE = "compliance"
    PUBLIC_DOCUMENTATION = "public_documentation"


class Document(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    domain: RagDomain
    source: str
    content: str
    version: str


class RetrievalResult(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    content: str
    citation: RetrievalCitation


class PublicWebAccessConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    allowed_domains: list[str] = Field(default_factory=list)
    timeout_seconds: float = Field(default=3.0, gt=0, le=30)
    max_response_bytes: int = Field(default=128 * 1024, gt=0, le=1024 * 1024)
    max_excerpt_chars: int = Field(default=4000, gt=0, le=20000)
    max_results: int = Field(default=3, gt=0, le=10)

    @field_validator("allowed_domains")
    @classmethod
    def normalize_allowed_domains(cls, value: list[str]) -> list[str]:
        return sorted({normalize_hostname(domain) for domain in value if domain.strip()})


class PublicWebResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    url: str
    status_code: int
    body: bytes


class PublicWebTransport(Protocol):
    def get(self, url: str, *, timeout_seconds: float, max_bytes: int) -> PublicWebResponse: ...


class _NoPublicWebRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Any,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        raise PublicWebRetrievalBlocked("public documentation redirects are not allowed")


class UrllibPublicWebTransport:
    @property
    def redirect_handler(self) -> HTTPRedirectHandler:
        return _NoPublicWebRedirectHandler()

    def get(self, url: str, *, timeout_seconds: float, max_bytes: int) -> PublicWebResponse:
        request = Request(url, headers={"User-Agent": "jedi-devproject-public-docs/1.0"})
        opener = build_opener(self.redirect_handler)
        try:
            with opener.open(request, timeout=timeout_seconds) as response:
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise PublicWebRetrievalBlocked(
                        "public documentation response exceeded max bytes"
                    )
                return PublicWebResponse(
                    url=response.geturl(),
                    status_code=int(response.status),
                    body=body,
                )
        except HTTPError as exc:
            raise PublicWebRetrievalBlocked(
                f"public documentation fetch failed with HTTP {exc.code}"
            ) from None
        except (TimeoutError, URLError):
            raise PublicWebRetrievalBlocked("public documentation fetch failed") from None


class PublicWebRetriever:
    def __init__(
        self,
        *,
        config: PublicWebAccessConfig,
        transport: PublicWebTransport | None = None,
    ) -> None:
        self._config = config
        self._transport = transport or UrllibPublicWebTransport()

    def retrieve(self, query: str, *, urls: list[str]) -> list[RetrievalResult]:
        results: list[RetrievalResult] = []
        for raw_url in urls[: self._config.max_results]:
            requested_url = _normalize_public_url(raw_url)
            _validate_public_url(
                requested_url,
                allowed_domains=self._config.allowed_domains,
            )
            response = self._transport.get(
                requested_url,
                timeout_seconds=self._config.timeout_seconds,
                max_bytes=self._config.max_response_bytes,
            )
            final_url = _normalize_public_url(response.url)
            if final_url != requested_url and _host(final_url) != _host(requested_url):
                raise PublicWebRetrievalBlocked(
                    "public documentation fetch redirected to a different host"
                )
            _validate_public_url(final_url, allowed_domains=self._config.allowed_domains)
            if response.status_code < 200 or response.status_code >= 300:
                raise PublicWebRetrievalBlocked(
                    f"public documentation fetch returned HTTP {response.status_code}"
                )
            excerpt = _extract_bounded_text(
                response.body,
                max_excerpt_chars=self._config.max_excerpt_chars,
            )
            if not excerpt:
                continue
            content_hash = stable_artifact_hash(
                {
                    "source": final_url,
                    "query": query,
                    "excerpt": excerpt,
                    "version": "live-public-web",
                }
            )
            results.append(
                RetrievalResult(
                    content=excerpt,
                    citation=RetrievalCitation(
                        source=f"public_web:{final_url}",
                        content_hash=content_hash,
                        confidence=0.75,
                        version="live-public-web",
                    ),
                )
            )
        return results


class LocalRagIndex:
    def __init__(self, *, domain: RagDomain, documents: list[Document]) -> None:
        self._domain = domain
        self._documents = [document for document in documents if document.domain is domain]
        self._fingerprint = stable_artifact_hash(
            {
                "domain": domain.value,
                "documents": [
                    {
                        "source": document.source,
                        "content": document.content,
                        "version": document.version,
                    }
                    for document in self._documents
                ],
            }
        )

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

    @property
    def documents(self) -> list[Document]:
        return list(self._documents)

    @property
    def fingerprint(self) -> str:
        return self._fingerprint


_CACHE_EXCLUDED_DOMAINS = frozenset({RagDomain.PUBLIC_DOCUMENTATION})


class SpecializedRags:
    def __init__(
        self,
        indexes: dict[RagDomain, LocalRagIndex],
        *,
        cache: RetrievalCache[RetrievalResult] | None = None,
        cache_enabled: bool = True,
    ) -> None:
        self._indexes = indexes
        if not cache_enabled:
            self._cache: RetrievalCache[RetrievalResult] | None = None
        elif cache is not None:
            self._cache = cache
        else:
            self._cache = RetrievalCache()

    @classmethod
    def from_documents(
        cls,
        documents: list[Document],
        *,
        cache: RetrievalCache[RetrievalResult] | None = None,
        cache_enabled: bool = True,
    ) -> SpecializedRags:
        return cls(
            indexes={
                domain: LocalRagIndex(domain=domain, documents=documents)
                for domain in RagDomain
            },
            cache=cache,
            cache_enabled=cache_enabled,
        )

    def with_documents(self, documents: list[Document]) -> SpecializedRags:
        existing_documents: list[Document] = []
        for index in self._indexes.values():
            existing_documents.extend(index.documents)
        return SpecializedRags.from_documents(
            [*existing_documents, *documents],
            cache_enabled=self._cache is not None,
        )

    @property
    def cache_stats(self) -> RetrievalCacheStats | None:
        return self._cache.stats if self._cache is not None else None

    def retrieve(self, domain: RagDomain, query: str) -> list[RetrievalResult]:
        index = self._indexes[domain]
        if self._cache is None or domain in _CACHE_EXCLUDED_DOMAINS:
            return index.retrieve(query)
        key = stable_artifact_hash(
            {
                "domain": domain.value,
                "query": query,
                "corpus_fingerprint": index.fingerprint,
            }
        )
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        results = index.retrieve(query)
        self._cache.put(key, results)
        return results

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


def _normalize_public_url(raw_url: str) -> str:
    if has_whitespace_or_control_character(raw_url):
        raise PublicWebRetrievalBlocked(
            "public documentation URL must not include whitespace or control characters"
        )
    if has_encoded_whitespace_or_control_character(raw_url):
        raise PublicWebRetrievalBlocked(
            "public documentation URL must not include encoded whitespace or control characters"
        )
    parsed = urlsplit(raw_url.strip())
    if parsed.scheme.lower() != "https":
        raise PublicWebRetrievalBlocked("public documentation URLs must use https")
    if not parsed.netloc:
        raise PublicWebRetrievalBlocked("public documentation URL must include a host")
    if parsed.username or parsed.password:
        raise PublicWebRetrievalBlocked("public documentation URL must not include credentials")
    if parsed.fragment:
        raise PublicWebRetrievalBlocked("public documentation URL must not include fragments")
    query_keys = sensitive_query_keys(parsed.query)
    if query_keys:
        raise PublicWebRetrievalBlocked(
            "public documentation URL must not include sensitive query parameters: "
            + ", ".join(query_keys)
        )
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path or "/",
            parsed.query,
            "",
        )
    )


def _validate_public_url(url: str, *, allowed_domains: list[str]) -> None:
    host = _host(url)
    if not _is_allowlisted_host(host, allowed_domains):
        raise PublicWebRetrievalBlocked(f"public documentation host is not allowlisted: {host}")
    if _is_private_or_loopback_host(host):
        raise PublicWebRetrievalBlocked("public documentation host is private or loopback")


def _host(url: str) -> str:
    return normalize_hostname(urlsplit(url).hostname or "")


def _is_allowlisted_host(host: str, allowed_domains: list[str]) -> bool:
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)


def _is_private_or_loopback_host(host: str) -> bool:
    return is_non_public_hostname(host)


def _extract_bounded_text(body: bytes, *, max_excerpt_chars: int) -> str:
    text = body.decode("utf-8", errors="replace")
    text = re.sub(
        r"(?is)<(script|style|noscript)[^>]*>.*?</\1>",
        " ",
        text,
    )
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_excerpt_chars]
