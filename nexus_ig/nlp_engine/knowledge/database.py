import sqlite3
import time
import os
import random
import re
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from rapidfuzz import process, fuzz
from ..memory.long_term import LongTermMemory


HINGLISH_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
    "him", "her", "his", "its", "they", "them", "their", "this", "that",
    "these", "those", "am", "not", "no", "nor", "but", "and", "or",
    "if", "then", "so", "too", "very", "just", "about", "for", "with",
    "from", "to", "in", "on", "at", "by", "of", "up", "out", "off",
    "over", "into", "what", "which", "who", "whom", "how", "when",
    "where", "why", "all", "each", "every", "both", "few", "more",
    "some", "any", "most", "other", "than", "such", "only", "own",
    "same", "also", "here", "there", "now", "then", "get", "got",
    "mai", "hai", "ka", "ki", "ke", "ko", "se", "ne", "par", "mein",
    "kya", "koi", "kuch", "yeh", "woh", "toh", "bhi", "nhi", "nahi",
    "haan", "aur", "ya", "jo", "jab", "tab", "ab", "hum", "tum", "bot", "nexus"
}


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
    """ChatterBot-style Statement Pair SQLite Database with Markov Synthesizer & Weighted Fuzzy Search."""

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
        self.seed_default_pairs()

    def seed_default_pairs(self):
        """Seed initial Hinglish roast & casual banter pairs if statement_pairs is empty."""
        seed_data = [
            ("tu pagal ya mai pagal", "Bhai dono hi pagal hain tabhi toh late night group chat kar rahe hain 😂"),
            ("pagal hai tu", "Pehle khud ko mirror mein dekh fir mujhe pagal bol! 😜"),
            ("chup kar", "Main kyu chup ho jaun? Aag toh tune lagayi thi! 🔥"),
            ("ai job kha jayega", "AI job khaye ya na khaye, teri neend zaroor kha raha hai! 😂"),
            ("or ai ko kha jayega job", "Aisa kuch nahi hone wala bhai, AI se pehle teri neend udegaye! 🤣"),
            ("kya chal raha hai", "Bas group chat pe chill scene hai, tu bata kya plan hai? 🥂"),
            ("kaise ho", "Ekdam mast bhai, tu bata tera kya haal chaal hai? ⚡"),
            ("kya kar raha hai", "Tere ajeeb sawalon ke jawab dhoond raha hu! 🤖"),
            ("bhai meme bhej", "Meme dekhne se ghar nahi chalta, padhai kar le! 📖"),
            ("nexus pagal", "Pagal mat bol, pura system hiladunga! ⚡"),
            ("oye listen", "Haan bol bhai, kaunsa naya drama ho gaya? 🍿"),
            ("good night", "Ja so ja, sapne mein bhi bakchodi mat karna! 😴"),
            ("bot bakwas hai", "Tu konsa Einstein hai bhai! 😂"),
            ("sun na", "Bata bhi de ab, suspense kyu bana raha hai? 👀"),
            ("bored ho raha hu", "Toh jaakar bartan dho le, boredom gayab ho jayega! 🧹"),
            ("shana mat ban", "Shana main born hu, banna nahi padta! 😎"),
            ("padhai ho gayi", "Padhai aur meri koi dushman thodi hai, chill kar! 📚"),
            ("chai peene chale", "Chai ke bina life mein zero feel hota hai, chalo ☕"),
            ("kaun hai tu", "Main hu Nexus, is group ka asli boss! 👑"),
            ("gussa mat ho", "Gussa hone ki fursat kisko hai, maze karo! 🎉"),
            ("roast kar", "Tujhe roast karne ki zaroorat nahi, life pehle se kar rahi hai! 🤣"),
        ]
        now = time.time()
        try:
            with self._get_conn() as conn:
                for req, stmt in seed_data:
                    conn.execute("""
                        INSERT INTO statement_pairs (in_response_to, statement, occurrence, confidence, user_id, created_at)
                        VALUES (?, ?, 5, 0.9, 'seed_data', ?)
                        ON CONFLICT(in_response_to, statement) DO UPDATE SET confidence = 0.9
                    """, (req.strip().lower(), stmt.strip(), now))
                conn.commit()
        except Exception:
            pass




    def learn_pair(self, in_response_to: str, statement: str, user_id: str = "user"):
        """Save or increment ChatterBot statement response pair in SQLite."""
        req_clean = in_response_to.strip().lower()
        stmt_clean = statement.strip()
        if not req_clean or not stmt_clean or len(req_clean) < 2 or len(stmt_clean) < 2:
            return

        # Ignore bot commands, mentions, and bot replies from statement pair memory
        if (
            req_clean.startswith(("@", "nexus", "oli", "/", "bot", "chotu")) or
            stmt_clean.startswith(("@", "nexus", "oli", "/", "bot", "chotu")) or
            "bot reply:" in req_clean or "bot reply:" in stmt_clean.lower() or
            "command:" in req_clean or "command:" in stmt_clean.lower()
        ):
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


    def auto_train_from_storage(self, storage):
        """Train statement pairs directly from all historical messages in group_activity database."""
        if not storage:
            return
        try:
            with storage.conn:
                # 1. Train from explicit quoted replies (reply_to_text -> content), excluding bot replies
                cur = storage.conn.execute(
                    """SELECT reply_to_text, content, user_id FROM group_activity
                       WHERE reply_to_text IS NOT NULL AND content IS NOT NULL
                       AND action_type != 'bot_reply'
                       AND LOWER(COALESCE(username, '')) NOT IN ('nexusbot', 'bot', 'nexus')
                       AND content NOT LIKE '@%'
                       AND LENGTH(TRIM(reply_to_text)) > 1 AND LENGTH(TRIM(content)) > 1"""
                )
                rows = cur.fetchall()
                for row in rows:
                    self.learn_pair(row["reply_to_text"], row["content"], user_id=row["user_id"])

                # 2. Train from sequential thread message pairs
                cur = storage.conn.execute(
                    """SELECT thread_id, user_id, content, created_at FROM group_activity
                       WHERE content IS NOT NULL AND LENGTH(TRIM(content)) > 1
                       AND action_type != 'bot_reply'
                       AND LOWER(COALESCE(username, '')) NOT IN ('nexusbot', 'bot', 'nexus')
                       AND content NOT LIKE '@%'
                       ORDER BY thread_id, created_at ASC"""
                )
                rows = cur.fetchall()
                for i in range(len(rows) - 1):
                    curr_row = rows[i]
                    next_row = rows[i + 1]
                    if (
                        curr_row["thread_id"] == next_row["thread_id"]
                        and curr_row["user_id"] != next_row["user_id"]
                        and abs(next_row["created_at"] - curr_row["created_at"]) <= 180
                    ):
                        self.learn_pair(curr_row["content"], next_row["content"], user_id=next_row["user_id"])
        except Exception as exc:
            pass


    def _extract_keywords(self, text: str) -> List[str]:
        """Extract significant content keywords excluding stop words."""
        words = re.findall(r"\w+", text.lower())
        return [w for w in words if len(w) > 2 and w not in HINGLISH_STOP_WORDS]

    def find_best_response(self, text: str, context_text: str = "") -> Optional[str]:
        """Weighted Fuzzy Search & Multi-Turn Context Matching across trained pairs."""
        req_clean = text.strip().lower()
        if not req_clean:
            return None

        # Strip bot call prefixes like 'nexus chat', 'nexus', 'chat', 'bot'
        clean_query = re.sub(r"^(nexus\s+chat|nexus|chat|bot|oye)\s+", "", req_clean).strip()
        if not clean_query:
            clean_query = req_clean

        keywords = self._extract_keywords(clean_query)

        with self._get_conn() as conn:
            # 1. Exact SQL match (with and without prefix)
            for q in (clean_query, req_clean):
                cur = conn.execute(
                    "SELECT statement FROM statement_pairs WHERE in_response_to = ? ORDER BY occurrence DESC, confidence DESC LIMIT 1",
                    (q,)
                )
                row = cur.fetchone()
                if row:
                    return row["statement"]

            # 2. Weighted Fuzzy Search on current query ONLY (never pollute query with context_text)
            cur = conn.execute("SELECT in_response_to, statement, occurrence FROM statement_pairs")
            rows = cur.fetchall()
            if not rows:
                return None

            best_stmt = None
            best_score = 0.0

            for r in rows:
                in_resp = r["in_response_to"]
                stmt = r["statement"]

                # Score directly against current user query
                score = max(
                    fuzz.ratio(clean_query, in_resp),
                    fuzz.token_sort_ratio(clean_query, in_resp),
                )

                # Keyword bonus / penalty
                if keywords:
                    matching_kws = sum(1 for kw in keywords if kw in in_resp or kw in stmt.lower())
                    if matching_kws > 0:
                        score += matching_kws * 15
                    else:
                        score -= 25  # Heavy penalty if user query has keywords but candidate pair shares none

                if score > best_score:
                    best_score = score
                    best_stmt = stmt

            if best_stmt and best_score >= 55:
                return best_stmt

        # 3. Markov Synthesizer fallback if no direct statement pair matches
        return self.generate_markov_response(clean_query)

    def generate_markov_response(self, seed_text: str, max_words: int = 12) -> Optional[str]:
        """Synthesize original Hinglish sentence dynamically from learned word transition graphs."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT statement FROM statement_pairs UNION SELECT in_response_to FROM statement_pairs")
            rows = cur.fetchall()

        if not rows:
            return None

        # Build Bigram Transition Graph
        transitions: Dict[str, List[str]] = defaultdict(list)
        all_words = []

        for row in rows:
            sentence = row[0]
            words = re.findall(r"\w+", sentence)
            if len(words) >= 2:
                for i in range(len(words) - 1):
                    w1, w2 = words[i].lower(), words[i + 1]
                    transitions[w1].append(w2)
                    all_words.append(w1)

        if not transitions:
            return None

        # Pick Seed Word from user text or random learned word
        seed_words = self._extract_keywords(seed_text)
        current = seed_words[0] if seed_words and seed_words[0] in transitions else random.choice(list(transitions.keys()))

        res_words = [current.capitalize()]

        for _ in range(max_words - 1):
            next_options = transitions.get(current.lower())
            if not next_options:
                break
            nxt = random.choice(next_options)
            res_words.append(nxt)
            current = nxt

        if len(res_words) >= 2:
            return " ".join(res_words)

        return None


