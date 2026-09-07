"""SparkleScore API adapter (Principle 14)."""

import logging
import os
from typing import Any

import httpx

from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.scoring.backend import ScoringBackend

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 20.0


def _listing_score_request(listing: CanonicalListing | dict[str, Any], tenant_id: str) -> dict[str, Any]:
    if isinstance(listing, CanonicalListing):
        if not listing.cert_number:
            raise ValueError(f"Listing {listing.listing_id} has no cert for SparkleScore scoring")
        body = {
            "cert_number": listing.cert_number,
            "cert_lab": listing.cert_lab,
            "price": listing.price,
            "diamond_type": listing.diamond_type,
            "country_code": "us" if tenant_id.endswith("-us") else tenant_id.split("-")[-1],
            "site_id": tenant_id.split("-")[0],
        }
    else:
        body = dict(listing)
        if not body.get("cert_number"):
            raise ValueError("SparkleScore scoring requires cert_number")
    return {key: value for key, value in body.items() if value is not None}


class SparkleScoreClient(ScoringBackend):
    """Calls SparkleScore POST /api/v1/score per stone."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._base_url = (base_url or os.environ.get("SPARKLESCORE_API_URL", "")).rstrip("/")
        self._api_key = api_key or os.environ.get("SPARKLESCORE_API_KEY")
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    def _score_one(self, body: dict[str, Any]) -> dict[str, Any]:
        if not self._base_url:
            raise RuntimeError("SPARKLESCORE_API_URL is not configured")
        url = f"{self._base_url}/api/v1/score"
        response = httpx.post(url, json=body, headers=self._headers(), timeout=self._timeout)
        response.raise_for_status()
        payload = response.json()
        return {
            "composite": float(payload["composite"]),
            "pillars": payload.get("pillars") or {},
            "scoring_backend": "sparklescore",
            "raw": payload,
        }

    def score_listing(self, listing: CanonicalListing | dict[str, Any], tenant_id: str) -> dict[str, Any]:
        body = _listing_score_request(listing, tenant_id)
        result = self._score_one(body)
        if isinstance(listing, CanonicalListing):
            return {"listing": listing, **result}
        return {**listing, **result}

    def score_candidates(
        self,
        tenant_id: str,
        anchor: dict[str, Any] | None,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        scored = []
        for candidate in candidates:
            listing = candidate.get("listing") if isinstance(candidate, dict) else candidate
            result = self.score_listing(listing, tenant_id)
            scored.append({**candidate, **result})
        return scored

    def score_anchor(self, anchor: dict[str, Any], tenant_id: str) -> dict[str, Any]:
        if anchor.get("cert_number"):
            return self._score_one(_listing_score_request(anchor, tenant_id))
        raise ValueError("SparkleScore anchor requires cert_number; use listing_id or cert anchor")
