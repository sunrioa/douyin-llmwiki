# Douyin LLMWiki Codex Skill

这个文件夹是 `douyin-llmwiki` 的独立 Codex Skill 分发包。

目录结构：

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

这个 Skill 是工作流包装层，不内置业务代码和密钥。运行前需要本机已经有：

- `douyin-llmwiki` CLI，或本仓库源码 checkout
- 已配置的 `.env`
- 可写的 Obsidian Vault
- `ffmpeg` / `ffprobe`
- 阿里云百炼 `DASHSCOPE_API_KEY`
- 可选：`yt-dlp` cookie 文件或外部 `douyin_crawl`

敏感信息只放在本机 `.env` 或 cookie 文件中，不要写入 Skill 文件，也不要提交到 GitHub。

## 在 Codex 中使用

安装后，可以直接对 Codex 说：

```text
把这个抖音链接沉淀到 Obsidian：https://v.douyin.com/xxx/
```

或者：

```text
把这个本地视频转成 Obsidian 知识笔记：C:\path\to\video.mp4，来源链接是 https://v.douyin.com/xxx/
```

Skill 会指导 Codex 选择 URL 模式或本地文件模式，并运行底层 CLI。

## 直接运行包装脚本

如果 CLI 是从当前源码项目运行：

```powershell
python ".\douyin-llmwiki-skill\douyin-llmwiki\scripts\run_douyin_llmwiki.py" --project (Get-Location).Path --source url "https://v.douyin.com/xxx/"
```

本地文件模式：

```powershell
python ".\douyin-llmwiki-skill\douyin-llmwiki\scripts\run_douyin_llmwiki.py" --project (Get-Location).Path --source file "C:\path\to\video.mp4" --source-url "https://v.douyin.com/xxx/" --title "视频标题"
```

如果 `douyin-llmwiki` 已经安装到当前环境，可以省略 `--project`：

```powershell
python ".\douyin-llmwiki-skill\douyin-llmwiki\scripts\run_douyin_llmwiki.py" --source url "https://v.douyin.com/xxx/"
```

## 输出

成功后，CLI 会打印生成的 Obsidian Markdown 路径。默认位置：

```text
<OBSIDIAN_VAULT_PATH>/<LLMWIKI_DIR>/YYYY/YYYY-MM-DD_<标题或视频ID>.md
```

Obsidian 笔记是“知识沉淀”结构，不是 Codex Skill 卡片。
