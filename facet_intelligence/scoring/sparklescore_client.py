"""SparkleScore API adapter (Principle 14) — Epic 3."""

import logging
from typing import Any

from facet_intelligence.scoring.backend import ScoringBackend

logger = logging.getLogger(__name__)


class SparkleScoreClient(ScoringBackend):
    """Calls SparkleScore per candidate. Not wired until SS-002 staging pilot."""

    def score_candidates(
        self,
        tenant_id: str,
        anchor: dict[str, Any] | None,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        raise NotImplementedError("SparkleScore client — implement in PRD-FI-001 Epic 3")
