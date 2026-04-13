#!/usr/bin/env python3
"""
Democracy 4 - Realistic Economics Overhaul — Save Patcher v3.1
==============================================================

Patches the autosave between turns to replace the engine's hardcoded
interest-rate formula with a realistic yield-curve-driven debt cost model,
and overrides the credit rating display to track the mod's SovereignRisk.

How it works:
  1. On startup, patches the game's simconfig.txt to widen the interest rate
     range (0.1%-25%) and align credit rating thresholds with the mod's 7-tier
     system. Creates a .vanilla.bak backup for safe restoration.
  2. Watches the autosave file for changes (player ends a turn).
  3. Reads yield values (ShortTermYield, MediumTermYield, LongTermYield) and
     SovereignRisk from the save XML.
  4. Maintains a debt-maturity model: outstanding debt is split into tranches
     that mature and roll over at the current blended rate.
  5. Computes the effective weighted-average interest rate and derives a credit
     rating from SovereignRisk, then patches the save's interest rate (<3>),
     credit value (<6>), and credit rating (<creditrating>).
  6. The player reloads the autosave (F9) to play with the corrected values.

v3.1 improvements over v3:
  - Patches credit_value and creditrating from SovereignRisk
  - Auto-patches simconfig.txt on startup (with vanilla backup)
  - Credit rating displayed in dashboard with colour coding
  - New --gamedir, --restore-simconfig CLI options
  - Aligned thresholds: simconfig + patcher use identical credit boundaries

v3 improvements over v2:
  - Cleaner, colour-coded console output with a compact dashboard
  - Auto-detects whether Democracy 4 is running
  - Sound notification on successful patch
  - Robust error recovery (corrupted saves, mid-write detection)
  - Graceful shutdown on Ctrl+C
  - Persistent state survives patcher restarts (patcher_state.json)
  - Configurable via constants at the top of the file

Usage:
  python D4_Economics_Patcher.py                        # interactive mode
  python D4_Economics_Patcher.py --savedir <path>       # custom save path
  python D4_Economics_Patcher.py --gamedir <path>       # custom game install
  python D4_Economics_Patcher.py --once                  # patch once and exit
  python D4_Economics_Patcher.py --restore-simconfig     # undo simconfig changes
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import re
import shutil
import signal
import struct
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# =============================================================================
# CONFIGURATION
# =============================================================================

VERSION = "3.1.0"

# Yield blending weights (must sum to 1.0)
WEIGHT_SHORT  = 0.15   # 1-2 year paper
WEIGHT_MEDIUM = 0.55   # 5-year benchmark
WEIGHT_LONG   = 0.30   # 10-year benchmark

# Maturity model — how many quarterly tranches exist and how fast they roll
MATURITY_TRANCHES   = 20    # 5 years of quarterly tranches
ROLLOVER_PER_TURN   = 1     # tranches that mature each quarter

# Yield values are 0-1 in the save; map to real interest-rate range
YIELD_FLOOR  = 0.001   # minimum annual rate (0.1%)
YIELD_CAP    = 0.25     # maximum annual rate (25%)

# Credit rating thresholds — SovereignRisk (0-1, higher=worse) → letter grade
# These MUST match the simconfig.txt CREDIT_RATING_* values exactly
CREDIT_THRESHOLDS = [
    (0.06, "AAA"),
    (0.12, "AA"),
    (0.20, "A"),
    (0.32, "BBB"),
    (0.48, "BB"),
    (0.65, "B"),
    (0.80, "CCC"),
    (0.90, "CC"),
    (0.96, "C"),
]
# If SovereignRisk >= 0.96 → "D" (default/junk)

# simconfig overrides — applied to game's simconfig.txt on startup
SIMCONFIG_OVERRIDES = {
    "INTEREST_RATE_MIN": "0.002",
    "INTEREST_RATE_MAX": "0.25",
    "DEBT_TO_GDP_MAX": "3.5",
    "CREDIT_RATING_AAA": "0.06",
    "CREDIT_RATING_AA": "0.12",
    "CREDIT_RATING_A": "0.20",
    "CREDIT_RATING_BBB": "0.32",
    "CREDIT_RATING_BB": "0.48",
    "CREDIT_RATING_B": "0.65",
    "CREDIT_RATING_CCC": "0.80",
    "CREDIT_RATING_CC": "0.90",
    "CREDIT_RATING_C": "0.96",
    "DEBTRATIO_CREDIT_EFFECT": "0.30",
    "DEFICIT_CREDIT_EFFECT": "0.05",
    "MONEYPRINT_CREDIT_EFFECT": "0.05",
}

# File paths (defaults — can be overridden by args)
DEFAULT_SAVE_DIR = Path.home() / "OneDrive" / "Documents" / "My Games" / "democracy4" / "savegames"
DEFAULT_GAME_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Democracy 4")
AUTOSAVE_NAME    = "autosave.xml"
STATE_FILE_NAME  = "patcher_state.json"

# Polling
POLL_INTERVAL = 1.0     # seconds between file-change checks
MAX_RETRY     = 5       # retries on read failure before giving up

# Game process detection
GAME_PROCESS_NAME = "Democracy4.exe"

# Console colours (ANSI)
class C:
    """ANSI colour codes. Disabled automatically on non-supporting terminals."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    MAGENTA = "\033[95m"

    @classmethod
    def disable(cls):
        for attr in dir(cls):
            if attr.isupper() and isinstance(getattr(cls, attr), str):
                setattr(cls, attr, "")


# Ensure UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError for box-drawing chars)
if platform.system() == "Windows":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

# Disable colours if not a real terminal or if on older Windows without ANSI
if not sys.stdout.isatty():
    C.disable()
elif platform.system() == "Windows":
    try:
        kernel32 = ctypes.windll.kernel32
        # Enable ANSI on Windows 10+
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        C.disable()


# =============================================================================
# DATA MODEL
# =============================================================================

@dataclass
class DebtTranche:
    """A tranche of government debt issued at a fixed rate."""
    annual_rate: float      # the rate at which this tranche was issued
    share: float            # fraction of total debt in this tranche (sums to ~1)
    quarters_remaining: int # quarters until maturity

@dataclass
class PatcherState:
    """Persistent state across patcher restarts."""
    last_turn: int = 0
    last_hash: str = ""
    tranches: List[Dict] = field(default_factory=list)
    last_blended_rate: float = 0.03
    patches_applied: int = 0
    session_start: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PatcherState":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def get_tranches(self) -> List[DebtTranche]:
        return [DebtTranche(**t) for t in self.tranches]

    def set_tranches(self, tranches: List[DebtTranche]):
        self.tranches = [asdict(t) for t in tranches]


# =============================================================================
# SAVE FILE PARSING
# =============================================================================

def parse_save(path: Path) -> Optional[dict]:
    """
    Parse a Democracy 4 autosave XML file and extract relevant data.
    Returns None if the file is corrupt or unreadable.
    """
    for attempt in range(MAX_RETRY):
        try:
            raw = path.read_text(encoding="utf-8")
            break
        except (OSError, UnicodeDecodeError):
            if attempt < MAX_RETRY - 1:
                time.sleep(0.3)
            else:
                return None

    # D4 saves have multiple top-level elements — wrap in <root>
    # Fix invalid tags starting with digits (e.g. <0>, <1_hist>)
    raw = re.sub(r"<(/?)(\d+[a-zA-Z_]*)>", r"<\1_\2>", raw)
    # Strip stray </xml> closing tag that D4 writes without a matching opener
    raw = raw.replace("</xml>", "")
    raw = f"<root>{raw}</root>"

    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return None

    data: dict = {}

    # ---- Mission (country) ----
    mission = root.find("mission")
    if mission is not None:
        name_elem = mission.find("name")
        data["mission"] = name_elem.text if name_elem is not None else "unknown"
    else:
        data["mission"] = "unknown"

    # ---- Turn count ----
    finances_elem = root.find("finances")
    turn = 0
    if finances_elem is not None:
        debthist = finances_elem.find("debthist")
        if debthist is not None and debthist.text:
            turn = len(debthist.text.strip().rstrip(",").split(","))
    data["turn"] = turn

    # ---- Simulation values ----
    simvalues: Dict[str, float] = {}
    sv_section = root.find("simvalues")
    if sv_section is not None:
        for sv in sv_section.findall("simvalue"):
            n = sv.find("name")
            v = sv.find("value")
            if n is not None and v is not None:
                try:
                    simvalues[n.text] = float(v.text)
                except (ValueError, TypeError):
                    pass
    data["simvalues"] = simvalues

    # ---- Finances ----
    fin: Dict[str, float] = {}
    if finances_elem is not None:
        field_map = {
            "_0": "income",
            "_1": "expenditure",
            "_3": "interest_rate",
            "_5": "debt",
            "_6": "credit_value",
        }
        for tag, key in field_map.items():
            elem = finances_elem.find(tag)
            if elem is not None:
                try:
                    fin[key] = float(elem.text)
                except (ValueError, TypeError):
                    pass
        cr = finances_elem.find("creditrating")
        if cr is not None:
            fin["credit_rating"] = cr.text
    data["finances"] = fin

    # Keep a reference to the raw text for patching
    data["_raw"] = path.read_text(encoding="utf-8")

    return data


def file_hash(path: Path) -> str:
    """Fast hash of file contents for change detection."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except OSError:
        return ""


# =============================================================================
# YIELD / INTEREST RATE ENGINE
# =============================================================================

def yield_to_rate(yield_val: float) -> float:
    """
    Convert a 0–1 simulation yield value to an annual interest rate.
    Uses a non-linear mapping:
      yield 0.0  → 0.1% (floor)
      yield 0.05 → ~1%
      yield 0.15 → ~3%
      yield 0.30 → ~6%
      yield 0.50 → ~10%
      yield 1.0  → 25% (cap)
    """
    # Quadratic mapping gives sensible real-world rates
    rate = YIELD_FLOOR + (YIELD_CAP - YIELD_FLOOR) * (yield_val ** 1.5)
    return max(YIELD_FLOOR, min(YIELD_CAP, rate))


def compute_blended_rate(short: float, medium: float, long: float) -> float:
    """
    Weighted blend of the three yield tenors → single market rate
    that new debt is issued at this quarter.
    """
    rs = yield_to_rate(short)
    rm = yield_to_rate(medium)
    rl = yield_to_rate(long)
    return WEIGHT_SHORT * rs + WEIGHT_MEDIUM * rm + WEIGHT_LONG * rl


def update_maturity_model(
    tranches: List[DebtTranche],
    current_market_rate: float,
) -> Tuple[List[DebtTranche], float]:
    """
    Roll the maturity model forward one quarter.

    - Tranches with quarters_remaining == 0 mature and are re-issued at the
      current market rate.
    - Returns updated tranche list and the weighted-average cost of debt.
    """
    if not tranches:
        # Initialise: uniform distribution across all tenors at current rate
        share = 1.0 / MATURITY_TRANCHES
        tranches = [
            DebtTranche(
                annual_rate=current_market_rate,
                share=share,
                quarters_remaining=i + 1,
            )
            for i in range(MATURITY_TRANCHES)
        ]

    # Age all tranches by one quarter
    for t in tranches:
        t.quarters_remaining -= 1

    # Mature and roll over
    for t in tranches:
        if t.quarters_remaining <= 0:
            t.annual_rate = current_market_rate
            t.quarters_remaining = MATURITY_TRANCHES  # re-issue for full term

    # Normalise shares (safety net)
    total_share = sum(t.share for t in tranches)
    if total_share > 0:
        for t in tranches:
            t.share /= total_share

    # Weighted average interest rate across all outstanding tranches
    wavg = sum(t.annual_rate * t.share for t in tranches)
    return tranches, wavg


# =============================================================================
# SOVEREIGN RISK → CREDIT RATING
# =============================================================================

def sovereign_risk_to_credit(sov_risk: float) -> Tuple[float, str]:
    """
    Convert the mod's SovereignRisk (0-1, higher=worse) to:
      - credit_value: the numeric value D4 uses internally (same 0-1 scale, higher=worse)
      - credit_rating: the letter grade string (e.g. "AAA", "BB", "CCC")

    The credit_value IS the SovereignRisk (direct passthrough) because both
    use the same 0-1 scale and direction. The simconfig thresholds convert
    this to a letter grade.
    """
    credit_value = max(0.0, min(1.0, sov_risk))

    # Walk the threshold table to find the letter grade
    rating = "D"
    for threshold, grade in CREDIT_THRESHOLDS:
        if credit_value < threshold:
            rating = grade
            break

    return credit_value, rating


# =============================================================================
# SIMCONFIG PATCHING
# =============================================================================

def patch_simconfig(game_dir: Path) -> bool:
    """
    Apply mod overrides to the game's simconfig.txt.
    Creates a backup (.vanilla.bak) on first run so the original can be restored.
    Returns True on success.
    """
    simconfig_path = game_dir / "data" / "simconfig.txt"
    if not simconfig_path.exists():
        log(f"simconfig.txt not found at {simconfig_path}", "error")
        return False

    backup_path = simconfig_path.with_suffix(".vanilla.bak")

    # Read current simconfig
    try:
        content = simconfig_path.read_text(encoding="utf-8")
    except OSError as e:
        log(f"Cannot read simconfig.txt: {e}", "error")
        return False

    # Check if already patched (look for our marker)
    MARKER = "# REO_PATCHED"
    if MARKER in content:
        log("simconfig.txt already patched — skipping", "dim")
        return True

    # Backup the vanilla file (only if no backup exists yet)
    if not backup_path.exists():
        try:
            shutil.copy2(simconfig_path, backup_path)
            log(f"Backed up vanilla simconfig → {backup_path.name}", "ok")
        except OSError as e:
            log(f"Cannot backup simconfig.txt: {e}", "error")
            return False

    # Apply overrides: replace each key = old_value with key = new_value
    patched = content
    applied = 0
    for key, new_val in SIMCONFIG_OVERRIDES.items():
        # Match: KEY = value (with optional whitespace)
        pattern = rf"^({re.escape(key)}\s*=\s*)(.+)$"
        new_line = rf"\g<1>{new_val}"
        patched_new = re.sub(pattern, new_line, patched, count=1, flags=re.MULTILINE)
        if patched_new != patched:
            applied += 1
            patched = patched_new

    # Add marker at the end of the [config] section
    patched = patched.replace("[config]", f"[config]\n{MARKER}", 1)

    # Write back
    try:
        simconfig_path.write_text(patched, encoding="utf-8")
        log(f"Patched simconfig.txt: {applied}/{len(SIMCONFIG_OVERRIDES)} values updated", "ok")
        return True
    except OSError as e:
        log(f"Cannot write simconfig.txt: {e}", "error")
        return False


def restore_simconfig(game_dir: Path) -> bool:
    """Restore the vanilla simconfig.txt from backup."""
    simconfig_path = game_dir / "data" / "simconfig.txt"
    backup_path = simconfig_path.with_suffix(".vanilla.bak")
    if backup_path.exists():
        try:
            shutil.copy2(backup_path, simconfig_path)
            log("Restored vanilla simconfig.txt from backup", "ok")
            return True
        except OSError as e:
            log(f"Cannot restore simconfig.txt: {e}", "error")
            return False
    else:
        log("No vanilla simconfig backup found — nothing to restore", "warn")
        return False


# =============================================================================
# SAVE PATCHING
# =============================================================================

def patch_save(
    path: Path,
    raw: str,
    debt: float,
    effective_annual_rate: float,
    old_expenditure: float,
    old_income: float,
    credit_value: Optional[float] = None,
    credit_rating: Optional[str] = None,
) -> bool:
    """
    Write the patched values back into the save file.
    Patches: interest rate (<3>), credit value (<6>), credit rating (<creditrating>).
    Returns True on success.
    """
    quarterly_rate = effective_annual_rate / 4.0
    quarterly_interest = debt * quarterly_rate

    # The engine stores interest rate as a quarterly fraction
    patched = raw

    # Patch interest rate field: <finances> child element <3>
    # NOTE: the raw save uses bare numeric tags like <3>, not <_3>
    patched = re.sub(
        r"(<finances>.*?<3>)([\d.eE+-]+)(</3>)",
        lambda m: f"{m.group(1)}{quarterly_rate:.8f}{m.group(3)}",
        patched,
        count=1,
        flags=re.DOTALL,
    )

    # Patch credit value: <finances> child element <6>
    if credit_value is not None:
        patched = re.sub(
            r"(<finances>.*?<6>)([\d.eE+-]+)(</6>)",
            lambda m: f"{m.group(1)}{credit_value:.8f}{m.group(3)}",
            patched,
            count=1,
            flags=re.DOTALL,
        )

    # Patch credit rating: <finances> child element <creditrating>
    if credit_rating is not None:
        patched = re.sub(
            r"(<finances>.*?<creditrating>)([^<]*)(</creditrating>)",
            lambda m: f"{m.group(1)}{credit_rating}{m.group(3)}",
            patched,
            count=1,
            flags=re.DOTALL,
        )

    # We don't directly patch expenditure or deficit — the engine recalculates
    # those from the interest rate on reload. We only need to set the rate.
    # This is the safer approach per v2 experience.

    # Write atomically: write to temp, then rename
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(patched, encoding="utf-8")
        # On Windows, can't rename over existing — remove first
        if path.exists():
            path.unlink()
        tmp.rename(path)
        return True
    except OSError as e:
        log(f"Write error: {e}", "error")
        # Try to restore from backup
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return False


# =============================================================================
# GAME DETECTION
# =============================================================================

def is_game_running() -> bool:
    """Check whether Democracy4.exe is currently running."""
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {GAME_PROCESS_NAME}", "/NH"],
                stderr=subprocess.DEVNULL,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
            return GAME_PROCESS_NAME.lower() in output.lower()
        except (subprocess.SubprocessError, OSError):
            return False
    else:
        # Linux/Mac fallback
        try:
            output = subprocess.check_output(["pgrep", "-i", "democracy"], stderr=subprocess.DEVNULL, text=True)
            return bool(output.strip())
        except (subprocess.SubprocessError, OSError):
            return False


# =============================================================================
# SOUND NOTIFICATION
# =============================================================================

def play_notification():
    """Play a short beep / notification sound on successful patch."""
    if platform.system() == "Windows":
        try:
            import winsound
            # 750 Hz for 200ms — a pleasant "ding"
            winsound.Beep(750, 200)
        except Exception:
            pass
    else:
        # Terminal bell fallback
        sys.stdout.write("\a")
        sys.stdout.flush()


# =============================================================================
# STATE PERSISTENCE
# =============================================================================

def load_state(save_dir: Path) -> PatcherState:
    """Load persistent patcher state from disk."""
    state_path = save_dir / STATE_FILE_NAME
    if state_path.exists():
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            state = PatcherState.from_dict(data)
            log(f"Loaded state: turn {state.last_turn}, {state.patches_applied} patches applied", "dim")
            return state
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            log(f"State file corrupt ({e}), starting fresh", "warn")
    return PatcherState(session_start=datetime.now().isoformat())


def save_state(save_dir: Path, state: PatcherState):
    """Persist patcher state to disk."""
    state_path = save_dir / STATE_FILE_NAME
    try:
        state_path.write_text(
            json.dumps(state.to_dict(), indent=2),
            encoding="utf-8",
        )
    except OSError as e:
        log(f"Could not save state: {e}", "warn")


# =============================================================================
# CONSOLE OUTPUT
# =============================================================================

def log(msg: str, level: str = "info"):
    """Print a timestamped, colour-coded log message."""
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "info":    f"{C.DIM}[{ts}]{C.RESET} {C.CYAN}INFO{C.RESET}  ",
        "ok":      f"{C.DIM}[{ts}]{C.RESET} {C.GREEN}OK{C.RESET}    ",
        "warn":    f"{C.DIM}[{ts}]{C.RESET} {C.YELLOW}WARN{C.RESET}  ",
        "error":   f"{C.DIM}[{ts}]{C.RESET} {C.RED}ERROR{C.RESET} ",
        "patch":   f"{C.DIM}[{ts}]{C.RESET} {C.GREEN}{C.BOLD}PATCH{C.RESET} ",
        "dim":     f"{C.DIM}[{ts}] ...   ",
        "header":  f"{C.DIM}[{ts}]{C.RESET} ",
    }.get(level, f"{C.DIM}[{ts}]{C.RESET}       ")
    end = C.RESET if level == "dim" else ""
    print(f"{prefix}{msg}{end}")


def print_banner():
    """Print the startup banner."""
    print()
    print(f"  {C.BOLD}{C.CYAN}╔══════════════════════════════════════════════╗{C.RESET}")
    print(f"  {C.BOLD}{C.CYAN}║  Democracy 4 — Realistic Economics Overhaul ║{C.RESET}")
    print(f"  {C.BOLD}{C.CYAN}║          Save Patcher v{VERSION}              ║{C.RESET}")
    print(f"  {C.BOLD}{C.CYAN}╚══════════════════════════════════════════════╝{C.RESET}")
    print()


def credit_colour(rating: str) -> str:
    """Return an ANSI colour code appropriate for the credit rating."""
    if rating in ("AAA", "AA"):
        return C.GREEN
    elif rating in ("A", "BBB"):
        return C.CYAN
    elif rating in ("BB", "B"):
        return C.YELLOW
    else:
        return C.RED


def print_dashboard(
    data: dict, rate: float, wavg: float, state: PatcherState,
    credit_rating: str = "?", credit_value: float = 0.0, sov_risk: float = 0.0,
):
    """Print a compact dashboard after a successful patch."""
    sv = data.get("simvalues", {})
    fin = data.get("finances", {})
    mission = data.get("mission", "?")
    turn = data.get("turn", 0)

    short  = sv.get("ShortTermYield", 0)
    medium = sv.get("MediumTermYield", 0)
    long   = sv.get("LongTermYield", 0)
    debt   = fin.get("debt", 0)

    rs = yield_to_rate(short)
    rm = yield_to_rate(medium)
    rl = yield_to_rate(long)

    quarterly_interest = debt * (wavg / 4.0)
    cc = credit_colour(credit_rating)

    print()
    print(f"  {C.BOLD}┌─────────────────────────────────────────────┐{C.RESET}")
    print(f"  {C.BOLD}│{C.RESET}  {C.CYAN}{mission.upper():^10}{C.RESET}  Turn {C.BOLD}{turn}{C.RESET}  │  Patch #{C.BOLD}{state.patches_applied}{C.RESET}      {C.BOLD}│{C.RESET}")
    print(f"  {C.BOLD}├─────────────────────────────────────────────┤{C.RESET}")
    print(f"  {C.BOLD}│{C.RESET}  Yields:  Short {C.YELLOW}{rs*100:5.2f}%{C.RESET}  ({short:.3f})          {C.BOLD}│{C.RESET}")
    print(f"  {C.BOLD}│{C.RESET}           Med   {C.YELLOW}{rm*100:5.2f}%{C.RESET}  ({medium:.3f})          {C.BOLD}│{C.RESET}")
    print(f"  {C.BOLD}│{C.RESET}           Long  {C.YELLOW}{rl*100:5.2f}%{C.RESET}  ({long:.3f})          {C.BOLD}│{C.RESET}")
    print(f"  {C.BOLD}│{C.RESET}  Market rate:    {C.BOLD}{C.WHITE}{rate*100:5.2f}%{C.RESET}                  {C.BOLD}│{C.RESET}")
    print(f"  {C.BOLD}│{C.RESET}  Eff. WAVG rate: {C.BOLD}{C.GREEN}{wavg*100:5.2f}%{C.RESET}                  {C.BOLD}│{C.RESET}")
    print(f"  {C.BOLD}│{C.RESET}  Debt:           {C.WHITE}{debt:,.0f}{C.RESET} bn              {C.BOLD}│{C.RESET}")
    print(f"  {C.BOLD}│{C.RESET}  Qtr interest:   {C.WHITE}{quarterly_interest:,.1f}{C.RESET} bn              {C.BOLD}│{C.RESET}")
    print(f"  {C.BOLD}├─────────────────────────────────────────────┤{C.RESET}")
    print(f"  {C.BOLD}│{C.RESET}  Credit rating:  {cc}{C.BOLD}{credit_rating:>4}{C.RESET}  (SovRisk {sov_risk:.3f})  {C.BOLD}│{C.RESET}")
    print(f"  {C.BOLD}│{C.RESET}  Credit value:   {C.WHITE}{credit_value:.4f}{C.RESET}                    {C.BOLD}│{C.RESET}")
    print(f"  {C.BOLD}└─────────────────────────────────────────────┘{C.RESET}")
    print()


# =============================================================================
# MAIN LOOP
# =============================================================================

class Patcher:
    """The main patcher controller."""

    def __init__(self, save_dir: Path, game_dir: Path, once: bool = False):
        self.save_dir = save_dir
        self.game_dir = game_dir
        self.autosave_path = save_dir / AUTOSAVE_NAME
        self.once = once
        self.running = True
        self.state = load_state(save_dir)
        if not self.state.session_start:
            self.state.session_start = datetime.now().isoformat()

    def stop(self, *_):
        """Signal handler for graceful shutdown."""
        self.running = False
        print()
        log("Shutting down gracefully...", "info")

    def run(self):
        """Main entry point."""
        print_banner()

        # Validate save directory
        if not self.save_dir.exists():
            log(f"Save directory not found: {self.save_dir}", "error")
            log("Use --savedir to specify the correct path.", "info")
            return 1

        log(f"Save directory: {C.WHITE}{self.save_dir}{C.RESET}", "info")
        log(f"Game directory: {C.WHITE}{self.game_dir}{C.RESET}", "info")
        log(f"Watching: {C.WHITE}{AUTOSAVE_NAME}{C.RESET}", "info")

        # Apply simconfig overrides to game directory
        if self.game_dir.exists():
            patch_simconfig(self.game_dir)
        else:
            log(f"Game directory not found — simconfig not patched", "warn")
            log("Use --gamedir to specify the correct path.", "info")

        # Check if game is running
        if is_game_running():
            log(f"{C.GREEN}Democracy 4 is running{C.RESET}", "ok")
        else:
            log(f"Democracy 4 not detected — will watch anyway", "warn")

        # Register signal handlers
        signal.signal(signal.SIGINT, self.stop)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self.stop)

        log(f"Waiting for autosave changes... {C.DIM}(Ctrl+C to quit){C.RESET}", "info")
        print()

        last_hash = self.state.last_hash
        game_check_counter = 0

        while self.running:
            time.sleep(POLL_INTERVAL)

            # Periodically check if game is still running (every 30s)
            game_check_counter += 1
            if game_check_counter >= 30:
                game_check_counter = 0
                if not is_game_running():
                    log("Game not detected — still watching...", "dim")

            # Check for file change
            if not self.autosave_path.exists():
                continue

            current_hash = file_hash(self.autosave_path)
            if not current_hash or current_hash == last_hash:
                continue

            # File has changed — wait a moment for the write to finish
            time.sleep(0.5)
            confirm_hash = file_hash(self.autosave_path)
            if confirm_hash != current_hash:
                # File is still being written, wait and retry
                time.sleep(1.0)
                current_hash = file_hash(self.autosave_path)

            log("Autosave change detected!", "info")

            # Back up before patching
            backup_path = self.autosave_path.with_suffix(".bak")
            try:
                shutil.copy2(self.autosave_path, backup_path)
            except OSError as e:
                log(f"Backup failed: {e}", "error")

            success = self.apply_patch()

            if success:
                last_hash = file_hash(self.autosave_path)  # hash of patched file
                self.state.last_hash = last_hash
                save_state(self.save_dir, self.state)
                play_notification()
                log(f"Press {C.BOLD}F9{C.RESET} in-game to reload the patched autosave", "ok")
            else:
                last_hash = current_hash  # don't re-trigger on the same file

            if self.once:
                break

        # Clean exit
        save_state(self.save_dir, self.state)
        log(f"Session total: {C.BOLD}{self.state.patches_applied}{C.RESET} patches applied", "info")
        log("Goodbye!", "ok")
        return 0

    def apply_patch(self) -> bool:
        """Parse the autosave and apply interest rate + credit rating patches."""
        data = parse_save(self.autosave_path)
        if data is None:
            log("Failed to parse autosave (file may be corrupt or mid-write)", "error")
            return False

        sv = data.get("simvalues", {})
        fin = data.get("finances", {})

        # Extract yields
        short  = sv.get("ShortTermYield", 0.15)
        medium = sv.get("MediumTermYield", 0.15)
        long   = sv.get("LongTermYield", 0.15)
        debt   = fin.get("debt", 0)
        income = fin.get("income", 0)
        expenditure = fin.get("expenditure", 0)
        turn = data.get("turn", 0)

        # Extract SovereignRisk for credit rating patching
        sov_risk = sv.get("SovereignRisk", 0.25)  # default 0.25 = BBB baseline
        credit_value, credit_rating = sovereign_risk_to_credit(sov_risk)

        if debt <= 0:
            # Even with no debt, still patch credit rating (it's meaningful)
            log(f"Debt is {debt:.0f} — patching credit only (surplus country?)", "info")

        # Detect turn change — but always patch if the save is different
        # (the engine overwrites our patched values on reload/new turn)
        # We skip ONLY if the turn AND hash are both unchanged (double-patch guard)
        current_hash = file_hash(self.autosave_path)
        if turn <= self.state.last_turn and self.state.last_turn > 0:
            if current_hash == self.state.last_hash:
                log(f"Turn {turn} ≤ last patched turn {self.state.last_turn} and hash unchanged — skipping", "dim")
                return False
            else:
                log(f"Turn {turn} — save changed (engine overwrote patch), re-patching", "info")

        # Compute the current market rate from yields
        market_rate = compute_blended_rate(short, medium, long)

        # Update the maturity model
        tranches = self.state.get_tranches()
        tranches, wavg_rate = update_maturity_model(tranches, market_rate)
        self.state.set_tranches(tranches)

        # Patch the save — interest rate + credit value + credit rating
        success = patch_save(
            self.autosave_path,
            data["_raw"],
            debt,
            wavg_rate,
            expenditure,
            income,
            credit_value=credit_value,
            credit_rating=credit_rating,
        )

        if not success:
            return False

        # Update state
        self.state.last_turn = turn
        self.state.last_blended_rate = wavg_rate
        self.state.patches_applied += 1

        # Dashboard output
        log(f"Turn {turn} patched — rate {wavg_rate*100:.2f}% | credit {credit_rating} ({credit_value:.3f}) | SovRisk {sov_risk:.3f}", "patch")
        print_dashboard(data, market_rate, wavg_rate, self.state, credit_rating, credit_value, sov_risk)

        return True


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Democracy 4 — Realistic Economics Overhaul Save Patcher",
    )
    parser.add_argument(
        "--savedir",
        type=Path,
        default=DEFAULT_SAVE_DIR,
        help=f"Path to the savegames directory (default: {DEFAULT_SAVE_DIR})",
    )
    parser.add_argument(
        "--gamedir",
        type=Path,
        default=DEFAULT_GAME_DIR,
        help=f"Path to the Democracy 4 install directory (default: {DEFAULT_GAME_DIR})",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Patch once and exit (don't watch for changes)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset patcher state (clear maturity model and start fresh)",
    )
    parser.add_argument(
        "--restore-simconfig",
        action="store_true",
        help="Restore the vanilla simconfig.txt from backup and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"D4 Economics Patcher v{VERSION}",
    )

    args = parser.parse_args()

    if args.restore_simconfig:
        print_banner()
        restore_simconfig(args.gamedir)
        return 0

    if args.reset:
        state_path = args.savedir / STATE_FILE_NAME
        if state_path.exists():
            state_path.unlink()
            print(f"State reset: deleted {state_path}")
        else:
            print("No state file found — already clean.")
        if not args.once:
            return 0

    patcher = Patcher(save_dir=args.savedir, game_dir=args.gamedir, once=args.once)
    return patcher.run()


if __name__ == "__main__":
    sys.exit(main() or 0)
