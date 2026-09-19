# 🤖 Nexus IG — Instagram Group Chat Automation Bot

A production-ready, modular Instagram Group Chat Automation & Intelligence Bot built with Python 3.11+.

Featuring a zero-dependency lightweight NLP engine, SQLite persistent storage, leveling & mini-economy system, automated moderation, rules enforcement, auto-revive, and message archiving.

---

## ⚡ Features Overview

- **🤖 Target Group Automation**: Listens to targeted group threads or all incoming direct messages.
- **🧠 Zero-Dependency NLP Engine**: Hinglish & English sentiment analysis, word tokenization, intent recognition, entity extraction, and extractive summarization with zero heavy ML libraries.
- **💰 Leveling & Economy**: Message XP system, level progression badges, daily rewards, coin transfers, and item shop.
- **🛡️ Auto Moderation & Protection**: Instant link blocking, bad word filter, sensitive info alerts, slow mode, and automated warnings.
- **🔄 Auto-Revive & Scheduled Rules**: Detects dead chat activity and sends periodic rule reminders.
- **💾 Message Archival**: Persistent message logging to SQLite database.

---

## 📂 Project Structure

```
nexus-ig/
├── main.py                        # Entry point — calls nexus_ig.core.bot.main()
├── login.py                       # One-shot session login helper
├── setup.py / setup.cfg           # Package configuration
├── requirements.txt               # Minimal production dependencies
├── .env / .env.example            # Environment runtime configuration
├── session.json                   # Instagram session (git-ignored)
├── data/                          # SQLite database & runtime data
│   └── nexus.db                   # Main SQLite database
├── scripts/
│   ├── init_memory.py             # Pre-seed greeted threads
│   ├── backup.py                  # Database backup helper
│   └── migrate.py                 # DB schema migration helper
├── tests/                         # Pytest automated test suite
└── nexus_ig/                      # Core package
    ├── __init__.py                # Exports (NexusBot, main)
    ├── core/                      # Core engine modules
    │   ├── bot.py                 # NexusBot main loop & polling
    │   ├── config.py              # Configuration loader & dataclass
    │   ├── console.py             # Rich terminal UI & dashboards
    │   ├── constants.py           # Project constants & defaults
    │   ├── events.py              # Event dispatcher system
    │   ├── logger.py              # Central logging helper
    │   ├── scheduler.py           # Periodic background tasks
    │   └── storage.py             # SQLite Storage access layer
    ├── commands/                  # Command handlers
    │   ├── __init__.py            # Main CommandHandler routing
    │   ├── admin.py               # Admin & group management
    │   └── economy.py             # Economy & shop commands
    ├── instagram/                 # Instagram API integration
    │   ├── client.py              # Low-level client wrapper
    │   ├── groups.py              # Group thread helpers
    │   └── login.py               # Authentication helper
    ├── nlp_engine/                # Lightweight traditional NLP engine
    │   ├── bot.py                 # StrictNLPBot orchestrator
    │   ├── brain/                 # Ranking, intent, response selection
    │   ├── intents/               # Intent classifier
    │   ├── knowledge/             # Fact database & FAQ matcher
    │   ├── learning/              # Pattern learning
    │   ├── memory/                # Conversation history & entity tracker
    │   ├── nlp/                   # Tokenizer, sentiment, topics, similarity, summarizer
    │   └── response/              # Generator & templates
    └── services/                  # Application services
        ├── archiver.py            # Message archiving service
        ├── chatbot.py             # Chatbot service facade
        └── provider.py            # Instagram API provider wrapper
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Instagram credentials and preferences:

```env
INSTAGRAM_USERNAME=your_bot_username
INSTAGRAM_PASSWORD=your_bot_password
COMMAND_PREFIX=nexus
DATABASE_FILE=data/nexus.db
```

### 3. Session Login

Generate a session token:

```bash
python login.py
```

### 4. Run Bot

```bash
python main.py
```

---

## 🎮 Commands Reference

### Public Commands

| Command | Description |
|---|---|
| `nexus help` | Display command help menu |
| `nexus profile` | View your level, XP, coins, and title badge |
| `nexus daily` | Claim your daily coin reward |
| `nexus transfer @user <amount>` | Transfer coins to another member |
| `nexus shop` | View economy item shop |
| `nexus buy <id>` | Purchase a shop item/badge |
| `nexus leaderboard` | View group level & XP leaderboard |
| `nexus rules` | Display group rules |

### Admin Commands

| Command | Description |
|---|---|
| `nexus status` | Display bot operational health report |
| `nexus gc info` | View current group chat information |
| `nexus welcome set <msg>` | Set custom welcome message |
| `nexus warnadd <word>` | Add word to bad word filter |
| `nexus warnlist` | List active bad words |

---

## 🧪 Testing

Run the automated test suite with pytest:

```bash
pytest
```

---

## 📜 License

MIT License.
