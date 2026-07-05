"""Shared utilities."""

import logging
import os

logger = logging.getLogger(__name__)


def validate_environment_variables(required: list[str]) -> None:
    """Fail fast if required environment variables are missing."""
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(sorted(missing))}"
        )
