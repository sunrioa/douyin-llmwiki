---
name: douyin-llmwiki
description: Use this skill whenever the user wants to turn a Douyin share link, saved Douyin MP4/audio file, or ASR transcript into a richer Obsidian LLMWiki note; configure or run the douyin-llmwiki CLI; troubleshoot DashScope/Bailian ASR, yt-dlp, douyin_crawl cookies, ffmpeg, or Obsidian Vault output; or asks in Chinese to 把抖音视频/音频/转写沉淀到 Obsidian、本地知识库、LLMWiki.
---

# Douyin LLMWiki

## Purpose

Use this skill to run the local `douyin-llmwiki` workflow end to end: input a Douyin URL or local media file, extract/transcribe audio, summarize it into a rich knowledge note, and write the Markdown note into an Obsidian Vault.

Keep two concepts separate:

- Obsidian output is a knowledge note, not a Codex Skill card.
- This directory is the Codex Skill that tells the agent how to configure, run, and troubleshoot the workflow.

## Workflow

1. Identify the input mode.
   - Use `--source url` for a public Douyin share URL or copied share text.
   - Use `--source file` for a local `.mp4`, `.mp3`, `.m4a`, `.wav`, or similar media file.
   - Use `--source auto` only when the input may be either a real local path or a URL.

2. Check configuration before ingesting.
   - Read `references/config.md` when setup, `.env`, cookie, ASR, storage, or Vault configuration is relevant.
   - Do not ask the user to paste API keys or cookies into chat. Tell them to put secrets in their local `.env` or cookie file.
   - Run `douyin-llmwiki doctor` when the CLI is installed and the user wants environment validation.

3. Run the workflow.
   - Prefer the bundled wrapper script when using this skill from Codex:

```powershell
python <skill-dir>\scripts\run_douyin_llmwiki.py --project "C:\path\to\douyin-llmwiki" --source url "https://v.douyin.com/xxx/"
```

   - If the package is already installed globally or in the active venv, `--project` can be omitted:

```powershell
python <skill-dir>\scripts\run_douyin_llmwiki.py --source url "https://v.douyin.com/xxx/"
```

   - For a local video or audio file:

```powershell
python <skill-dir>\scripts\run_douyin_llmwiki.py --project "C:\path\to\douyin-llmwiki" --source file "C:\path\to\video.mp4" --source-url "https://v.douyin.com/xxx/" --title "视频标题"
```

4. Confirm the result.
   - The CLI prints the generated Markdown path.
   - Verify the note is under `<OBSIDIAN_VAULT_PATH>/<LLMWIKI_DIR>/YYYY/`.
   - Verify the Vault contains the Markdown note only; downloaded/extracted audio should remain in cache and be deleted after processing.
   - Read `references/output.md` if the user asks what the note should contain or wants to adjust summary richness.

## Common Decisions

- If URL download fails with fresh-cookie or signature errors, switch to a local saved file first. For URL automation, configure `DOUYIN_DOWNLOADER=douyin_crawl` only if the user already has the external downloader installed and a valid cookie file.
- If `OBSIDIAN_VAULT_PATH does not exist`, fix the `.env` path to the actual Vault directory before retrying.
- If `ffmpeg` or `ffprobe` is missing, install FFmpeg and open a new terminal before retrying.
- If DashScope or Bailian authentication fails, check `DASHSCOPE_API_KEY`; do not expose the key in chat.
- If the summary JSON is invalid, rerun once. If it repeats, reduce `MAX_SUMMARY_CHUNK_CHARS` or inspect the transcript for malformed content.

## Commands

Use these commands from the project checkout when not using the wrapper script:

```powershell
douyin-llmwiki doctor
douyin-llmwiki ingest --source url "https://v.douyin.com/xxx/"
douyin-llmwiki ingest --source file "C:\path\to\video.mp4" --source-url "https://v.douyin.com/xxx/" --title "视频标题"
```

Use `--dry-run` on the wrapper script to show the command it will execute:

```powershell
python <skill-dir>\scripts\run_douyin_llmwiki.py --project "C:\path\to\douyin-llmwiki" --source url "https://v.douyin.com/xxx/" --dry-run
```

## Safety Boundaries

- Only process content the user has access to and is allowed to save into their local knowledge base.
- Do not try to bypass login, paywalls, privacy settings, rate limits, or platform restrictions.
- Do not copy `.env`, cookie files, media cache, ASR outputs with secrets, or Obsidian Vault contents into GitHub.
- Keep `douyin_crawl` as an optional external dependency; do not vendor its source into this project.
