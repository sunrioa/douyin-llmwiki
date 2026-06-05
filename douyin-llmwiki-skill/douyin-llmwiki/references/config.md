# Configuration Reference

## Required `.env`

Create `.env` in the `douyin-llmwiki` project or pass `--env-file` to the CLI.

```env
DASHSCOPE_API_KEY=
SUMMARY_MODEL=qwen-plus
ASR_MODEL=qwen3-asr-flash-filetrans
LOCAL_ASR_MODEL=qwen3-asr-flash
STORAGE_BACKEND=bailian
OBSIDIAN_VAULT_PATH=C:\Users\ELAINA\Documents\ObsidianVault
LLMWIKI_DIR=LLMWiki/Douyin
```

`OBSIDIAN_VAULT_PATH` must be an existing Obsidian Vault directory. `LLMWIKI_DIR` is created inside that Vault.

## Storage Backend

Default:

```env
STORAGE_BACKEND=bailian
```

This stores audio in the local cache, uploads it to Bailian temporary file storage to obtain a temporary URL for ASR, then deletes the local cache after the workflow finishes.

Optional OSS mode:

```env
STORAGE_BACKEND=oss
ALIYUN_ACCESS_KEY_ID=
ALIYUN_ACCESS_KEY_SECRET=
ALIYUN_OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET=
```

OSS mode uploads the audio to private OSS, signs a short-lived URL, and deletes the temporary OSS object after ASR completes.

## Douyin Download Backend

Default:

```env
DOUYIN_DOWNLOADER=yt-dlp
YT_DLP_COOKIES_FROM_BROWSER=edge
YT_DLP_COOKIE_FILE=
```

Prefer `YT_DLP_COOKIE_FILE` when browser cookie databases are locked. The file should be Netscape cookie format.

External downloader fallback:

```env
DOUYIN_DOWNLOADER=douyin_crawl
DOUYIN_CRAWL_PATH=C:\tools\douyin_crawl
DOUYIN_COOKIE_FILE=C:\path\to\cookies.txt
DOUYIN_DOWNLOAD_DIR=C:\path\to\.cache\douyin-downloads
```

Use this only when the user has installed `douyin_crawl` separately. Do not copy its source into this project.

## Local Tools

The local machine needs:

- Python 3.11+
- `ffmpeg`
- `ffprobe`
- `yt-dlp` unless URL mode uses only `douyin_crawl`

Run:

```powershell
douyin-llmwiki doctor
```

Common failures:

- Missing Vault path: fix `OBSIDIAN_VAULT_PATH`.
- Missing FFmpeg: install FFmpeg and reopen the terminal.
- Fresh cookies required: export cookies to a file or use local file mode.
- ASR auth failure: verify `DASHSCOPE_API_KEY` locally without pasting it into chat.
