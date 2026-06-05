---
name: douyin-llmwiki
description: Use this skill whenever the user wants to summarize a local speech-to-text transcript file such as 111.txt, .md, .srt, or .vtt into an Obsidian LLMWiki note; asks to turn local ASR text into a knowledge note; wants Codex or another local agent to do the summary directly; or needs to find/create an Obsidian Vault directory without using DashScope, Bailian, OSS, yt-dlp, Douyin downloaders, or any remote workflow service.
---

# Douyin LLMWiki

## Purpose

Use this skill for a fully local transcript-to-Obsidian workflow. The input is already-transcribed text, for example `111.txt`; the current agent reads and summarizes that text directly, then writes a structured Markdown note into an Obsidian Vault.

This skill does not download videos, extract audio, run ASR, upload files, or call remote API services. It intentionally starts after speech-to-text is complete.

## Workflow

1. Identify the transcript file.
   - Accept local `.txt`, `.md`, `.srt`, `.vtt`, or similar plain-text transcript files.
   - If the user gives only a filename, resolve it from the current workspace first, then ask for a path only if it cannot be found.
   - Do not send transcript contents to external services from this skill. Summarize using the current Codex/local agent context.

2. Read the transcript and summarize it.
   - For short files, read the full file and produce one structured summary.
   - For long files, summarize in chunks, then merge into a final summary.
   - Prefer reusable knowledge over ordinary recap: extract what the user can apply later.
   - Use this JSON shape internally when calling the helper script:

```json
{
  "knowledge_title": "短而具体的知识主题",
  "knowledge_definition": "1-2 句话说明这条知识解决什么问题",
  "summary": "聚焦可复用知识的中文摘要",
  "key_points": ["核心观点"],
  "concepts": ["关键概念：解释"],
  "use_cases": ["适用场景"],
  "workflow_steps": ["可执行步骤"],
  "decision_rules": ["判断准则"],
  "pitfalls": ["常见误区"],
  "practice_template": ["可复制的模板或清单"],
  "actions": ["后续行动"],
  "review_questions": ["复习问题"],
  "transferable_methods": ["可迁移方法"],
  "tags": ["Obsidian 标签，不含 #"],
  "related_topics": ["相关主题"]
}
```

3. Resolve the Obsidian target.
   - If the user provides a Vault path, use it directly.
   - If the user provides a Vault-relative directory such as `LLMWiki/Meetings/{year}`, use that structure and create missing folders.
   - If the Vault is not provided, run the helper script to discover local Vaults:

```powershell
python <skill-dir>\scripts\obsidian_transcript_note.py discover --json
```

   - If exactly one Vault is found, use it.
   - If multiple Vaults are found, ask the user which one to use.
   - If no Vault is found, ask the user for the Vault path.

4. Write the note.
   - Prefer the helper script for path sanitizing, date folders, frontmatter, and duplicate filename handling.
   - Create a temporary summary JSON locally, then run:

```powershell
python <skill-dir>\scripts\obsidian_transcript_note.py write "C:\path\to\111.txt" --vault "C:\path\to\Vault" --directory "LLMWiki/LocalTranscripts/{year}" --title "笔记标题" --summary-json "C:\path\to\summary.json"
```

   - The helper prints the created Markdown path.
   - Confirm that the note was written under the Vault and that no audio/media/cache files were created.

## Obsidian Output

Use a knowledge-note structure, not a Codex Skill card:

- Frontmatter with `note_type: local-transcript-summary`
- 知识沉淀
- 摘要
- 核心观点
- 关键概念
- 适用场景
- 操作流程
- 判断准则
- 常见误区
- 实践模板
- 可执行事项
- 复习问题
- 可迁移方法
- 相关主题
- 完整转写

Read `references/output.md` when the user wants to customize the note structure.

## Local Helper

The bundled script only touches local files:

```powershell
python <skill-dir>\scripts\obsidian_transcript_note.py discover --json
python <skill-dir>\scripts\obsidian_transcript_note.py write "C:\path\to\111.txt" --vault "C:\path\to\Vault" --directory "LLMWiki/LocalTranscripts/{year}" --summary-json "C:\path\to\summary.json"
```

Read `references/config.md` when choosing Vault paths, scan roots, directory templates, or troubleshooting path errors.

## Safety Boundaries

- Do not call DashScope, Bailian, OSS, yt-dlp, douyin_crawl, or the old `douyin-llmwiki` CLI from this skill.
- Do not upload transcript contents or generated notes to external services as part of this skill.
- Do not read or expose unrelated Vault files. Only create the requested note.
- Do not commit transcript files, generated notes, `.env`, cookies, or user Vault content to GitHub.
