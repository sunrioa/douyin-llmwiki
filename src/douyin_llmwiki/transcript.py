from __future__ import annotations

from typing import Any

from .models import Transcript, TranscriptSegment
from .utils import format_ms


def parse_asr_result(data: dict[str, Any]) -> Transcript:
    segments = extract_segments(data)
    text = "\n".join(segment.text for segment in segments if segment.text).strip()
    if not text:
        text = extract_text_fallback(data).strip()
    return Transcript(text=text, segments=segments, raw=data)


def extract_segments(data: Any) -> list[TranscriptSegment]:
    segments: list[TranscriptSegment] = []
    for sentence in _walk_sentences(data):
        text = sentence.get("text") or sentence.get("sentence") or sentence.get("content")
        if not text:
            continue
        segments.append(
            TranscriptSegment(
                text=str(text).strip(),
                start_ms=_first_int(sentence, "begin_time", "start_time", "start", "begin"),
                end_ms=_first_int(sentence, "end_time", "end", "stop_time", "stop"),
                speaker=_first_str(sentence, "speaker_id", "speaker"),
            )
        )
    return segments


def format_transcript(transcript: Transcript) -> str:
    if transcript.segments:
        lines = []
        for segment in transcript.segments:
            prefix = f"[{format_ms(segment.start_ms)} - {format_ms(segment.end_ms)}]"
            if segment.speaker:
                prefix += f" {segment.speaker}"
            lines.append(f"- {prefix} {segment.text}")
        return "\n".join(lines)
    return transcript.text


def extract_text_fallback(data: Any) -> str:
    texts: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"text", "sentence", "content"} and isinstance(child, str):
                    texts.append(child)
                else:
                    walk(child)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(data)
    return "\n".join(dict.fromkeys(texts))


def _walk_sentences(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        sentences = value.get("sentences")
        if isinstance(sentences, list):
            found.extend(item for item in sentences if isinstance(item, dict))
        for child in value.values():
            found.extend(_walk_sentences(child))
    elif isinstance(value, list):
        for item in value:
            found.extend(_walk_sentences(item))
    return found


def _first_int(mapping: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = mapping.get(key)
        if value is None:
            continue
        try:
            return int(float(value))
        except (TypeError, ValueError):
            continue
    return None


def _first_str(mapping: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return str(value)
    return None
