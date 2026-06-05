# Douyin LLMWiki Codex Skill

这个文件夹是一个完全本地化的 Codex Skill 分发包。它不再依赖抖音下载、音频提取、百炼 ASR、OSS、DashScope 或 `douyin-llmwiki` CLI。

它的输入是已经由本地语音识别工具转换好的文字文件，例如：

```text
111.txt
meeting-transcript.md
video.srt
```

总结工作由当前 Codex 或其他本地 agent 直接完成，然后写入用户指定或自动发现的 Obsidian Vault。

## 目录结构

```text
douyin-llmwiki-skill/
├── README.md
└── douyin-llmwiki/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── references/
    └── scripts/
```

真正需要安装到 Codex 的目录是内层 `douyin-llmwiki/`。外层 README 只作为安装和使用说明，不属于 Skill 本体。

## 安装到 Codex

在仓库根目录运行：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\douyin-llmwiki-skill\douyin-llmwiki" "$env:USERPROFILE\.codex\skills\"
```

安装后，重启 Codex 或开启新会话，让 Skill 列表重新加载。

## 前置条件

只需要：

- 一个本地转写文本文件
- 一个可写的 Obsidian Vault
- Codex 或其他能读取本地文件并生成总结的本地 agent

不需要：

- `.env`
- 阿里云百炼 / DashScope
- OSS
- ffmpeg / ffprobe
- yt-dlp
- douyin_crawl
- `douyin-llmwiki` CLI

## 在 Codex 中使用

可以直接对 Codex 说：

```text
把 C:\Users\ELAINA\Downloads\111.txt 总结成 Obsidian 知识笔记，放到我的 LLMWiki/LocalTranscripts 目录。
```

如果不知道 Vault 路径，也可以说：

```text
扫描我的电脑找到 Obsidian Vault，然后把 111.txt 总结进去。
```

如果发现多个 Vault，Skill 会要求选择一个，而不是自动猜。

## 直接运行本地辅助脚本

扫描 Vault：

```powershell
python ".\douyin-llmwiki-skill\douyin-llmwiki\scripts\obsidian_transcript_note.py" discover --json
```

写入笔记时，先由 Codex 或本地 agent 生成一个 summary JSON，然后运行：

```powershell
python ".\douyin-llmwiki-skill\douyin-llmwiki\scripts\obsidian_transcript_note.py" write "C:\path\to\111.txt" --vault "C:\path\to\ObsidianVault" --directory "LLMWiki/LocalTranscripts/{year}" --title "笔记标题" --summary-json "C:\path\to\summary.json"
```

## 输出

默认输出位置：

```text
<Vault>/LLMWiki/LocalTranscripts/YYYY/YYYY-MM-DD_<标题>.md
```

Obsidian 笔记是“知识沉淀”结构，不是 Codex Skill 卡片。
