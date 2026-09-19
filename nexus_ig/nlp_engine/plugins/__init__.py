"""Plugin architecture hook for external NLP tools and scrapers."""
from typing import Dict, Any


class BasePlugin:
    """Base class for custom NLP plugins."""

    name: str = "base"

    def process(self, text: str) -> Dict[str, Any]:
        return {}


__all__ = ["BasePlugin"]
