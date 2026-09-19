from typing import List, Tuple
import networkx as nx


class KnowledgeGraph:
    """NetworkX-powered Entity & Subject Relationship Graph."""

    def __init__(self):
        self.g = nx.DiGraph()
        self._seed_default_knowledge()

    def _seed_default_knowledge(self):
        """Seed core technology and group relations."""
        self.g.add_edge("Python", "Flask", relation="has_framework")
        self.g.add_edge("Python", "Data Science", relation="used_in")
        self.g.add_edge("Flask", "Web App", relation="builds")
        self.g.add_edge("ML", "Machine Learning", relation="alias")
        self.g.add_edge("OS", "Operating System", relation="alias")

    def add_fact(self, subject: str, predicate: str, object_val: str):
        """Add directed relation edge between entities."""
        self.g.add_edge(subject.lower(), object_val.lower(), relation=predicate)

    def get_relations(self, entity: str) -> List[Tuple[str, str, str]]:
        """Find outgoing and incoming relations for an entity."""
        e_lower = entity.lower()
        results = []
        if e_lower in self.g:
            for neighbor in self.g.neighbors(e_lower):
                rel = self.g[e_lower][neighbor].get("relation", "related_to")
                results.append((e_lower, rel, neighbor))

            for u, v, data in self.g.in_edges(e_lower, data=True):
                rel = data.get("relation", "related_to")
                results.append((u, rel, e_lower))
        return results
