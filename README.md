# douyin-llmwiki

本地 CLI 工作流：输入单个公开视频的抖音分享链接，提取音频，调用阿里云百炼 ASR 转写，再用通义千问总结，最后写入 Obsidian Vault 的 LLMWiki Markdown 笔记。

> 注意：不要把 `.env`、`cookies.txt`、下载的视频/音频、Obsidian Vault 内容提交到 GitHub。本项目只保存代码、测试、示例配置和文档。

生成的 Obsidian 笔记会按更丰富的知识沉淀结构输出，不只是普通摘要。默认包含：

- 知识主题和定义
- 摘要、核心观点、关键概念
- 适用场景、前置条件、操作流程
- 判断准则、常见误区、实践模板
- 可执行事项、复习问题、可迁移方法
- 相关主题和完整转写

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

还需要系统里能找到 `ffmpeg` 和 `ffprobe`。Windows 上可用 `winget install Gyan.FFmpeg`，安装后重新打开终端。

## 配置

复制 `.env.example` 为 `.env`，填写：

- `DASHSCOPE_API_KEY`
- `ALIYUN_ACCESS_KEY_ID`
- `ALIYUN_ACCESS_KEY_SECRET`
- `ALIYUN_OSS_ENDPOINT`
- `ALIYUN_OSS_BUCKET`
- `OBSIDIAN_VAULT_PATH`

默认 `STORAGE_BACKEND=bailian`，音频会先存在本地缓存，再上传到百炼临时文件空间获取临时 URL，ASR 完成后删除本地缓存。百炼临时文件由平台按有效期自动清理。音频不会写入 Obsidian。

如果以后要改回自有 OSS，设置 `STORAGE_BACKEND=oss`，并填写 `ALIYUN_ACCESS_KEY_ID`、`ALIYUN_ACCESS_KEY_SECRET`、`ALIYUN_OSS_ENDPOINT`、`ALIYUN_OSS_BUCKET`。OSS 后端会在 ASR 完成后删除临时对象。

抖音公开视频有时要求浏览器 cookie。默认可设置 `YT_DLP_COOKIES_FROM_BROWSER=edge`，也可以改成 `chrome` 或 `chrome:Default`。
如果浏览器 cookie 数据库被锁，建议手动导出 Netscape 格式的 cookie 文件，然后设置：

```env
YT_DLP_COOKIE_FILE=C:\Users\ELAINA\Documents\New project 3\cookies.txt
```

`YT_DLP_COOKIE_FILE` 优先级高于 `YT_DLP_COOKIES_FROM_BROWSER`。

如果 `yt-dlp` 仍然卡在抖音签名，可以接入外部 `douyin_crawl` 后端。先把项目 clone 或下载到本地，然后安装它的依赖到当前 venv：

```powershell
git clone https://github.com/zouzanyan/douyin_crawl C:\tools\douyin_crawl
.\.venv\Scripts\python.exe -m pip install -r C:\tools\douyin_crawl\requirements.txt
```

配置：

```env
DOUYIN_DOWNLOADER=douyin_crawl
DOUYIN_CRAWL_PATH=C:\tools\douyin_crawl
DOUYIN_COOKIE_FILE=C:\Users\ELAINA\Documents\New project 3\cookies.txt
DOUYIN_DOWNLOAD_DIR=C:\Users\ELAINA\Documents\New project 3\.cache\douyin-downloads
```

然后仍然使用统一入口：

```powershell
douyin-llmwiki ingest --source url "https://v.douyin.com/xxx/"
```

当前项目不会复制 `douyin_crawl` 源码，只作为外部命令调用；下载成功后会复用本地文件切片 ASR 流程。

## GitHub 发布前检查

确认只提交这些内容：

```text
README.md
LICENSE
pyproject.toml
.env.example
.gitignore
src/
tests/
douyin-llmwiki-skill/
```

确认不要提交：

```text
.env
cookies.txt
.cache/
.venv/
_pdf_replace_preview/
*.mp4 / *.mp3 / *.m4a / *.wav
Obsidian Vault 内容
```

`douyin_crawl` 是可选外部下载器，不包含在本仓库内；如果使用它，请用户自行 clone 并按 README 配置 `DOUYIN_CRAWL_PATH`。

## License

MIT. Optional external tools such as `douyin_crawl` are not bundled with this repository and keep their own licenses.

## 使用

```powershell
douyin-llmwiki doctor
douyin-llmwiki ingest "复制来的抖音分享文本或 https://v.douyin.com/xxx/"
```

如果抖音链接下载被风控拦截，可以先手动保存视频或音频，再走本地文件入口：

```powershell
douyin-llmwiki ingest-file "C:\path\to\video.mp4" --source-url "https://v.douyin.com/xxx/" --title "视频标题"
```

`ingest-file` 会把本地文件抽取/复制成缓存 mp3，处理结束后删除缓存，不会删除原始文件。
本地文件入口默认使用 `LOCAL_ASR_MODEL=qwen3-asr-flash`，会把长音频切成小段逐段识别后合并，不依赖 OSS 或百炼临时文件 URL。

也可以使用统一入口，通过 `--source` 决定输入类型：

```powershell
douyin-llmwiki ingest --source url "https://v.douyin.com/xxx/"
douyin-llmwiki ingest --source file "C:\path\to\video.mp4" --source-url "https://v.douyin.com/xxx/" --title "视频标题"
douyin-llmwiki ingest --source auto "C:\path\to\video.mp4"
```

输出文件默认写入：

```text
<OBSIDIAN_VAULT_PATH>/<LLMWIKI_DIR>/YYYY/YYYY-MM-DD_<标题或视频ID>.md
```

第一版只处理单个公开分享链接，不支持批量、登录态、私密内容。

## Codex Skill

仓库内提供了一个独立 Codex Skill 分发目录：`douyin-llmwiki-skill/`。这个 Skill 已经和上面的远程 ASR/下载 CLI 工作流解耦，只处理本地转写文本文件，例如 `111.txt`，由 Codex 或其他本地 agent 直接总结，再写入 Obsidian。

单独说明文档见：`douyin-llmwiki-skill/README.md`。真正需要安装到 Codex 的 Skill 本体是：`douyin-llmwiki-skill/douyin-llmwiki/`。

本地安装：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\douyin-llmwiki-skill\douyin-llmwiki" "$env:USERPROFILE\.codex\skills\"
```

安装后，在 Codex 中可以直接说：

```text
把 C:\Users\ELAINA\Downloads\111.txt 总结成 Obsidian 知识笔记，放到 LLMWiki/LocalTranscripts 目录。
```

也可以直接用 Skill 附带的本地辅助脚本扫描 Vault：

```powershell
python "$env:USERPROFILE\.codex\skills\douyin-llmwiki\scripts\obsidian_transcript_note.py" discover --json
```

该 Skill 不需要 `.env`、DashScope、百炼、OSS、`ffmpeg`、`yt-dlp`、`douyin_crawl` 或 `douyin-llmwiki` CLI。

## 测试

```powershell
python -m unittest discover -s tests
```
