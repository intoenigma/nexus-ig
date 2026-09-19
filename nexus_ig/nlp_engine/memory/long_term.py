import os
import diskcache


class LongTermMemory:
    """Persistent storage backed by diskcache."""

    def __init__(self, cache_dir: str = "data/nlp_cache"):
        os.makedirs(cache_dir, exist_ok=True)
        self.cache = diskcache.Cache(cache_dir)

    def set(self, key: str, value: dict, expire: float = None):
        """Save dict to persistent cache."""
        self.cache.set(key, value, expire=expire)

    def get(self, key: str) -> dict:
        """Fetch dict from persistent cache."""
        return self.cache.get(key)

    def delete(self, key: str):
        """Remove key from persistent cache."""
        self.cache.delete(key)
