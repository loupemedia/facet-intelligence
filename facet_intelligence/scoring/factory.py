"""Scoring backend factory."""

from config.scoring_backends import SPARKLESCORE, VANILLA, resolve_backend
from facet_intelligence.scoring.backend import ScoringBackend
from facet_intelligence.scoring.sparklescore_client import SparkleScoreClient
from facet_intelligence.scoring.vanilla import VanillaScorer

__all__ = [
    "get_scoring_backend",
]


def get_scoring_backend(tenant_id: str, requested: str | None, tenant_default: str) -> ScoringBackend:
    backend_name = resolve_backend(tenant_id, requested, tenant_default)
    if backend_name == SPARKLESCORE:
        return SparkleScoreClient()
    if backend_name == VANILLA:
        return VanillaScorer()
    raise ValueError(f"Unknown scoring backend {backend_name!r}")
