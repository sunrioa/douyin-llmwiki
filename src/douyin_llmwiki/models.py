from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VideoMetadata:
    source_url: str
    video_id: str
    title: str
    webpage_url: str | None = None
    uploader: str | None = None
    duration_seconds: float | None = None
    upload_date: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DownloadResult:
    audio_path: Path
    metadata: VideoMetadata


@dataclass(frozen=True)
class TranscriptSegment:
    text: str
    start_ms: int | None = None
    end_ms: int | None = None
    speaker: str | None = None


@dataclass(frozen=True)
class Transcript:
    text: str
    segments: list[TranscriptSegment] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Summary:
    summary: str
    key_points: list[str]
    concepts: list[str]
    actions: list[str]
    tags: list[str]
    related_topics: list[str]
    knowledge_title: str = ""
    knowledge_definition: str = ""
    use_cases: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    workflow_steps: list[str] = field(default_factory=list)
    decision_rules: list[str] = field(default_factory=list)
    pitfalls: list[str] = field(default_factory=list)
    practice_template: list[str] = field(default_factory=list)
    review_questions: list[str] = field(default_factory=list)
    transferable_methods: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IngestResult:
    note_path: Path
    metadata: VideoMetadata
