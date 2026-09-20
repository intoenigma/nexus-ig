import sqlite3
import time
import os
from dataclasses import dataclass, field, asdict
from typing import Optional
from rapidfuzz import process, fuzz
from ..memory.long_term import LongTermMemory


@dataclass
class KnowledgeFact:
    """Knowledge base fact entry with confidence scoring."""

    subject: str
    predicate: str
    object_val: str
    confidence: float = 0.5  # 0.0 to 1.0 (prevents unverified claims from becoming DB truth)
    source: str = "user_input"
    confirmations: int = 1
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def model_dump(self):
        return asdict(self)


class FactDatabase:
    """Persistent Fact Database with Confidence Verification."""

    def __init__(self, long_term: LongTermMemory):
        self.long_term = long_term

    def add_fact(self, subject: str, predicate: str, object_val: str, initial_confidence: float = 0.3) -> KnowledgeFact:
        """Add or update fact with initial confidence score."""
        key = f"fact:{subject.lower()}:{predicate.lower()}"
        data = self.long_term.get(key)
        now = time.time()
        if data:
            try:
                fact = KnowledgeFact(**data)
                fact.confirmations += 1
                fact.confidence = min(1.0, fact.confidence + 0.15)
                fact.updated_at = now
                self.long_term.set(key, fact.model_dump())
                return fact
            except Exception:
                pass


        fact = KnowledgeFact(
            subject=subject,
            predicate=predicate,
            object_val=object_val,
            confidence=initial_confidence,
            source="user_input",
            created_at=now,
            updated_at=now,
        )
        self.long_term.set(key, fact.model_dump())
        return fact

    def get_fact(self, subject: str, predicate: str) -> Optional[KnowledgeFact]:
        """Fetch verified fact if confidence >= 0.40."""
        key = f"fact:{subject.lower()}:{predicate.lower()}"
        data = self.long_term.get(key)
        if data:
            try:
                fact = KnowledgeFact(**data)
                if fact.confidence >= 0.40:
                    return fact
            except Exception:
                pass
        return None


class SQLiteStatementDatabase:
    """ChatterBot-style Statement Pair SQLite Database."""

    def __init__(self, db_path: str = "data/chatterbot_memory.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS statement_pairs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    in_response_to TEXT NOT NULL,
                    statement TEXT NOT NULL,
                    occurrence INTEGER DEFAULT 1,
                    confidence REAL DEFAULT 0.5,
                    user_id TEXT,
                    created_at REAL,
                    UNIQUE(in_response_to, statement)
                )
            """)
            conn.commit()

    def learn_pair(self, in_response_to: str, statement: str, user_id: str = "user"):
        """Save or increment ChatterBot statement response pair in SQLite."""
        req_clean = in_response_to.strip().lower()
        stmt_clean = statement.strip()
        if not req_clean or not stmt_clean or len(req_clean) < 2 or len(stmt_clean) < 2:
            return
        now = time.time()
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO statement_pairs (in_response_to, statement, occurrence, confidence, user_id, created_at)
                VALUES (?, ?, 1, 0.5, ?, ?)
                ON CONFLICT(in_response_to, statement) DO UPDATE SET
                    occurrence = occurrence + 1,
                    confidence = MIN(1.0, confidence + 0.1)
            """, (req_clean, stmt_clean, str(user_id), now))
            conn.commit()

    def find_best_response(self, text: str) -> Optional[str]:
        """Search SQLite statement pairs for exact or rapidfuzz fuzzy match on in_response_to."""
        req_clean = text.strip().lower()
        with self._get_conn() as conn:
            # 1. Exact SQL match
            cur = conn.execute(
                "SELECT statement FROM statement_pairs WHERE in_response_to = ? ORDER BY occurrence DESC, confidence DESC LIMIT 1",
                (req_clean,)
            )
            row = cur.fetchone()
            if row:
                return row["statement"]

            # 2. RapidFuzz Fuzzy SQL Search
            cur = conn.execute("SELECT in_response_to, statement, occurrence FROM statement_pairs")
            rows = cur.fetchall()
            if not rows:
                return None

            choices = {row["in_response_to"]: row["statement"] for row in rows}
            match = process.extractOne(req_clean, list(choices.keys()), scorer=fuzz.token_sort_ratio)
            if match and match[1] >= 75:
                matched_key = match[0]
                return choices[matched_key]

        return None
