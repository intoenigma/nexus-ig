from typing import List, Optional
from ..memory.short_term import ChatMessage


class ContextResolver:
    """Group context, threading, ellipsis, and implicit context resolution."""

    def resolve_implicit_context(self, current_text: str, history: List[ChatMessage]) -> Optional[str]:
        """Resolve implicit topics across conversational turns."""
        lower_raw = current_text.lower().strip()
        prev_text = history[-2].text.lower() if len(history) >= 2 else ""

        if "flask" in lower_raw and "python" in prev_text:
            return "Flask Python ka popular web framework hai. Python ke baad Flask seekhna useful rahega!"

        if lower_raw in ["konsa?", "kaunsa?", "konsa", "kaunsa", "kab?", "kab"]:
            if "exam" in prev_text or "ppr" in prev_text or "ml" in prev_text or "os" in prev_text:
                return "ML wala paper hai na? Acche se tayari kar lo!"
            return "Konsa topic ki baat ho rahi hai?"

        return None
