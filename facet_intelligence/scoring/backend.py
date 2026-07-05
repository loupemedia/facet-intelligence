"""Scoring backend interface — SparkleScore client implements this in Epic 3."""

from abc import ABC, abstractmethod
from typing import Any


class ScoringBackend(ABC):
    @abstractmethod
    def score_candidates(
        self,
        tenant_id: str,
        anchor: dict[str, Any] | None,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Return candidates with score fields attached, best-first."""
