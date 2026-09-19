"""In-memory caching utilities."""

class MemoryCache:
    def __init__(self, maxsize: int = 50000):
        self._set = set()
        self.maxsize = maxsize

    def add(self, key):
        self._set.add(str(key))

    def contains(self, key) -> bool:
        return str(key) in self._set

    def clear(self):
        self._set.clear()
