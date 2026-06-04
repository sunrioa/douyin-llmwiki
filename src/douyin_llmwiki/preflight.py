from __future__ import annotations

import importlib.util
import shutil

from .errors import PreflightError


def check_preflight() -> None:
    missing: list[str] = []
    for binary in ("ffmpeg", "ffprobe"):
        if shutil.which(binary) is None:
            missing.append(binary)
    if importlib.util.find_spec("yt_dlp") is None and shutil.which("yt-dlp") is None:
        missing.append("yt-dlp Python package or yt-dlp executable")

    if missing:
        raise PreflightError(
            "Missing required local dependencies: "
            + ", ".join(missing)
            + ". Install project dependencies with `pip install -e .` and install FFmpeg."
        )


def doctor_lines() -> list[str]:
    lines = []
    for binary in ("ffmpeg", "ffprobe", "yt-dlp"):
        path = shutil.which(binary)
        lines.append(f"{binary}: {path or 'NOT FOUND'}")
    lines.append(
        "yt_dlp Python package: "
        + ("OK" if importlib.util.find_spec("yt_dlp") is not None else "NOT FOUND")
    )
    return lines
