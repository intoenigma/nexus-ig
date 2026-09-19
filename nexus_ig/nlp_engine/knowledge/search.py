import os
from typing import Dict, List
from whoosh import fields, index, qparser


class KnowledgeIndex:
    """Whoosh BM25 Full-Text Search Engine."""

    def __init__(self, index_dir: str = "data/whoosh_index"):
        self.index_dir = index_dir
        self.schema = fields.Schema(
            title=fields.TEXT(stored=True),
            content=fields.TEXT(stored=True),
            tags=fields.KEYWORD(stored=True),
        )
        self.ix = self._init_index()
        self._seed_kb()

    def _init_index(self):
        """Create or open Whoosh index directory."""
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir, exist_ok=True)
            return index.create_in(self.index_dir, self.schema)
        try:
            return index.open_dir(self.index_dir)
        except Exception:
            return index.create_in(self.index_dir, self.schema)

    def _seed_kb(self):
        """Seed initial knowledge articles."""
        try:
            writer = self.ix.writer()
            writer.add_document(
                title="Python & Flask Guide",
                content="Python is a versatile programming language. Flask is a micro web framework for Python.",
                tags="python flask web coding",
            )
            writer.add_document(
                title="Exam Preparation",
                content="Study key concepts early, solve past papers, and revise important formulas before exam day.",
                tags="exam study paper test",
            )
            writer.commit()
        except Exception:
            pass

    def add_document(self, title: str, content: str, tags: str = ""):
        """Add new document to search index."""
        try:
            writer = self.ix.writer()
            writer.add_document(title=title, content=content, tags=tags)
            writer.commit()
        except Exception:
            pass

    def search(self, query_str: str, limit: int = 3) -> List[Dict[str, str]]:
        """Search Whoosh index using BM25 scoring."""
        results = []
        try:
            with self.ix.searcher() as searcher:
                parser = qparser.QueryParser("content", self.ix.schema)
                q = parser.parse(query_str)
                hits = searcher.search(q, limit=limit)
                for hit in hits:
                    results.append({"title": hit["title"], "content": hit["content"]})
        except Exception:
            pass
        return results
