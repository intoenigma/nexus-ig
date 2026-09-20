from dataclasses import dataclass, field
from typing import List, Optional

try:
    import dateparser
except ImportError:
    dateparser = None


@dataclass
class ExtractedEntities:
    """Named Entity Extraction output."""

    people: List[str] = field(default_factory=list)
    places: List[str] = field(default_factory=list)
    dates_times: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    raw_parsed_date: Optional[str] = None



class EntityExtractor:
    """Named Entity Extraction (NER) & Hinglish Normalization Engine."""

    HINGLISH_SLANG = {
        "ppr": "paper",
        "padhai": "study",
        "kal": "tomorrow",
        "aaj": "today",
        "milte hai": "meetup",
        "bro": "brother",
        "bhai": "brother",
        "pls": "please",
    }

    TECH_KEYWORDS = {"python", "flask", "django", "java", "c++", "sql", "api", "react", "html", "css"}
    KNOWN_PLACES = {"bikaner", "goa", "delhi", "mumbai", "jaipur", "bangalore"}

    def normalize_hinglish(self, text: str) -> str:
        """Replace common Hinglish abbreviations with canonical terms."""
        words = text.split()
        res = [self.HINGLISH_SLANG.get(w.lower(), w) for w in words]
        return " ".join(res)

    def extract(self, text: str) -> ExtractedEntities:
        """Extract People, Places, Tech terms, and Temporal dates/times."""
        norm_text = self.normalize_hinglish(text)
        entities = ExtractedEntities()

        words = norm_text.split()
        for w in words:
            w_clean = w.strip(",.!?").lower()
            if w_clean in self.TECH_KEYWORDS:
                entities.technologies.append(w_clean)
            if w_clean in self.KNOWN_PLACES:
                entities.places.append(w_clean.capitalize())
            if w.startswith("@") and len(w) > 1:
                entities.people.append(w.lstrip("@"))

        if dateparser:
            try:
                parsed_dt = dateparser.parse(
                    norm_text,
                    settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": None},
                )
                if parsed_dt:
                    entities.dates_times.append(parsed_dt.strftime("%Y-%m-%d %H:%M"))
                    entities.raw_parsed_date = str(parsed_dt)
            except Exception:
                pass


        return entities
