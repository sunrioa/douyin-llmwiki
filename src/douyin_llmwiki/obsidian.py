from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .errors import ObsidianError
from .models import Summary, Transcript, VideoMetadata
from .timeutil import now_shanghai
from .transcript import format_transcript
from .utils import ensure_unique_path, sanitize_filename


def write_obsidian_note(
    vault_path: Path,
    llmwiki_dir: str,
    metadata: VideoMetadata,
    transcript: Transcript,
    summary: Summary,
    asr_model: str,
    summary_model: str,
    now: datetime | None = None,
) -> Path:
    now = now or now_shanghai()
    output_dir = vault_path / llmwiki_dir / f"{now:%Y}"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ObsidianError(f"Could not create Obsidian output directory: {output_dir}") from exc

    filename_title = sanitize_filename(metadata.title, metadata.video_id)
    note_path = ensure_unique_path(output_dir / f"{now:%Y-%m-%d}_{filename_title}.md")
    content = render_note(metadata, transcript, summary, asr_model, summary_model, now)
    try:
        note_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ObsidianError(f"Could not write Obsidian note: {note_path}") from exc
    return note_path


def render_note(
    metadata: VideoMetadata,
    transcript: Transcript,
    summary: Summary,
    asr_model: str,
    summary_model: str,
    created_at: datetime,
) -> str:
    tags = unique_tags(["llmwiki", "douyin", *summary.tags])
    frontmatter = [
        "---",
        f"title: {_yaml_quote(metadata.title)}",
        "note_type: llmwiki-video-summary",
        "source: douyin",
        f"source_url: {_yaml_quote(metadata.webpage_url or metadata.source_url)}",
        f"video_id: {_yaml_quote(metadata.video_id)}",
        f"uploader: {_yaml_quote(metadata.uploader or '')}",
        f"duration_seconds: {metadata.duration_seconds or 0}",
        f"created: {_yaml_quote(created_at.isoformat())}",
        f"asr_model: {_yaml_quote(asr_model)}",
        f"summary_model: {_yaml_quote(summary_model)}",
        "tags:",
        *[f"  - {_yaml_quote(tag)}" for tag in tags],
        "---",
        "",
    ]

    lines = [
        *frontmatter,
        f"# {metadata.title}",
        "",
        f"- 来源：[{metadata.webpage_url or metadata.source_url}]({metadata.webpage_url or metadata.source_url})",
        f"- 发布者：{metadata.uploader or '未知'}",
        f"- 视频 ID：`{metadata.video_id}`",
        "",
        "## 知识沉淀",
        "",
        f"**主题**：{summary.knowledge_title or metadata.title}",
        "",
        f"**定义**：{summary.knowledge_definition or summary.summary}",
        "",
        "## 摘要",
        "",
        summary.summary,
        "",
        "## 核心观点",
        "",
        *_bullet_lines(summary.key_points),
        "",
        "## 关键概念",
        "",
        *_bullet_lines(summary.concepts),
        "",
        "## 适用场景",
        "",
        *_bullet_lines(summary.use_cases),
        "",
        "## 前置条件",
        "",
        *_bullet_lines(summary.prerequisites, empty="暂无明确前置条件。"),
        "",
        "## 操作流程",
        "",
        *_ordered_lines(summary.workflow_steps),
        "",
        "## 判断准则",
        "",
        *_bullet_lines(summary.decision_rules),
        "",
        "## 常见误区",
        "",
        *_bullet_lines(summary.pitfalls),
        "",
        "## 实践模板",
        "",
        *_bullet_lines(summary.practice_template),
        "",
        "## 可执行事项",
        "",
        *_bullet_lines(summary.actions, empty="暂无明确行动项。"),
        "",
        "## 复习问题",
        "",
        *_bullet_lines(summary.review_questions),
        "",
        "## 可迁移方法",
        "",
        *_bullet_lines(summary.transferable_methods),
        "",
        "## 相关主题",
        "",
        *_bullet_lines(summary.related_topics),
        "",
        "## 完整转写",
        "",
        format_transcript(transcript),
        "",
    ]
    return "\n".join(lines)


def unique_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        cleaned = sanitize_tag(tag)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def sanitize_tag(tag: str) -> str:
    return str(tag).strip().replace("#", "").replace(" ", "-").strip("-")


def _bullet_lines(items: list[str], empty: str = "暂无。") -> list[str]:
    if not items:
        return [empty]
    return [f"- {item}" for item in items]


def _ordered_lines(items: list[str], empty: str = "暂无明确流程。") -> list[str]:
    if not items:
        return [empty]
    return [f"{index}. {item}" for index, item in enumerate(items, start=1)]


def _yaml_quote(value: str) -> str:
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
