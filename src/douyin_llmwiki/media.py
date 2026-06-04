from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .errors import DownloadError


def probe_audio(path: Path) -> dict[str, Any]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise DownloadError(f"ffprobe failed for {path}: {message}")
    try:
        return json.loads(completed.stdout or "")
    except json.JSONDecodeError as exc:
        raise DownloadError(f"ffprobe returned invalid JSON for {path}") from exc


def has_audio_stream(probe: dict[str, Any]) -> bool:
    return any(stream.get("codec_type") == "audio" for stream in probe.get("streams", []))


def duration_seconds(probe: dict[str, Any]) -> float | None:
    value = probe.get("format", {}).get("duration")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_audio_to_mp3(source_path: Path, target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "128k",
        str(target_path),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise DownloadError(f"ffmpeg failed to extract audio from {source_path}: {message}")
    return target_path


def split_audio_to_mp3_chunks(source_path: Path, chunk_dir: Path, segment_seconds: int = 240) -> list[Path]:
    chunk_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = chunk_dir / "chunk_%03d.mp3"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-reset_timestamps",
        "1",
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "96k",
        str(output_pattern),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise DownloadError(f"ffmpeg failed to split audio {source_path}: {message}")
    chunks = sorted(chunk_dir.glob("chunk_*.mp3"))
    if not chunks:
        raise DownloadError(f"ffmpeg did not produce audio chunks for {source_path}")
    return chunks
