"""Safe public-content fetching with SSRF, redirect, MIME and PDF limits."""

from __future__ import annotations

import hashlib
import ipaddress
import io
import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from pypdf import PdfReader

from .http import USER_AGENT
from .types import WorkflowFailure


ALLOWED_HOST_SUFFIXES = (
    "arxiv.org",
    "semanticscholar.org",
    "aclweb.org",
    "aclanthology.org",
    "openreview.net",
    "proceedings.neurips.cc",
    "proceedings.mlr.press",
    "acm.org",
    "ieee.org",
    "springer.com",
    "springeropen.com",
    "nature.com",
)
MAX_REDIRECTS = 3


@dataclass(frozen=True)
class PublicContent:
    final_url: str
    content_type: str
    sha256: str
    size_bytes: int
    page_count: int | None
    text: str


def _host_allowed(hostname: str, allowed_suffixes: tuple[str, ...]) -> bool:
    host = hostname.rstrip(".").lower()
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in allowed_suffixes)


def validate_public_url(
    url: str,
    *,
    allowed_suffixes: tuple[str, ...] = ALLOWED_HOST_SUFFIXES,
    resolver: Any = socket.getaddrinfo,
) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise WorkflowFailure("unsafe_url", "Only credential-free HTTPS content URLs are allowed")
    if parsed.port not in (None, 443):
        raise WorkflowFailure("unsafe_url", "Non-HTTPS ports are not allowed")
    if not _host_allowed(parsed.hostname, allowed_suffixes):
        raise WorkflowFailure("hostname_not_allowed", "Content hostname is not on the academic allowlist")
    try:
        addresses = resolver(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise WorkflowFailure("dns_failure", "Content hostname could not be resolved") from exc
    if not addresses:
        raise WorkflowFailure("dns_failure", "Content hostname returned no addresses")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise WorkflowFailure("ssrf_blocked", "Content URL resolves to a non-public network")
    return url


def _mime(response: httpx.Response) -> str:
    return response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()


class SafeContentFetcher:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        maximum_bytes: int = 20 * 1024 * 1024,
        maximum_pages: int = 80,
        allowed_suffixes: tuple[str, ...] = ALLOWED_HOST_SUFFIXES,
        resolver: Any = socket.getaddrinfo,
    ) -> None:
        self.client = client or httpx.Client(timeout=httpx.Timeout(20), headers={"User-Agent": USER_AGENT}, follow_redirects=False)
        self.maximum_bytes = maximum_bytes
        self.maximum_pages = maximum_pages
        self.allowed_suffixes = allowed_suffixes
        self.resolver = resolver

    def fetch(self, url: str) -> PublicContent:
        current = validate_public_url(url, allowed_suffixes=self.allowed_suffixes, resolver=self.resolver)
        response: httpx.Response | None = None
        for _ in range(MAX_REDIRECTS + 1):
            response = self.client.get(current)
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location:
                    raise WorkflowFailure("redirect_missing_location", "Redirect omitted Location")
                current = validate_public_url(urljoin(current, location), allowed_suffixes=self.allowed_suffixes, resolver=self.resolver)
                continue
            if response.status_code >= 400:
                raise WorkflowFailure("content_http_error", f"Content returned HTTP {response.status_code}")
            break
        else:
            raise WorkflowFailure("redirect_limit", "Content exceeded the redirect limit")
        assert response is not None
        declared = response.headers.get("Content-Length")
        if declared and declared.isdigit() and int(declared) > self.maximum_bytes:
            raise WorkflowFailure("content_size_limit", "Content-Length exceeds the local limit")
        body = response.content
        if len(body) > self.maximum_bytes:
            raise WorkflowFailure("content_size_limit", "Downloaded content exceeds the local limit")
        mime = _mime(response)
        digest = hashlib.sha256(body).hexdigest()
        if mime == "application/pdf" or body.startswith(b"%PDF-"):
            if mime != "application/pdf" or not body.startswith(b"%PDF-"):
                raise WorkflowFailure("mime_signature_mismatch", "PDF MIME and signature disagree")
            try:
                reader = PdfReader(io.BytesIO(body))
            except Exception as exc:
                raise WorkflowFailure("pdf_parsing", "Public PDF could not be parsed") from exc
            if len(reader.pages) > self.maximum_pages:
                raise WorkflowFailure("pdf_page_limit", "Public PDF exceeds the local page limit")
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
            return PublicContent(current, "pdf", digest, len(body), len(reader.pages), text)
        if mime not in ("text/html", "text/plain"):
            raise WorkflowFailure("unsupported_mime", f"Unsupported content MIME: {mime or 'missing'}")
        return PublicContent(current, "html", digest, len(body), None, body.decode(response.encoding or "utf-8", errors="replace"))
