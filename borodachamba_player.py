#!/usr/bin/env python3
"""
Borodachamba Player - a warm htop-style terminal MP3 player.

Runtime dependencies:
  - Python stdlib curses
  - ffplay for playback
  - ffprobe for track duration metadata
"""

from __future__ import annotations

import curses
import json
import locale
import math
import os
import random
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


AUDIO_EXTS = {
    ".mp3",
    ".flac",
    ".ogg",
    ".wav",
    ".m4a",
    ".aac",
    ".opus",
    ".wma",
}


LOGO = [
    r"██████╗  ██████╗ ██████╗  ██████╗ ██████╗  █████╗  ██████╗██╗  ██╗ █████╗ ███╗   ███╗██████╗  █████╗",
    r"██╔══██╗██╔═══██╗██╔══██╗██╔═══██╗██╔══██╗██╔══██╗██╔════╝██║  ██║██╔══██╗████╗ ████║██╔══██╗██╔══██╗",
    r"██████╔╝██║   ██║██████╔╝██║   ██║██║  ██║███████║██║     ███████║███████║██╔████╔██║██████╔╝███████║",
    r"██╔══██╗██║   ██║██╔══██╗██║   ██║██║  ██║██╔══██║██║     ██╔══██║██╔══██║██║╚██╔╝██║██╔══██╗██╔══██║",
    r"██████╔╝╚██████╔╝██║  ██║╚██████╔╝██████╔╝██║  ██║╚██████╗██║  ██║██║  ██║██║ ╚═╝ ██║██████╔╝██║  ██║",
    r"╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═════╝ ╚═╝  ╚═╝",
    r"                                   BORODACHAMBA MUSIC v1.0                                    ",
]

COPYRIGHT_TEXT = "Borodachamba Studio open-source by Nick Antonov (2000-2026)"
LICENSE_TEXT = "Licensed under GNU GPL v3.0 only"


HELP = (
    "Space play/pause  Enter play  o open  a add  d dsp reset  D delete  c clear  "
    "n/p next/prev  Left/Right seek  r repeat  h shuffle  m mute  u resume  v visual  i about  x dsp mode  b/B bass  +/- volume  </> tone  [/] dsp  e eq  l/w playlist  t/F7/F8 theme  q quit"
)

VISUAL_STYLES = [
    "deck flow",
    "pacman medusa",
    "pixel rain",
    "scanner",
    "matrix",
    "sine wave",
    "spark field",
    "mirror bars",
    "retro fire",
    "orbit",
]


COLOR_SCHEMES = [
    ("Amber CRT", "cyan", "yellow", "green", "red", "yellow", "magenta", "cyan"),
    ("Green Phosphor", "green", "green", "green", "yellow", "green", "cyan", "green"),
    ("Blue Night", "blue", "cyan", "blue", "red", "cyan", "magenta", "cyan"),
    ("Solar Workbench", "yellow", "white", "green", "red", "yellow", "blue", "white"),
    ("Magenta Tape", "magenta", "magenta", "cyan", "red", "magenta", "yellow", "cyan"),
    ("Red Alert Soft", "red", "yellow", "green", "red", "red", "magenta", "yellow"),
    ("Cyan Glass", "cyan", "cyan", "white", "red", "cyan", "blue", "white"),
    ("Mono Terminal", "white", "white", "white", "red", "white", "white", "white"),
    ("IBM 5150", "blue", "white", "cyan", "red", "white", "yellow", "cyan"),
    ("Midnight Oil", "blue", "cyan", "green", "red", "cyan", "blue", "white"),
    ("Violet Desk", "magenta", "white", "green", "red", "white", "cyan", "magenta"),
    ("Copper Wire", "yellow", "yellow", "red", "magenta", "yellow", "green", "white"),
    ("Mint Console", "green", "cyan", "green", "red", "cyan", "white", "green"),
    ("Arctic TTY", "white", "cyan", "blue", "red", "white", "cyan", "white"),
    ("Hotline", "red", "white", "yellow", "red", "white", "magenta", "yellow"),
    ("Deep Sea", "blue", "green", "cyan", "red", "green", "cyan", "white"),
    ("Workshop", "yellow", "green", "yellow", "red", "green", "cyan", "yellow"),
    ("Purple Haze", "magenta", "cyan", "magenta", "red", "cyan", "yellow", "white"),
    ("Old Kernel", "green", "yellow", "green", "red", "yellow", "cyan", "green"),
    ("Paperwhite", "white", "black", "black", "red", "white", "blue", "black"),
    ("Neon Rack", "cyan", "magenta", "green", "red", "magenta", "yellow", "cyan"),
    ("DOS Blue", "blue", "white", "cyan", "red", "white", "yellow", "white"),
    ("Rusty Lamp", "yellow", "red", "yellow", "magenta", "red", "green", "yellow"),
    ("Icebreaker", "cyan", "white", "blue", "red", "white", "magenta", "cyan"),
    ("Matrix Soft", "green", "green", "white", "red", "green", "yellow", "green"),
    ("Broadcast", "magenta", "yellow", "cyan", "red", "yellow", "white", "cyan"),
    ("Low Light", "blue", "green", "cyan", "red", "green", "blue", "white"),
    ("Sunset TTY", "red", "yellow", "magenta", "red", "yellow", "cyan", "white"),
    ("Steel Room", "white", "blue", "cyan", "red", "blue", "magenta", "white"),
    ("Warm Linux", "yellow", "green", "green", "red", "yellow", "magenta", "cyan"),
]


CURSES_COLORS = {
    "black": curses.COLOR_BLACK,
    "red": curses.COLOR_RED,
    "green": curses.COLOR_GREEN,
    "yellow": curses.COLOR_YELLOW,
    "blue": curses.COLOR_BLUE,
    "magenta": curses.COLOR_MAGENTA,
    "cyan": curses.COLOR_CYAN,
    "white": curses.COLOR_WHITE,
}


EQ_PRESETS = [
    ("flat", 0, 0),
    ("rock", 5, 4),
    ("jazz", 3, 2),
    ("vocal", 4, 0),
    ("bass boost", 1, 5),
]


DSP_MODES = [
    ("stereo", "panorama"),
    ("echo", "echo"),
    ("chorus", "chorus"),
    ("reverb", "reverb"),
    ("phaser", "phaser"),
    ("flanger", "flanger"),
]


LAYOUT_KEY_TO_LATIN = {
    "й": "q",
    "ц": "w",
    "у": "e",
    "к": "r",
    "е": "t",
    "н": "y",
    "г": "u",
    "ш": "i",
    "щ": "o",
    "з": "p",
    "ф": "a",
    "ы": "s",
    "і": "s",
    "в": "d",
    "а": "f",
    "п": "g",
    "р": "h",
    "о": "j",
    "л": "k",
    "д": "l",
    "я": "z",
    "ч": "x",
    "с": "c",
    "м": "v",
    "и": "b",
    "т": "n",
    "ь": "m",
}

CONFIG_DIR = Path.home() / ".config" / "borodachamba-player"
CONFIG_FILE = CONFIG_DIR / "config.json"
PLAYLIST_FILE = CONFIG_DIR / "playlist.m3u"


@dataclass
class Track:
    path: Path
    duration: float | None = None

    @property
    def title(self) -> str:
        return self.path.name


class AudioEngine:
    def __init__(self) -> None:
        self.proc: subprocess.Popen[bytes] | None = None
        self.current: Track | None = None
        self.started_at = 0.0
        self.paused_at: float | None = None
        self.paused_total = 0.0

    def build_filter(self, volume: int, tone: int, dsp: int, dsp_mode: str, bass_boost: int) -> str:
        filters = [f"volume={max(0, volume) / 100:.2f}"]
        if bass_boost > 0:
            filters.append(f"bass=g={bass_boost}")
            filters.append("lowshelf=f=110:g=2.5")
        if tone:
            filters.append(f"equalizer=f=1200:width_type=o:width=1.6:g={tone}")
            filters.append(f"treble=g={tone / 2:.1f}")
        if dsp:
            depth = max(0.0, min(1.0, dsp / 12.0))
            if dsp_mode == "echo":
                delay_ms = int(85 + depth * 170)
                decay = 0.18 + depth * 0.42
                filters.append(f"aecho=0.85:0.72:{delay_ms}:{decay:.2f}")
            elif dsp_mode == "chorus":
                delay_a = int(24 + depth * 18)
                delay_b = int(34 + depth * 22)
                decay_a = 0.20 + depth * 0.28
                decay_b = 0.15 + depth * 0.22
                speed_a = 0.18 + depth * 0.42
                speed_b = 0.12 + depth * 0.36
                depth_a = 1.2 + depth * 2.8
                depth_b = 0.8 + depth * 2.2
                filters.append(
                    f"chorus=0.55:0.88:{delay_a}|{delay_b}:{decay_a:.2f}|{decay_b:.2f}:{speed_a:.2f}|{speed_b:.2f}:{depth_a:.1f}|{depth_b:.1f}"
                )
            elif dsp_mode == "reverb":
                d1 = int(35 + depth * 40)
                d2 = int(95 + depth * 85)
                d3 = int(160 + depth * 130)
                g1 = 0.34 + depth * 0.16
                g2 = 0.24 + depth * 0.14
                g3 = 0.14 + depth * 0.11
                filters.append(f"aecho=0.80:0.88:{d1}|{d2}|{d3}:{g1:.2f}|{g2:.2f}|{g3:.2f}")
            elif dsp_mode == "phaser":
                in_gain = 0.45 + depth * 0.15
                out_gain = 0.70 + depth * 0.12
                delay = 1.5 + depth * 2.2
                decay = 0.2 + depth * 0.55
                speed = 0.2 + depth * 0.9
                filters.append(
                    f"aphaser=in_gain={in_gain:.2f}:out_gain={out_gain:.2f}:delay={delay:.2f}:decay={decay:.2f}:speed={speed:.2f}:type=s"
                )
            elif dsp_mode == "flanger":
                delay = 2.0 + depth * 8.0
                depth_v = 1.0 + depth * 3.0
                regen = -40 + depth * 70
                width = 45 + depth * 45
                speed = 0.12 + depth * 0.55
                filters.append(
                    f"flanger=delay={delay:.1f}:depth={depth_v:.1f}:regen={regen:.1f}:width={width:.1f}:speed={speed:.2f}"
                )
            else:
                width = 1.0 + depth * 1.6
                filters.append(f"extrastereo=m={width:.2f}")
        return ",".join(filters)

    def play(
        self,
        track: Track,
        volume: int,
        tone: int,
        dsp: int,
        dsp_mode: str,
        bass_boost: int,
        start_at: float = 0.0,
        paused: bool = False,
    ) -> str | None:
        self.stop()
        afilter = self.build_filter(volume, tone, dsp, dsp_mode, bass_boost)
        cmd = [
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-hide_banner",
            "-loglevel",
            "quiet",
            "-af",
            afilter,
        ]
        if start_at > 0.5:
            cmd.extend(["-ss", f"{start_at:.2f}"])
        cmd.append(str(track.path))
        try:
            popen_kwargs: dict[str, object] = {
                "stdin": subprocess.PIPE,
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            if os.name == "nt":
                create_group = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                if create_group:
                    popen_kwargs["creationflags"] = create_group
            else:
                popen_kwargs["start_new_session"] = True
            self.proc = subprocess.Popen(cmd, **popen_kwargs)
        except FileNotFoundError:
            self.proc = None
            return "ffplay not found"
        except OSError as exc:
            self.proc = None
            return str(exc)
        self.current = track
        self.started_at = time.monotonic() - max(0.0, start_at)
        self.paused_at = None
        self.paused_total = 0.0
        if paused:
            self.paused_at = time.monotonic()
        return None

    def stop(self, clear_current: bool = True) -> None:
        proc = self.proc
        if not proc:
            if clear_current:
                self.current = None
                self.paused_at = None
            return
        try:
            if proc.stdin:
                proc.stdin.write(b"q")
                proc.stdin.flush()
        except OSError:
            pass

        try:
            proc.wait(timeout=0.25)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                self.kill_process_tree_windows(proc.pid)
                try:
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    try:
                        proc.kill()
                    except OSError:
                        pass
            else:
                self.terminate_process(proc, force=False)
                try:
                    proc.wait(timeout=0.8)
                except subprocess.TimeoutExpired:
                    self.terminate_process(proc, force=True)
                    try:
                        proc.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        pass
        self.proc = None
        if clear_current:
            self.current = None
            self.paused_at = None

    def terminate_process(self, proc: subprocess.Popen[bytes], force: bool) -> None:
        if os.name == "nt":
            self.kill_process_tree_windows(proc.pid)
            return
        sig = signal.SIGKILL if force else signal.SIGTERM
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        except OSError:
            try:
                proc.send_signal(sig)
            except OSError:
                pass

    def kill_process_tree_windows(self, pid: int) -> None:
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pass

    def send_runtime_key(self, key: str) -> bool:
        if not key or not self.proc or self.proc.poll() is not None:
            return False
        try:
            if not self.proc.stdin:
                return False
            self.proc.stdin.write(key.encode("ascii", "ignore"))
            self.proc.stdin.flush()
            return True
        except OSError:
            return False

    def change_volume_runtime(self, delta: int) -> bool:
        if delta == 0:
            return True
        key = "0" if delta > 0 else "9"
        steps = max(1, abs(delta) // 5)
        ok = True
        for _ in range(steps):
            ok = self.send_runtime_key(key) and ok
        return ok

    def elapsed(self) -> float:
        if not self.current:
            return 0.0
        end = self.paused_at if self.paused_at is not None else time.monotonic()
        return max(0.0, end - self.started_at - self.paused_total)

    def is_playing(self) -> bool:
        return bool(self.proc and self.proc.poll() is None and self.paused_at is None)

    def finished(self) -> bool:
        return bool(self.proc and self.proc.poll() is not None)


class VuField:
    def __init__(self) -> None:
        self.levels: list[float] = [0.0] * 24
        self.bits: list[tuple[float, float, int]] = []

    def step(self, active: bool, volume: int, dsp: int) -> None:
        drive = volume / 100.0 * (1.0 + abs(dsp) / 18.0)
        for i, old in enumerate(self.levels):
            wave = 0.5 + 0.5 * math.sin(time.monotonic() * (2.8 + i / 9) + i)
            target = random.random() * drive if active else 0.04 * random.random()
            target = max(target, wave * drive * random.random() if active else target)
            self.levels[i] = max(old * 0.78, min(1.0, target))
            if active and old > 0.72 and random.random() < 0.13:
                self.bits.append((float(i), self.levels[i] * 8.0, random.choice([2, 3, 4, 6])))
        next_bits = []
        for x, y, color_id in self.bits[-90:]:
            y -= random.uniform(0.35, 0.9)
            x += random.uniform(-0.35, 0.35)
            if y > 0:
                next_bits.append((x, y, color_id))
        self.bits = next_bits


class App:
    def __init__(self, screen: curses.window) -> None:
        self.screen = screen
        self.playlist: list[Track] = []
        self.selected = 0
        self.scroll = 0
        self.browser_path = Path.cwd()
        self.browser_items: list[Path] = []
        self.browser_marked: set[Path] = set()
        self.browser_selected = 0
        self.browser_scroll = 0
        self.browser_open = False
        self.engine = AudioEngine()
        self.vu = VuField()
        self.volume = 80
        self.tone = 0
        self.dsp = 2
        self.dsp_mode_index = 0
        self.bass_boost = 0
        self.theme_index = 0
        self.eq_preset_index = 0
        self.repeat_mode = "all"
        self.shuffle_enabled = False
        self.muted = False
        self.pre_mute_volume = self.volume
        self.pending_reconfigure_at: float | None = None
        self.resume_track_path: Path | None = None
        self.resume_position = 0.0
        self.resume_autoplay = True
        self.visual_style_index = 0
        self.about_open = False
        self.status = "Press o to open files or folders"
        self.running = True
        self.load_config()
        self.load_playlist(announce=False)

    def setup(self) -> None:
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        try:
            curses.set_escdelay(120)
        except AttributeError:
            pass
        self.screen.timeout(50)
        self.screen.keypad(True)
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        except curses.error:
            pass
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            self.apply_theme()
        self.refresh_browser()

    def apply_theme(self) -> None:
        if not curses.has_colors():
            return
        scheme = COLOR_SCHEMES[self.theme_index]
        highlight, logo, good, danger, badge, status, muted = [
            CURSES_COLORS[name] for name in scheme[1:]
        ]
        curses.init_pair(1, curses.COLOR_BLACK, highlight)
        curses.init_pair(2, logo, -1)
        curses.init_pair(3, good, -1)
        curses.init_pair(4, danger, -1)
        curses.init_pair(5, curses.COLOR_BLACK, badge)
        curses.init_pair(6, status, -1)
        curses.init_pair(7, muted, -1)

    def switch_theme(self, delta: int) -> None:
        self.theme_index = (self.theme_index + delta) % len(COLOR_SCHEMES)
        self.apply_theme()
        self.save_config()
        self.status = f"Theme {self.theme_index + 1}/{len(COLOR_SCHEMES)}: {COLOR_SCHEMES[self.theme_index][0]}"

    def set_eq_preset(self, index: int, restart: bool = True) -> None:
        self.eq_preset_index = max(0, min(index, len(EQ_PRESETS) - 1))
        _, tone, dsp = EQ_PRESETS[self.eq_preset_index]
        self.tone = tone
        self.dsp = max(0, min(12, dsp))
        self.save_config()
        if restart:
            self.restart_if_active()
        self.status = f"EQ preset: {EQ_PRESETS[self.eq_preset_index][0]}"

    def cycle_eq_preset(self, delta: int) -> None:
        next_index = (self.eq_preset_index + delta) % len(EQ_PRESETS)
        self.set_eq_preset(next_index)

    def load_config(self) -> None:
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        theme_index = int(data.get("theme_index", 0))
        self.theme_index = max(0, min(theme_index, len(COLOR_SCHEMES) - 1))
        eq_preset_index = int(data.get("eq_preset_index", 0))
        self.eq_preset_index = max(0, min(eq_preset_index, len(EQ_PRESETS) - 1))
        _, preset_tone, preset_dsp = EQ_PRESETS[self.eq_preset_index]
        self.tone = int(data.get("tone", preset_tone))
        self.tone = max(-12, min(12, self.tone))
        self.dsp = int(data.get("dsp", max(0, preset_dsp)))
        self.dsp = max(0, min(12, self.dsp))
        self.volume = int(data.get("volume", self.volume))
        self.volume = max(0, min(150, self.volume))
        dsp_mode_index = int(data.get("dsp_mode_index", 0))
        self.dsp_mode_index = max(0, min(dsp_mode_index, len(DSP_MODES) - 1))
        bass_boost = int(data.get("bass_boost", 0))
        self.bass_boost = max(0, min(18, bass_boost))
        self.repeat_mode = str(data.get("repeat_mode", self.repeat_mode))
        if self.repeat_mode not in {"all", "one", "off"}:
            self.repeat_mode = "all"
        self.shuffle_enabled = bool(data.get("shuffle_enabled", self.shuffle_enabled))
        self.muted = bool(data.get("muted", self.muted))
        self.pre_mute_volume = int(data.get("pre_mute_volume", self.pre_mute_volume))
        self.pre_mute_volume = max(1, min(150, self.pre_mute_volume))
        self.selected = int(data.get("selected_index", self.selected))
        self.selected = max(0, self.selected)
        resume_track = str(data.get("resume_track", "")).strip()
        self.resume_track_path = safe_resolve(Path(resume_track).expanduser()) if resume_track else None
        self.resume_position = float(data.get("resume_position", 0.0) or 0.0)
        self.resume_position = max(0.0, self.resume_position)
        self.resume_autoplay = bool(data.get("resume_autoplay", True))
        style_idx = int(data.get("visual_style_index", 0))
        self.visual_style_index = max(0, min(style_idx, len(VISUAL_STYLES) - 1))

    def save_config(self, announce: bool = True) -> None:
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            payload = {
                "theme_index": self.theme_index,
                "eq_preset_index": self.eq_preset_index,
                "volume": self.volume,
                "tone": self.tone,
                "dsp": self.dsp,
                "dsp_mode_index": self.dsp_mode_index,
                "bass_boost": self.bass_boost,
                "repeat_mode": self.repeat_mode,
                "shuffle_enabled": self.shuffle_enabled,
                "muted": self.muted,
                "pre_mute_volume": self.pre_mute_volume,
                "selected_index": self.selected,
                "resume_track": str(self.resume_track_path) if self.resume_track_path else "",
                "resume_position": round(self.resume_position, 3),
                "resume_autoplay": self.resume_autoplay,
                "visual_style_index": self.visual_style_index,
            }
            CONFIG_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            if announce:
                self.status = "Failed to save config"

    def save_playlist(self, announce: bool = True) -> None:
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            lines = ["#EXTM3U"]
            lines.extend(str(track.path) for track in self.playlist)
            PLAYLIST_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
            if announce:
                self.status = f"Playlist saved: {PLAYLIST_FILE}"
        except OSError:
            if announce:
                self.status = "Failed to save playlist"

    def load_playlist(self, announce: bool = True) -> None:
        try:
            lines = PLAYLIST_FILE.read_text(encoding="utf-8").splitlines()
        except OSError:
            if announce:
                self.status = f"Playlist file missing: {PLAYLIST_FILE}"
            return
        loaded = 0
        preferred_selected = self.selected
        self.playlist.clear()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            path = Path(line).expanduser()
            if path.is_file() and path.suffix.lower() in AUDIO_EXTS:
                self.playlist.append(Track(safe_resolve(path)))
                loaded += 1
        self.selected = min(max(0, preferred_selected), max(0, len(self.playlist) - 1))
        if announce:
            self.status = f"Playlist loaded: {loaded} track(s)"

    def add_path(self, path: Path) -> int:
        found = []
        if path.is_dir():
            for item in sorted(path.rglob("*")):
                if item.is_file() and item.suffix.lower() in AUDIO_EXTS:
                    found.append(item)
        elif path.is_file() and path.suffix.lower() in AUDIO_EXTS:
            found.append(path)
        known = {t.path.resolve() for t in self.playlist}
        added = 0
        for item in found:
            try:
                resolved = item.resolve()
            except OSError:
                continue
            if resolved in known:
                continue
            self.playlist.append(Track(resolved))
            known.add(resolved)
            added += 1
        if added:
            self.status = f"Added {added} track(s)"
        else:
            self.status = "No new audio files found"
        return added

    def refresh_browser(self) -> None:
        try:
            entries = list(self.browser_path.iterdir())
        except OSError as exc:
            self.status = str(exc)
            entries = []
        dirs = sorted([p for p in entries if p.is_dir() and not p.name.startswith(".")], key=lambda p: p.name.lower())
        files = sorted([p for p in entries if p.is_file() and p.suffix.lower() in AUDIO_EXTS], key=lambda p: p.name.lower())
        self.browser_items = [self.browser_path, self.browser_path.parent] + dirs + files
        visible_paths = {safe_resolve(item) for item in self.browser_items}
        self.browser_marked = {path for path in self.browser_marked if path in visible_paths}
        self.browser_selected = min(self.browser_selected, max(0, len(self.browser_items) - 1))

    def selected_browser_paths(self) -> list[Path]:
        if self.browser_marked:
            return sorted(self.browser_marked, key=lambda path: str(path).lower())
        if not self.browser_items:
            return []
        return [safe_resolve(self.browser_items[self.browser_selected])]

    def add_browser_selection(self) -> int:
        added = 0
        for path in self.selected_browser_paths():
            added += self.add_path(path)
        if self.browser_marked:
            self.status = f"Added selection: {added} track(s)"
            self.browser_marked.clear()
        return added

    def toggle_browser_mark(self) -> None:
        if not self.browser_items:
            return
        item = safe_resolve(self.browser_items[self.browser_selected])
        if item in self.browser_marked:
            self.browser_marked.remove(item)
        else:
            self.browser_marked.add(item)
        self.status = f"Marked {len(self.browser_marked)} item(s)"
        self.browser_selected = min(max(0, len(self.browser_items) - 1), self.browser_selected + 1)

    def play_selected(self, start_at: float = 0.0, paused: bool = False) -> None:
        if not self.playlist:
            self.status = "Playlist is empty"
            return
        self.pending_reconfigure_at = None
        self.selected = max(0, min(self.selected, len(self.playlist) - 1))
        if self.playlist[self.selected].duration is None:
            self.playlist[self.selected].duration = probe_duration(self.playlist[self.selected].path)
        err = self.engine.play(
            self.playlist[self.selected],
            0 if self.muted else self.volume,
            self.tone,
            self.dsp,
            DSP_MODES[self.dsp_mode_index][0],
            self.bass_boost,
            start_at=start_at,
            paused=paused,
        )
        self.resume_track_path = self.playlist[self.selected].path
        self.resume_position = max(0.0, start_at)
        self.status = err or f"Playing: {self.playlist[self.selected].title}"

    def restore_last_session_playback(self) -> None:
        if not self.resume_autoplay or not self.playlist:
            return
        if self.resume_track_path:
            for index, track in enumerate(self.playlist):
                if track.path == self.resume_track_path:
                    self.selected = index
                    break
        self.selected = min(max(0, self.selected), len(self.playlist) - 1)
        self.play_selected(start_at=self.resume_position, paused=False)

    def remember_resume_state(self) -> None:
        if self.engine.current:
            self.resume_track_path = self.engine.current.path
            self.resume_position = self.engine.elapsed()
            return
        if self.playlist:
            self.selected = min(max(0, self.selected), len(self.playlist) - 1)
            self.resume_track_path = self.playlist[self.selected].path
            self.resume_position = 0.0
            return
        self.resume_track_path = None
        self.resume_position = 0.0

    def toggle_resume_autoplay(self) -> None:
        self.resume_autoplay = not self.resume_autoplay
        self.save_config()
        self.status = f"Resume autoplay: {'on' if self.resume_autoplay else 'off'}"

    def cycle_visual_style(self) -> None:
        self.visual_style_index = (self.visual_style_index + 1) % len(VISUAL_STYLES)
        self.save_config()
        self.status = f"Visual style: {VISUAL_STYLES[self.visual_style_index]}"

    def cycle_repeat_mode(self) -> None:
        modes = ["all", "one", "off"]
        index = (modes.index(self.repeat_mode) + 1) % len(modes)
        self.repeat_mode = modes[index]
        self.status = f"Repeat: {self.repeat_mode}"

    def toggle_shuffle(self) -> None:
        self.shuffle_enabled = not self.shuffle_enabled
        self.status = f"Shuffle: {'on' if self.shuffle_enabled else 'off'}"

    def toggle_mute(self) -> None:
        if self.muted:
            self.muted = False
            if self.volume == 0 and self.pre_mute_volume > 0:
                self.volume = self.pre_mute_volume
            self.status = f"Mute off (volume {self.volume}%)"
        else:
            self.muted = True
            self.pre_mute_volume = max(1, self.volume)
            self.status = "Mute on"
        self.schedule_reconfigure()

    def dsp_mode_label(self) -> str:
        return DSP_MODES[self.dsp_mode_index][1]

    def cycle_dsp_mode(self) -> None:
        self.dsp_mode_index = (self.dsp_mode_index + 1) % len(DSP_MODES)
        self.save_config()
        self.status = f"DSP mode: {self.dsp_mode_label()}"
        self.schedule_reconfigure()

    def toggle_bass_boost(self) -> None:
        if self.bass_boost > 0:
            self.bass_boost = 0
        else:
            self.bass_boost = 6
        self.save_config()
        self.status = f"Bass boost: {'off' if self.bass_boost == 0 else f'+{self.bass_boost} dB'}"
        self.schedule_reconfigure()

    def change_bass_boost(self, delta: int) -> None:
        self.bass_boost = max(0, min(18, self.bass_boost + delta))
        self.save_config()
        self.status = f"Bass boost: {'off' if self.bass_boost == 0 else f'+{self.bass_boost} dB'}"
        self.schedule_reconfigure()

    def reset_dsp_chain(self) -> None:
        self.dsp = 0
        self.dsp_mode_index = 0
        self.bass_boost = 0
        self.eq_preset_index = 0
        self.save_config()
        self.status = "DSP reset: mode stereo, level 0, bass boost off"
        self.schedule_reconfigure()

    def next_track(self) -> None:
        if not self.playlist:
            return
        if self.shuffle_enabled and len(self.playlist) > 1:
            choices = [idx for idx in range(len(self.playlist)) if idx != self.selected]
            self.selected = random.choice(choices)
        else:
            self.selected = (self.selected + 1) % len(self.playlist)
        self.play_selected()

    def prev_track(self) -> None:
        if not self.playlist:
            return
        self.selected = (self.selected - 1) % len(self.playlist)
        self.play_selected()

    def restart_if_active(self) -> None:
        if self.engine.current and self.engine.proc and self.engine.proc.poll() is None:
            elapsed = self.engine.elapsed()
            current_path = self.engine.current.path
            for index, track in enumerate(self.playlist):
                if track.path == current_path:
                    self.selected = index
                    break
            self.play_selected(start_at=elapsed, paused=False)

    def seek_current(self, delta_seconds: float) -> None:
        if not self.engine.current:
            return
        current_path = self.engine.current.path
        for index, track in enumerate(self.playlist):
            if track.path == current_path:
                self.selected = index
                break
        track = self.playlist[self.selected]
        if track.duration is None:
            track.duration = probe_duration(track.path)
        target = max(0.0, self.engine.elapsed() + delta_seconds)
        if track.duration is not None:
            target = min(target, max(0.0, track.duration - 0.2))
        if self.engine.paused_at is not None:
            self.engine.started_at = time.monotonic() - target
            self.engine.paused_total = 0.0
            self.engine.paused_at = time.monotonic()
            self.resume_track_path = current_path
            self.resume_position = target
            self.status = f"Seek: {fmt_time(target)} (paused)"
            return
        self.play_selected(start_at=target, paused=False)
        self.status = f"Seek: {fmt_time(target)}"

    def schedule_reconfigure(self, delay: float = 0.22) -> None:
        if self.engine.current and self.engine.proc and self.engine.proc.poll() is None:
            self.pending_reconfigure_at = time.monotonic() + delay

    def toggle_pause(self) -> None:
        if not self.engine.current:
            self.play_selected()
            return
        if self.engine.paused_at is None:
            elapsed = self.engine.elapsed()
            self.pending_reconfigure_at = None
            self.engine.stop(clear_current=False)
            self.engine.started_at = time.monotonic() - elapsed
            self.engine.paused_total = 0.0
            self.engine.paused_at = time.monotonic()
            self.status = "Paused"
            return
        resume_at = self.engine.elapsed()
        current_path = self.engine.current.path
        for index, track in enumerate(self.playlist):
            if track.path == current_path:
                self.selected = index
                break
        self.play_selected(start_at=resume_at, paused=False)

    def handle_key(self, key: int) -> None:
        key = normalize_hotkey(key)
        if key == -1:
            return
        if self.about_open:
            if key in (ord("q"), 27, ord("i")):
                self.about_open = False
            return
        if self.browser_open:
            self.handle_browser_key(key)
            return
        if key in (ord("q"), 27):
            self.running = False
        elif key in (curses.KEY_UP, ord("k")):
            self.selected = max(0, self.selected - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.selected = min(max(0, len(self.playlist) - 1), self.selected + 1)
        elif key in (curses.KEY_NPAGE,):
            self.selected = min(max(0, len(self.playlist) - 1), self.selected + 8)
        elif key in (curses.KEY_PPAGE,):
            self.selected = max(0, self.selected - 8)
        elif key == curses.KEY_LEFT:
            self.seek_current(-5.0)
        elif key == curses.KEY_RIGHT:
            self.seek_current(+5.0)
        elif key in (10, 13):
            self.play_selected()
        elif key == ord(" "):
            self.toggle_pause()
        elif key == ord("s"):
            self.remember_resume_state()
            self.resume_position = 0.0
            self.engine.stop()
            self.status = "Stopped"
        elif key == ord("n"):
            self.next_track()
        elif key == ord("p"):
            self.prev_track()
        elif key == ord("r"):
            self.cycle_repeat_mode()
        elif key == ord("h"):
            self.toggle_shuffle()
        elif key == ord("m"):
            self.toggle_mute()
        elif key == ord("u"):
            self.toggle_resume_autoplay()
        elif key == ord("v"):
            self.cycle_visual_style()
        elif key == ord("i"):
            self.about_open = True
        elif key == ord("x"):
            self.cycle_dsp_mode()
        elif key == ord("b"):
            self.toggle_bass_boost()
        elif key == ord("B"):
            self.change_bass_boost(+2)
        elif key == ord("o"):
            self.browser_open = True
            self.refresh_browser()
        elif key == ord("a"):
            self.add_path(Path.cwd())
        elif key == ord("d"):
            self.reset_dsp_chain()
        elif key in (ord("D"), curses.KEY_DC) and self.playlist:
            removed = self.playlist.pop(self.selected)
            self.selected = min(self.selected, max(0, len(self.playlist) - 1))
            self.status = f"Removed: {removed.title}"
        elif key == ord("c"):
            self.engine.stop()
            self.playlist.clear()
            self.selected = 0
            self.status = "Playlist cleared"
        elif key in (ord("+"), ord("=")):
            if self.muted:
                self.muted = False
            self.volume = min(150, self.volume + 5)
            self.status = f"Volume {self.volume}%"
            self.schedule_reconfigure()
        elif key in (ord("-"), ord("_")):
            if self.muted:
                self.muted = False
            self.volume = max(0, self.volume - 5)
            self.status = f"Volume {self.volume}%"
            self.schedule_reconfigure()
        elif key == ord(">"):
            self.tone = min(12, self.tone + 1)
            self.eq_preset_index = 0
            self.save_config()
            self.status = f"Tone {self.tone:+d}"
            self.schedule_reconfigure()
        elif key == ord("<"):
            self.tone = max(-12, self.tone - 1)
            self.eq_preset_index = 0
            self.save_config()
            self.status = f"Tone {self.tone:+d}"
            self.schedule_reconfigure()
        elif key == ord("]"):
            self.dsp = min(12, self.dsp + 1)
            self.eq_preset_index = 0
            self.save_config()
            self.status = f"DSP {self.dsp:02d} ({self.dsp_mode_label()})"
            self.schedule_reconfigure()
        elif key == ord("["):
            self.dsp = max(0, self.dsp - 1)
            self.eq_preset_index = 0
            self.save_config()
            self.status = f"DSP {self.dsp:02d} ({self.dsp_mode_label()})"
            self.schedule_reconfigure()
        elif key in (ord("t"), curses.KEY_F8):
            self.switch_theme(1)
        elif key == curses.KEY_F7:
            self.switch_theme(-1)
        elif key == ord("e"):
            self.cycle_eq_preset(1)
        elif key == ord("E"):
            self.cycle_eq_preset(-1)
        elif key == ord("w"):
            self.save_playlist()
        elif key == ord("l"):
            self.load_playlist()
        elif key in (ord("0"), ord("1"), ord("2"), ord("3"), ord("4")):
            self.set_eq_preset(key - ord("0"))

    def handle_browser_key(self, key: int) -> None:
        key = normalize_hotkey(key)
        if key in (ord("q"), 27, ord("o")):
            self.browser_open = False
        elif key in (curses.KEY_UP, ord("k")):
            self.browser_selected = max(0, self.browser_selected - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.browser_selected = min(max(0, len(self.browser_items) - 1), self.browser_selected + 1)
        elif key == curses.KEY_IC:
            self.toggle_browser_mark()
        elif key in (10, 13):
            if not self.browser_items:
                return
            item = self.browser_items[self.browser_selected]
            if self.browser_selected == 0:
                self.add_path(item)
                if self.playlist:
                    self.selected = len(self.playlist) - 1
                self.browser_open = False
            elif item.is_dir():
                self.browser_path = item.resolve()
                self.browser_selected = 0
                self.refresh_browser()
            else:
                self.add_path(item)
                self.browser_open = False
                self.selected = len(self.playlist) - 1
        elif key == ord("a"):
            self.add_browser_selection()
        elif key == ord(" "):
            added = self.add_browser_selection()
            if self.playlist and added:
                self.selected = len(self.playlist) - 1
                self.play_selected()
                self.browser_open = False

    def draw(self) -> None:
        self.screen.erase()
        height, width = self.screen.getmaxyx()
        if height < 24 or width < 72:
            self.screen.addstr(0, 0, "Need at least 72x24 terminal", color(4))
            self.screen.refresh()
            return
        self.vu.step(self.engine.is_playing(), self.volume, self.dsp)
        self.draw_top(width)
        body_top = 9
        controls_h = 7
        self.draw_playlist(body_top, height - controls_h - body_top - 1, width // 2 - 1)
        self.draw_right(body_top, height - controls_h - body_top - 1, width // 2, width - width // 2)
        self.draw_controls(height - controls_h, controls_h, width)
        if self.browser_open:
            self.draw_browser(height, width)
        if self.about_open:
            self.draw_about(height, width)
        self.screen.refresh()

    def draw_top(self, width: int) -> None:
        self.screen.attron(color(2) | curses.A_BOLD)
        for y, line in enumerate(LOGO[: min(len(LOGO), 7)]):
            self.add(1 + y, 2, line[: width - 4])
        self.screen.attroff(color(2) | curses.A_BOLD)
        status = "PLAY" if self.engine.is_playing() else "PAUSE" if self.engine.paused_at else "IDLE"
        self.badge(1, max(2, width - 16), f" {status} ", 3 if status == "PLAY" else 5)
        self.add(8, 2, COPYRIGHT_TEXT[: width - 4], color(7))

    def draw_playlist(self, y: int, h: int, w: int) -> None:
        self.box(y, 0, h, w, " playlist ")
        visible = max(1, h - 2)
        if self.selected < self.scroll:
            self.scroll = self.selected
        if self.selected >= self.scroll + visible:
            self.scroll = self.selected - visible + 1
        if not self.playlist:
            self.add(y + 2, 2, "Open a folder with o, add files with a.", color(7))
            return
        for row, idx in enumerate(range(self.scroll, min(len(self.playlist), self.scroll + visible))):
            track = self.playlist[idx]
            prefix = ">" if self.engine.current and self.engine.current.path == track.path else " "
            dur = fmt_time(track.duration) if track.duration else "--:--"
            text = f"{prefix} {idx + 1:03d} {track.title}"
            max_title = max(8, w - 13)
            text = text[:max_title].ljust(max_title) + dur.rjust(6)
            attr = color(1) | curses.A_BOLD if idx == self.selected else color(3 if prefix == ">" else 0)
            self.add(y + 1 + row, 1, text[: w - 2], attr)

    def draw_right(self, y: int, h: int, x: int, w: int) -> None:
        meter_h = max(8, h - 6)
        self.box(y, x, meter_h, w, " warm cube levels ")
        self.draw_vu(y + 1, x + 2, meter_h - 2, w - 4)
        info_y = y + meter_h
        info_h = h - meter_h
        self.box(info_y, x, info_h, w, " now ")
        title = self.engine.current.title if self.engine.current else "no track loaded"
        self.add(info_y + 1, x + 2, title[: w - 4], color(2) | curses.A_BOLD)
        elapsed = self.engine.elapsed()
        duration = self.engine.current.duration if self.engine.current else None
        self.add(info_y + 2, x + 2, f"{fmt_time(elapsed)} / {fmt_time(duration)}", color(7))
        if duration and info_h > 4:
            bar_w = max(10, w - 6)
            fill = min(bar_w, int(bar_w * min(1.0, elapsed / duration)))
            self.add(info_y + 3, x + 2, "[" + "#" * fill + "-" * (bar_w - fill) + "]", color(3))
        status_y = info_y + 4 if info_h > 5 else info_y + 3
        self.add(status_y, x + 2, self.status[: w - 4], color(6))
        if info_h > 6:
            theme = f"theme {self.theme_index + 1}/{len(COLOR_SCHEMES)} {COLOR_SCHEMES[self.theme_index][0]}"
            self.add(info_y + 5, x + 2, theme[: w - 4], color(7))
        if info_h > 7:
            eq_text = f"eq {self.eq_preset_index}: {EQ_PRESETS[self.eq_preset_index][0]}"
            self.add(info_y + 6, x + 2, eq_text[: w - 4], color(7))
        if info_h > 8:
            mode = (
                f"repeat {self.repeat_mode}  shuffle {'on' if self.shuffle_enabled else 'off'}  "
                f"mute {'on' if self.muted else 'off'}  resume {'on' if self.resume_autoplay else 'off'}"
            )
            self.add(info_y + 7, x + 2, mode[: w - 4], color(7))
        if info_h > 9:
            dsp_text = f"dsp mode: {self.dsp_mode_label()}  level: {self.dsp:02d}"
            self.add(info_y + 8, x + 2, dsp_text[: w - 4], color(7))
        if info_h > 10:
            bass_text = f"bass boost: {'off' if self.bass_boost == 0 else f'+{self.bass_boost} dB'}"
            self.add(info_y + 9, x + 2, bass_text[: w - 4], color(7))
        if info_h > 11:
            self.add(info_y + 10, x + 2, LICENSE_TEXT[: w - 4], color(7))
        if info_h > 12:
            vis = f"visual: {VISUAL_STYLES[self.visual_style_index]}"
            self.add(info_y + 11, x + 2, vis[: w - 4], color(7))

    def draw_vu(self, y: int, x: int, h: int, w: int) -> None:
        if h < 6 or w < 46:
            return

        bands = 40
        bar_x = x + 3
        zero_idx = 24

        left_lvl = sum(self.vu.levels[::2]) / max(1, len(self.vu.levels[::2]))
        right_lvl = sum(self.vu.levels[1::2]) / max(1, len(self.vu.levels[1::2]))

        left_neg_fill = int(min(1.0, left_lvl * 1.05) * zero_idx)
        right_neg_fill = int(min(1.0, right_lvl * 1.05) * zero_idx)
        left_pos_fill = int(max(0.0, left_lvl - 0.35) / 0.65 * (bands - zero_idx))
        right_pos_fill = int(max(0.0, right_lvl - 0.35) / 0.65 * (bands - zero_idx))

        def band_color(idx: int) -> int:
            if idx < 24:
                return 3
            if idx < 32:
                return 2
            return 4

        def draw_full_bar(row_y: int) -> None:
            for i in range(bands):
                self.add(row_y, bar_x + i, "▮", color(band_color(i)) | curses.A_BOLD)

        def draw_lr_bar(row_y: int, neg_fill: int, pos_fill: int) -> None:
            for i in range(bands):
                if i < zero_idx:
                    filled = i < neg_fill
                else:
                    filled = i < zero_idx + pos_fill
                if filled:
                    self.add(row_y, bar_x + i, "▮", color(band_color(i)) | curses.A_BOLD)
                else:
                    self.add(row_y, bar_x + i, "·", color(7))

        row_top = y
        row_l = y + 1
        row_db = y + 2
        row_r = y + 3
        row_bottom = y + 4
        row_t = y + 5

        draw_full_bar(row_top)

        self.add(row_l, x + 1, "L", color(3) | curses.A_BOLD)
        draw_lr_bar(row_l, left_neg_fill, left_pos_fill)

        db_ticks = [
            ("-32", 0), ("-24", 5), ("-16", 10), ("-8", 15), ("-4", 20), ("-2", 24), ("-1", 27),
            ("0", 30), ("+1", 33), ("+2", 35), ("+4", 37), ("+8", 39),
        ]
        self.add(row_db, bar_x, " " * min(bands + 4, max(0, w - 4)), color(7))
        for label, idx in db_ticks:
            ix = min(max(0, idx), bands - 1)
            self.add(row_db, bar_x + ix, label, color(band_color(ix)) | curses.A_BOLD)
        self.add(row_db, bar_x + bands - 1, " dB", color(4) | curses.A_BOLD)

        self.add(row_r, x + 1, "R", color(4) | curses.A_BOLD)
        draw_lr_bar(row_r, right_neg_fill, right_pos_fill)

        draw_full_bar(row_bottom)

        t_palette = [4, 4, 2, 2, 3, 3, 4, 2, 3, 4]
        for i in range(10):
            pos = bar_x + i * 4
            self.add(row_t, pos, f"T{i}", color(t_palette[i]) | curses.A_BOLD)

        extra_top = row_t + 1
        extra_h = y + h - extra_top
        if extra_h >= 5:
            self.draw_extra_visualization(extra_top, bar_x, extra_h, bands, zero_idx)

    def draw_extra_visualization(self, y: int, x: int, h: int, bands: int, zero_idx: int) -> None:
        style = self.visual_style_index % len(VISUAL_STYLES)
        phase = int(time.monotonic() * 10)
        levels_count = max(1, len(self.vu.levels))

        def zone_color(idx: int) -> int:
            if idx < zero_idx:
                return 3
            if idx < int(bands * 0.84):
                return 2
            return 4

        if style == 0:
            for col in range(bands):
                level = self.vu.levels[min(levels_count - 1, int(col * levels_count / bands))]
                col_fill = int(level * h)
                for off in range(h):
                    sy = y + h - 1 - off
                    if off < col_fill:
                        ch = "▮" if off % 2 == 0 else "▯"
                        self.add(sy, x + col, ch, color(zone_color(col)) | curses.A_BOLD)
                    elif off % 3 == 0:
                        self.add(sy, x + col, ".", color(7))
            return

        if style == 1:
            if h < 12 or bands < 36:
                return

            wall_color = color(2) | curses.A_BOLD
            pellet_color = color(7)
            gw = min(42, bands - 2)
            gh = min(15, h - 1)
            gx = x + max(0, (bands - gw) // 2)
            gy = y + max(0, (h - gh) // 2)

            walls: set[tuple[int, int]] = set()

            def draw_h(ry: int, x1: int, x2: int) -> None:
                for cx in range(x1, x2 + 1):
                    self.add(ry, cx, "═", wall_color)
                    walls.add((ry, cx))

            def draw_v(cx: int, y1: int, y2: int) -> None:
                for ry in range(y1, y2 + 1):
                    self.add(ry, cx, "║", wall_color)
                    walls.add((ry, cx))

            # Outer frame
            self.add(gy, gx, "╔", wall_color)
            self.add(gy, gx + gw - 1, "╗", wall_color)
            self.add(gy + gh - 1, gx, "╚", wall_color)
            self.add(gy + gh - 1, gx + gw - 1, "╝", wall_color)
            draw_h(gy, gx + 1, gx + gw - 2)
            draw_h(gy + gh - 1, gx + 1, gx + gw - 2)
            draw_v(gx, gy + 1, gy + gh - 2)
            draw_v(gx + gw - 1, gy + 1, gy + gh - 2)

            # ROM-like inner wall layout
            top = gy + 2
            upper_mid = gy + 4
            center = gy + gh // 2
            lower_mid = gy + gh - 5
            bottom = gy + gh - 3
            left = gx + 3
            right = gx + gw - 4

            draw_h(top, gx + 6, gx + gw - 7)
            draw_h(bottom, gx + 6, gx + gw - 7)
            draw_h(upper_mid, gx + 2, gx + 12)
            draw_h(upper_mid, gx + gw - 13, gx + gw - 3)
            draw_h(lower_mid, gx + 2, gx + 12)
            draw_h(lower_mid, gx + gw - 13, gx + gw - 3)

            draw_v(left, top + 1, bottom - 1)
            draw_v(right, top + 1, bottom - 1)
            draw_v(gx + gw // 2 - 1, top + 1, center - 2)
            draw_v(gx + gw // 2 + 1, center + 2, bottom - 1)

            # Ghost house
            ghx1 = gx + gw // 2 - 6
            ghx2 = gx + gw // 2 + 6
            ghy1 = center - 1
            ghy2 = center + 1
            draw_h(ghy1, ghx1, ghx2)
            draw_h(ghy2, ghx1, ghx2)
            draw_v(ghx1, ghy1, ghy2)
            draw_v(ghx2, ghy1, ghy2)
            door_x1 = gx + gw // 2 - 1
            door_x2 = gx + gw // 2 + 1
            for dx in range(door_x1, door_x2 + 1):
                self.add(ghy1, dx, "─", color(4) | curses.A_BOLD)

            # pellets (skip walls)
            pellet_rows = [gy + 1, gy + 3, gy + 5, center, gy + gh - 6, gy + gh - 4, gy + gh - 2]
            for ry in pellet_rows:
                if gy < ry < gy + gh - 1:
                    for px in range(gx + 2, gx + gw - 2, 2):
                        if (ry, px) not in walls:
                            self.add(ry, px, "•", pellet_color)

            # power pellets + tunnels
            self.add(center, gx + 1, "●", color(7) | curses.A_BOLD)
            self.add(center, gx + gw - 2, "●", color(7) | curses.A_BOLD)
            self.add(gy + 1, gx + 2, "●", color(7) | curses.A_BOLD)
            self.add(gy + 1, gx + gw - 3, "●", color(7) | curses.A_BOLD)

            # Chase route: corridors + side tunnel teleport
            path: list[tuple[int, int]] = []
            waypoints = [
                (gy + 1, gx + 2),
                (gy + 1, gx + gw - 3),
                (gy + 3, gx + gw - 3),
                (center - 1, gx + gw - 3),
                (center - 1, gx + 2),
                (center + 1, gx + 2),
                (center + 1, gx + gw - 3),
                (gy + gh - 4, gx + gw - 3),
                (gy + gh - 4, gx + 2),
                (center, gx + 2),
                (center, gx + 1),
                (center, gx + gw - 2),
                (center, gx + gw - 3),
                (gy + 1, gx + 2),
            ]
            for (y1, x1), (y2, x2) in zip(waypoints, waypoints[1:]):
                cy, cx = y1, x1
                path.append((cy, cx))
                # Always walk orthogonally to avoid diagonal infinite loops.
                while cy != y2:
                    cy += 1 if y2 > cy else -1
                    path.append((cy, cx))
                    if len(path) > 5000:
                        break
                while cx != x2 and len(path) <= 5000:
                    cx += 1 if x2 > cx else -1
                    path.append((cy, cx))
                if len(path) > 5000:
                    break

            if not path:
                return

            lead = phase % len(path)
            pac_idx = lead
            g1_idx = (lead - 7) % len(path)
            g2_idx = (lead - 13) % len(path)

            pac_y, pac_x = path[pac_idx]
            nxt_y, nxt_x = path[(pac_idx + 1) % len(path)]
            if nxt_x > pac_x:
                pac_ch = ">" if (phase // 2) % 2 == 0 else "C"
            elif nxt_x < pac_x:
                pac_ch = "<" if (phase // 2) % 2 == 0 else "C"
            else:
                pac_ch = "C"

            g1_y, g1_x = path[g1_idx]
            g2_y, g2_x = path[g2_idx]
            self.add(g2_y, g2_x, "M", color(6) | curses.A_BOLD)
            self.add(g1_y, g1_x, "M", color(4) | curses.A_BOLD)
            if g2_y - 1 >= y:
                self.add(g2_y - 1, g2_x, "o", color(7) | curses.A_BOLD)
            if g1_y - 1 >= y:
                self.add(g1_y - 1, g1_x, "o", color(7) | curses.A_BOLD)
            self.add(pac_y, pac_x, pac_ch, color(2) | curses.A_BOLD)
            return

        if style == 2:
            for col in range(bands):
                sy = y + ((phase + col * 2) % h)
                self.add(sy, x + col, "|", color(zone_color(col)) | curses.A_BOLD)
                if sy > y:
                    self.add(sy - 1, x + col, ".", color(7))
            return

        if style == 3:
            sx = x + (phase % bands)
            for row in range(h):
                self.add(y + row, sx, "|", color(2) | curses.A_BOLD)
                if sx - 1 >= x:
                    self.add(y + row, sx - 1, ".", color(7))
            return

        if style == 4:
            chars = "01:;"
            for col in range(0, bands, 2):
                sy = y + ((phase + col) % h)
                ch = chars[(phase + col) % len(chars)]
                self.add(sy, x + col, ch, color(3) | curses.A_BOLD)
            return

        if style == 5:
            for col in range(bands):
                wave = math.sin((col / 3.0) + time.monotonic() * 2.2)
                sy = y + int((h - 1) * (0.5 + wave * 0.4))
                self.add(sy, x + col, "~", color(zone_color(col)) | curses.A_BOLD)
            return

        if style == 6:
            for _ in range(max(8, bands // 3)):
                col = (phase * 7 + random.randint(0, bands - 1)) % bands
                sy = y + random.randint(0, h - 1)
                self.add(sy, x + col, "*", color(zone_color(col)) | curses.A_BOLD)
            return

        if style == 7:
            center = bands // 2
            for col in range(center):
                level = self.vu.levels[min(levels_count - 1, int(col * levels_count / center))]
                fill = int(level * h)
                for off in range(fill):
                    sy = y + h - 1 - off
                    left = x + center - 1 - col
                    right = x + center + col
                    self.add(sy, left, "▮", color(zone_color(left - x)) | curses.A_BOLD)
                    if right < x + bands:
                        self.add(sy, right, "▮", color(zone_color(right - x)) | curses.A_BOLD)
            return

        if style == 8:
            for col in range(bands):
                heat = (math.sin(time.monotonic() * 3.0 + col * 0.4) + 1.0) * 0.5
                fill = int((0.2 + heat * 0.8) * h)
                for off in range(fill):
                    sy = y + h - 1 - off
                    clr = 4 if off < fill * 0.35 else 2
                    self.add(sy, x + col, "^", color(clr) | curses.A_BOLD)
            return

        cx = x + (phase % bands)
        cy = y + int((h - 1) * (0.5 + math.sin(time.monotonic() * 1.8) * 0.4))
        self.add(cy, cx, "@", color(2) | curses.A_BOLD)
        for r in range(1, 5):
            px = cx - r
            if x <= px < x + bands:
                self.add(cy, px, ".", color(7))

    def draw_controls(self, y: int, h: int, w: int) -> None:
        self.box(y, 0, h, w, " controls ")
        buttons = [
            "[Space] Play/Pause",
            "[Enter] Play",
            "[s] Stop",
            "[p] Prev",
            "[n] Next",
            "[o] Open",
            "[d] DSP reset",
            "[D] Delete",
            "[r] Repeat",
            "[h] Shuffle",
            "[m] Mute",
            "[u] Resume",
            "[v] Visual",
            "[i] About",
            "[x] DSP mode",
            "[b/B] Bass",
        ]
        button_row = 0
        x = 2
        for label in buttons:
            if x + len(label) >= w - 2:
                button_row += 1
                if button_row > 1:
                    break
                x = 2
            self.badge(y + 1 + button_row, x, label, 5)
            x += len(label) + 2
        if w >= 84:
            slider_positions = [(2, 24), (30, 22), (56, 22)]
        else:
            slider_positions = [(2, 20), (24, 20), (46, 20)]
        self.slider(y + 3, slider_positions[0][0], slider_positions[0][1], "VOL", self.volume, 0, 150)
        self.slider(y + 3, slider_positions[1][0], slider_positions[1][1], "TONE", self.tone, -12, 12)
        self.slider(y + 3, slider_positions[2][0], slider_positions[2][1], "DSP", self.dsp, 0, 12)

        help_text = HELP
        max_w = max(10, w - 4)
        if len(help_text) <= max_w:
            self.add(y + 4, 2, help_text, color(7))
            return
        split_at = help_text.rfind("  ", 0, max_w)
        if split_at == -1:
            split_at = max_w
        line1 = help_text[:split_at].rstrip()
        line2 = help_text[split_at:].strip()
        self.add(y + 4, 2, line1[:max_w], color(7))
        self.add(y + 5, 2, line2[:max_w], color(7))

    def draw_browser(self, height: int, width: int) -> None:
        h = min(height - 4, max(12, height * 3 // 4))
        w = min(width - 6, max(64, width * 3 // 4))
        y = (height - h) // 2
        x = (width - w) // 2
        self.box(y, x, h, w, " file browser: Insert mark, a add marked, Space add+play ")
        header = f"{self.browser_path}  marked:{len(self.browser_marked)}"
        self.add(y + 1, x + 2, header[: w - 4], color(2) | curses.A_BOLD)
        visible = h - 4
        if self.browser_selected < self.browser_scroll:
            self.browser_scroll = self.browser_selected
        if self.browser_selected >= self.browser_scroll + visible:
            self.browser_scroll = self.browser_selected - visible + 1
        for row, idx in enumerate(range(self.browser_scroll, min(len(self.browser_items), self.browser_scroll + visible))):
            item = self.browser_items[idx]
            mark = "*" if safe_resolve(item) in self.browser_marked else " "
            if idx == 0:
                marker = "./  add this folder recursively"
                icon = "ADD "
            elif idx == 1:
                marker = "../"
                icon = "DIR "
            else:
                marker = f"{item.name}/" if item.is_dir() else item.name
                icon = "DIR " if item.is_dir() else "MP3 "
            attr = color(1) | curses.A_BOLD if idx == self.browser_selected else color(7 if item.is_dir() else 3)
            self.add(y + 3 + row, x + 2, f"[{mark}] {icon}{marker}"[: w - 4], attr)

    def draw_about(self, height: int, width: int) -> None:
        h = min(height - 4, 16)
        w = min(width - 6, 90)
        y = (height - h) // 2
        x = (width - w) // 2
        self.box(y, x, h, w, " about ")
        lines = [
            "Borodachamba Music v1.0",
            COPYRIGHT_TEXT,
            LICENSE_TEXT,
            "",
            "Open-source project",
            "Repository: github.com/nickantonov/borodachamba-music-v1-0",
            "Press i or Esc to close",
        ]
        for idx, line in enumerate(lines):
            if y + 1 + idx >= y + h - 1:
                break
            self.add(y + 1 + idx, x + 2, line[: w - 4], color(7 if idx > 0 else 2) | (curses.A_BOLD if idx == 0 else 0))

    def box(self, y: int, x: int, h: int, w: int, title: str) -> None:
        if h <= 1 or w <= 2:
            return
        attr = color(2)
        self.add(y, x, "+" + "-" * (w - 2) + "+", attr)
        for row in range(1, h - 1):
            self.add(y + row, x, "|" + " " * (w - 2) + "|", attr)
        self.add(y + h - 1, x, "+" + "-" * (w - 2) + "+", attr)
        self.add(y, x + 2, title[: max(0, w - 4)], color(5) | curses.A_BOLD)

    def badge(self, y: int, x: int, label: str, pair: int) -> None:
        self.add(y, x, label, color(pair) | curses.A_BOLD)

    def slider(self, y: int, x: int, w: int, label: str, value: int, low: int, high: int) -> None:
        bar_w = max(4, w - len(label) - 8)
        ratio = (value - low) / (high - low)
        fill = int(bar_w * ratio)
        text = f"{label} [" + "#" * fill + "-" * (bar_w - fill) + f"] {value:+d}"
        self.add(y, x, text[:w], color(3 if label == "VOL" else 2))

    def add(self, y: int, x: int, text: str, attr: int = 0) -> None:
        try:
            self.screen.addstr(y, x, text, attr)
        except curses.error:
            pass

    def read_key(self) -> int:
        key = self.screen.getch()
        if key != 27:
            return key

        seq = []
        self.screen.nodelay(True)
        try:
            deadline = time.monotonic() + 0.03
            while time.monotonic() < deadline and len(seq) < 6:
                nxt = self.screen.getch()
                if nxt == -1:
                    time.sleep(0.003)
                    continue
                seq.append(nxt)
                if nxt in (ord("~"), ord("A"), ord("B"), ord("C"), ord("D")):
                    break
        finally:
            self.screen.timeout(50)

        if seq == [ord("["), ord("2"), ord("~")]:
            return curses.KEY_IC
        if seq == [ord("["), ord("A")]:
            return curses.KEY_UP
        if seq == [ord("["), ord("B")]:
            return curses.KEY_DOWN
        if seq == [ord("["), ord("C")]:
            return curses.KEY_RIGHT
        if seq == [ord("["), ord("D")]:
            return curses.KEY_LEFT
        return 27

    def loop(self) -> None:
        install_shutdown_signal_handlers()
        self.setup()
        self.restore_last_session_playback()
        try:
            while self.running:
                if self.engine.finished():
                    self.engine.proc = None
                    if not self.playlist:
                        self.engine.current = None
                    elif self.repeat_mode == "one":
                        self.play_selected()
                    elif self.shuffle_enabled and len(self.playlist) > 1:
                        choices = [idx for idx in range(len(self.playlist)) if idx != self.selected]
                        self.selected = random.choice(choices)
                        self.play_selected()
                    elif self.selected < len(self.playlist) - 1:
                        self.selected += 1
                        self.play_selected()
                    elif self.repeat_mode == "all":
                        self.selected = 0
                        self.play_selected()
                    else:
                        self.engine.current = None
                        self.status = "Playback finished"
                key = self.read_key()
                self.handle_key(key)
                if self.pending_reconfigure_at is not None and time.monotonic() >= self.pending_reconfigure_at:
                    self.pending_reconfigure_at = None
                    self.restart_if_active()
                self.draw()
                time.sleep(1 / 18)
        except KeyboardInterrupt:
            self.running = False
        finally:
            self.pending_reconfigure_at = None
            self.remember_resume_state()
            self.save_config(announce=False)
            self.save_playlist(announce=False)
            self.engine.stop()


def probe_duration(path: Path) -> float | None:
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        str(path),
    ]
    try:
        out = subprocess.check_output(cmd, timeout=3)
        data = json.loads(out.decode("utf-8", "replace"))
        duration = data.get("format", {}).get("duration")
        return float(duration) if duration else None
    except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError):
        return None


def fmt_time(seconds: float | None) -> str:
    if seconds is None:
        return "--:--"
    seconds = max(0, int(seconds))
    mins, sec = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    if hrs:
        return f"{hrs:d}:{mins:02d}:{sec:02d}"
    return f"{mins:02d}:{sec:02d}"


def safe_resolve(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def color(pair: int) -> int:
    if not curses.has_colors() or pair <= 0:
        return 0
    return curses.color_pair(pair)


def normalize_hotkey(key: int) -> int:
    if key < 0 or key > 0x10FFFF:
        return key
    try:
        ch = chr(key)
    except ValueError:
        return key
    lower = ch.lower()
    mapped = LAYOUT_KEY_TO_LATIN.get(lower)
    if mapped:
        return ord(mapped.upper() if ch.isupper() else mapped)
    if lower in {",", "б"}:
        return ord("<")
    if lower in {".", "ю"}:
        return ord(">")
    if lower == "х":
        return ord("[")
    if lower in {"ъ", "ї"}:
        return ord("]")
    return key


def discover_initial(args: Iterable[str], app: App) -> None:
    paths = [Path(arg).expanduser() for arg in args]
    if not paths:
        return
    for path in paths:
        app.add_path(path)


def install_shutdown_signal_handlers() -> None:
    def stop_now(signum: int, frame: object) -> None:
        raise KeyboardInterrupt

    signals = [signal.SIGINT, signal.SIGTERM]
    if hasattr(signal, "SIGHUP"):
        signals.append(signal.SIGHUP)
    for sig in signals:
        try:
            signal.signal(sig, stop_now)
        except (AttributeError, ValueError):
            pass


def main(screen: curses.window) -> None:
    app = App(screen)
    discover_initial(os.sys.argv[1:], app)
    app.loop()


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
