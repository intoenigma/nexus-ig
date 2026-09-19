from ..nlp.entities import ExtractedEntities


class ReasoningEngine:
    """Combines intent, entities, and context to produce logical conclusions."""

    def reason_about_message(self, text: str, intent: str, entities: ExtractedEntities) -> str:
        """Infer target subject from intent & extracted entities."""
        if entities.technologies:
            return f"tech:{entities.technologies[0]}"
        if entities.places:
            return f"place:{entities.places[0]}"
        if intent != "general_chat":
            return f"intent:{intent}"
        return "general"
