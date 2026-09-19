"""Beautiful terminal output powered by Rich.

Every public function in this module preserves the exact same signature
as the original plain-text version so that callers never need to change.
"""

import os
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich import box

# ── Force UTF-8 on Windows legacy terminals ─────────────────────────
if sys.platform == "win32":
    try:
        os.system("chcp 65001 >nul 2>&1")
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Theme ────────────────────────────────────────────────────────────
_THEME = Theme({
    "banner.title":  "bold bright_cyan",
    "banner.sub":    "dim cyan",
    "section.title": "bold bright_magenta",
    "label":         "bold white",
    "value":         "bright_green",
    "stamp":         "dim bright_black",
    "ok":            "bold bright_green",
    "warn":          "bold bright_yellow",
    "err":           "bold bright_red",
    "cmd":           "bold bright_cyan",
    "idle":          "dim",
    "check":         "bold bright_blue",
    "archive":       "bold bright_magenta",
    "started":       "bold bright_green",
    "info":          "bright_white",
})

_con = Console(theme=_THEME, highlight=False)

WIDTH = 72

# ── Label -> style map for status() ─────────────────────────────────
_LABEL_STYLES = {
    "OK":       "ok",
    "STARTED":  "started",
    "WARN":     "warn",
    "ERROR":    "err",
    "COMMAND":  "cmd",
    "IDLE":     "idle",
    "CHECK":    "check",
    "ARCHIVE":  "archive",
    "SESSION":  "info",
    "LOGIN":    "info",
    "FALLBACK": "warn",
    "NEXT":     "ok",
}

_LABEL_ICONS = {
    "OK":       "[+]",
    "STARTED":  "[>]",
    "WARN":     "[!]",
    "ERROR":    "[X]",
    "COMMAND":  "[#]",
    "IDLE":     "[.]",
    "CHECK":    "[?]",
    "ARCHIVE":  "[A]",
    "SESSION":  "[S]",
    "LOGIN":    "[L]",
    "FALLBACK": "[~]",
    "NEXT":     "[>]",
}


# ── Primitives ───────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def line(char="-"):
    _con.rule(style="dim bright_black", characters=char)


def center(text):
    text = str(text)
    if len(text) >= WIDTH:
        return text[:WIDTH]
    left = (WIDTH - len(text)) // 2
    return " " * left + text


# ── Banner ───────────────────────────────────────────────────────────

def banner():
    clear()
    title_text = Text()
    title_text.append("NEXUS ", style="bold bright_yellow")
    title_text.append("INSTAGRAM GC BOT", style="bold bright_cyan")


    subtitle = Text("Target Group Automation Console", style="dim cyan")

    panel = Panel(
        Text.assemble(title_text, "\n", subtitle, justify="center"),
        box=box.DOUBLE_EDGE,
        border_style="bright_cyan",
        padding=(1, 4),
    )
    _con.print(panel)


# ── Sections & Rows ─────────────────────────────────────────────────

def section(title):
    _con.print()
    _con.rule(f"[section.title] {title} [/]", style="bright_magenta", characters="-")


def row(label, value):
    _con.print(f"  [label]{label:<22}[/] : [value]{value}[/]")


# ── Live-log helpers ─────────────────────────────────────────────────

def status(label, value=""):
    stamp = time.strftime("%H:%M:%S")
    style = _LABEL_STYLES.get(label.upper(), "info")
    icon = _LABEL_ICONS.get(label.upper(), "[*]")
    suffix = f" {value}" if value else ""
    _con.print(
        f" [stamp]\\[{stamp}][/] {icon} [{style}]{label:<14}[/]{suffix}"
    )


def success(message):
    status("OK", message)


def warning(message):
    status("WARN", message)


def error(message):
    status("ERROR", message)


# ── Startup dashboard ───────────────────────────────────────────────

def startup(config, account_name, account_id):
    banner()

    # Account table
    section("ACCOUNT")
    acct_table = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 1),
        expand=True,
        show_edge=False,
    )
    acct_table.add_column("Key", style="label", width=24)
    acct_table.add_column("Value", style="value")
    acct_table.add_row("Logged in as", f"{account_name} ({account_id})")
    acct_table.add_row("Session file", config.session_file)
    acct_table.add_row("Database", config.database_file)
    acct_table.add_row("Target thread", config.target_thread_id or "all")
    _con.print(acct_table)

    # System table
    section("SYSTEM")
    sys_table = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 1),
        expand=True,
        show_edge=False,
    )
    sys_table.add_column("Key", style="label", width=24)
    sys_table.add_column("Value", style="value")
    sys_table.add_row("Mode", "Target group bot")
    sys_table.add_row("AI chat mode", "[bold bright_green]18-Feature Traditional NLP Engine Active[/]")
    sys_table.add_row("Command prefix", f"[bold bright_yellow]{config.command_prefix}[/]")
    sys_table.add_row("Check interval", f"{config.poll_interval}s")
    sys_table.add_row("Thread scan limit", str(config.thread_fetch_amount))
    sys_table.add_row("Control users", str(len(config.admin_usernames) + len(config.admin_user_ids)))
    sys_table.add_row("Config reload", "[bright_green]enabled[/]")
    _con.print(sys_table)

    section("LIVE LOG")
    status("STARTED", "Press Ctrl+C to stop")


# ── Login / Memory screens ──────────────────────────────────────────

def login_screen():
    banner()
    section("SESSION LOGIN")
    row("Step 1", "Open Instagram.com in browser")
    row("Step 2", "Inspect -> Application -> Cookies")
    row("Step 3", "Copy the sessionid cookie value")


def memory_screen():
    banner()
    section("MEMORY INIT")
    row("Action", "Mark recent groups as already greeted")
    row("Storage", "SQLite database")
