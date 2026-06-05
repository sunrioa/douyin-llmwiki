# Local Configuration Reference

This skill has no required `.env` and no remote service configuration. It starts from a local transcript text file and writes a Markdown note into a local Obsidian Vault.

## Inputs

Supported input files are plain text or text-like transcript files:

- `.txt`
- `.md`
- `.srt`
- `.vtt`
- any local text file the agent can read as UTF-8

The speech-to-text step must already be complete before this skill starts.

## Obsidian Vault

Preferred: ask the user for the Vault path, for example:

```powershell
C:\Users\ELAINA\Documents\ObsidianVault
```

The helper script validates that the path exists, is a directory, and contains `.obsidian`.

If the user does not know the Vault path, discover local Vaults:

```powershell
python <skill-dir>\scripts\obsidian_transcript_note.py discover --json
```

Optional scan controls:

```powershell
python <skill-dir>\scripts\obsidian_transcript_note.py discover --root "D:\Notes" --root "$env:USERPROFILE\Documents" --max-depth 6 --json
```

Default scan roots are common user folders such as Documents, Desktop, OneDrive, and the user home directory. The script looks for `.obsidian` directories and returns their parent folders.

If multiple Vaults are found, ask the user which one to use instead of guessing.

## Vault-Relative Directory

Default:

```text
LLMWiki/LocalTranscripts/{year}
```

Supported placeholders:

- `{year}` -> `2026`
- `{date}` -> `2026-06-05`

Examples:

```text
LLMWiki/LocalTranscripts/{year}
LLMWiki/Meetings/{year}
Resources/VideoNotes/{date}
```

The helper creates missing directories inside the Vault.

## Summary JSON

The current Codex/local agent should create the summary. The helper script only renders and writes it.

Minimum useful JSON:

```json
{
  "knowledge_title": "主题",
  "knowledge_definition": "定义",
  "summary": "摘要",
  "key_points": ["观点"],
  "actions": [],
  "tags": ["知识库"],
  "related_topics": []
}
```

Recommended fields are listed in `SKILL.md`.

## No Remote Services

Do not configure or call:

- DashScope / Bailian
- OSS
- yt-dlp
- douyin_crawl
- `douyin-llmwiki` CLI
- any ASR, downloader, or remote LLM API from this skill

The only network-like dependency may be the Codex/local agent runtime itself. The skill files and helper script do not invoke external services.
