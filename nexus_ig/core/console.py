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


# ── User-friendly Activity Logging ─────────────────────────────────

_USER_COLORS = [
    "bright_cyan",
    "bright_yellow",
    "bright_magenta",
    "bright_green",
    "bright_blue",
    "orange1",
    "deep_pink1",
    "spring_green1",
    "light_goldenrod1",
]


def get_user_color(username: str) -> str:
    if not username:
        return "white"
    idx = sum(ord(c) for c in str(username)) % len(_USER_COLORS)
    return _USER_COLORS[idx]


def log_activity(group_name: str, sender_name: str, action_type: str, content: str = "", is_bot: bool = False, is_admin: bool = False):
    """Format and stream live group chat events cleanly without developer noise."""
    stamp = time.strftime("%H:%M:%S")
    grp = group_name or "Direct Message"
    if len(grp) > 22:
        grp = grp[:20] + "…"

    # Sender formatting
    clean_sender = str(sender_name or "User").lstrip("@")
    if is_bot:
        sender_badge = "[bold bright_green]🤖 NexusBot[/bold bright_green]"
    elif is_admin:
        sender_badge = f"[bold bright_yellow]★ @{clean_sender}[/bold bright_yellow]"
    else:
        ucolor = get_user_color(clean_sender)
        sender_badge = f"[bold {ucolor}]@{clean_sender}[/bold {ucolor}]"

    group_badge = f"[bold bright_cyan][{grp}][/bold bright_cyan]"

    # Action content formatting
    act = action_type.lower()
    if act == "text":
        action_text = f'[bright_white]"{content}"[/bright_white]'
    elif act in ("reel", "clip", "reel_share"):
        extra = f" [dim white]({content[:35]}…)[/dim white]" if content else ""
        action_text = f"[bold bright_red]🎬 Shared a Reel[/bold bright_red]{extra}"
    elif act == "media_share":
        extra = f" [dim white]({content[:35]}…)[/dim white]" if content else ""
        action_text = f"[bold bright_blue]📸 Shared a Post[/bold bright_blue]{extra}"
    elif act == "photo":
        action_text = "[bold cyan]🖼️ Sent a Photo[/bold cyan]"
    elif act == "video":
        action_text = "[bold magenta]🎥 Sent a Video[/bold magenta]"
    elif act in ("voice", "voice_media"):
        action_text = "[bold yellow]🎙️ Sent a Voice Message[/bold yellow]"
    elif act in ("sticker", "animated_media"):
        action_text = "[bold bright_yellow]🎭 Sent a Sticker[/bold bright_yellow]"
    elif act in ("story", "story_share"):
        action_text = "[bold purple]📱 Shared a Story[/bold purple]"
    elif act == "like":
        action_text = "[bold red]❤️ Liked a message[/bold red]"
    elif act == "join":
        action_text = "[bold bright_green]👋 Joined the group[/bold bright_green]"
    elif act == "left":
        action_text = "[bold bright_red]🚪 Left the group[/bold bright_red]"
    elif act == "command":
        action_text = f"[bold bright_yellow]⚡ Command:[/] [bright_white]{content}[/bright_white]"
    elif act == "reply":
        action_text = f"[bold bright_green]🤖 Bot Reply:[/] [bright_white]{content}[/bright_white]"
    elif act == "warn":
        action_text = f"[bold bright_red]🛡️ Warning:[/] [bright_white]{content}[/bright_white]"
    else:
        action_text = f"[bright_white]{content or action_type}[/bright_white]"

    _con.print(f" [dim bright_black]{stamp}[/] {group_badge} : {sender_badge} : {action_text}")


# ── Startup dashboard ───────────────────────────────────────────────

def startup(config, account_name, account_id, target_group_name="All Groups"):
    banner()

    status_table = Table(
        show_header=False,
        box=box.ROUNDED,
        padding=(0, 2),
        expand=True,
    )
    status_table.add_column("Property", style="bold bright_cyan", width=22)
    status_table.add_column("Value", style="bright_white")

    clean_acct = str(account_name or "bot").lstrip("@")
    status_table.add_row("🤖 Bot Account", f"[bold bright_green]@{clean_acct}[/bold bright_green]")
    status_table.add_row("🎯 Target Group", f"[bold yellow]{target_group_name}[/bold yellow]")
    status_table.add_row("⚡ Command Prefix", f"[bold bright_yellow]{config.command_prefix}[/bold bright_yellow]")
    status_table.add_row("🛡️ Protection", "[bold bright_green]Active (Bad Words Filter + Auto-Warn)[/]")
    status_table.add_row("📡 Status", "[bold bright_green]🟢 Online & Live Streaming Activity[/bold bright_green]")
    _con.print(status_table)

    section("LIVE GROUP ACTIVITY STREAM")
    _con.print("[dim cyan]Listening for messages, reels, photos, and commands (Ctrl+C to stop)...[/dim cyan]\n")



# ── Login / Memory screens ──────────────────────────────────────────

def login_screen():
    banner()
    section("INSTAGRAM AUTHENTICATION")
    
    table = Table(
        title="[bold bright_yellow]How to Get Your Instagram Session ID[/bold bright_yellow]",
        show_header=True,
        header_style="bold bright_cyan",
        box=box.ROUNDED,
        expand=True,
    )
    table.add_column("Step", style="bold bright_magenta", width=6, justify="center")
    table.add_column("Desktop (Chrome / Edge / Firefox)", style="bright_white")
    table.add_column("Mobile (Kiwi / Termux)", style="bright_white")

    table.add_row("1", "Log in to instagram.com", "Log in to instagram.com in Kiwi Browser")
    table.add_row("2", "Press F12 -> Application / Storage", "Open Developer Tools or Cookie extension")
    table.add_row("3", "Click Cookies -> instagram.com", "Find and select 'sessionid'")
    table.add_row("4", "Copy 'sessionid' value & paste below", "Copy full 'sessionid' value & paste below")

    _con.print(table)
    _con.print("\n[dim cyan]Note: Session ID will be saved permanently to .env & session.json (no repeat logins needed!)[/dim cyan]\n")



def memory_screen():
    banner()
    section("MEMORY INIT")
    row("Action", "Mark recent groups as already greeted")
    row("Storage", "SQLite database")
