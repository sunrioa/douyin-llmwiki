from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse


URL_RE = re.compile(r"https?://[^\s，。；、）)\]}\"'<>]+", re.IGNORECASE)
WINDOWS_ILLEGAL_RE = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
WHITESPACE_RE = re.compile(r"\s+")


def extract_first_url(text: str) -> str:
    match = URL_RE.search(text)
    if not match:
        raise ValueError("No http(s) URL found in input text.")
    return match.group(0).rstrip(".,;:!?，。；：！？")


def is_probable_url(text: str) -> bool:
    try:
        parsed = urlparse(text)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def sanitize_filename(name: str | None, fallback: str = "douyin-video", max_chars: int = 80) -> str:
    value = name or fallback
    value = WINDOWS_ILLEGAL_RE.sub(" ", value)
    value = WHITESPACE_RE.sub(" ", value).strip(" .")
    if not value:
        value = fallback
    if len(value) > max_chars:
        value = value[:max_chars].rstrip(" .")
    return value or fallback


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def format_ms(milliseconds: int | float | None) -> str:
    if milliseconds is None:
        return "00:00:00.000"
    total_ms = max(int(milliseconds), 0)
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"


def split_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in text.splitlines():
        part = paragraph.strip()
        if not part:
            continue
        if current and current_len + len(part) + 1 > max_chars:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        if len(part) > max_chars:
            for start in range(0, len(part), max_chars):
                chunks.append(part[start : start + max_chars])
            continue
        current.append(part)
        current_len += len(part) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks or [text[:max_chars]]
