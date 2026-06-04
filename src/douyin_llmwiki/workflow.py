from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable
from uuid import uuid4

from .asr import DashScopeASR
from .config import Config
from .downloader import YtDlpDownloader
from .models import IngestResult
from .obsidian import write_obsidian_note
from .storage import BailianTemporaryFileStorage, OssStorage
from .summarizer import QwenSummarizer
from .timeutil import now_shanghai
from .utils import sanitize_filename

Progress = Callable[[str], None]


class IngestWorkflow:
    def __init__(
        self,
        config: Config,
        cache_dir: Path,
        progress: Progress | None = None,
        downloader: object | None = None,
        storage: object | None = None,
        asr: object | None = None,
        summarizer: object | None = None,
    ) -> None:
        self.config = config
        self.cache_dir = cache_dir
        self.progress = progress or (lambda _message: None)
        self.downloader = downloader or YtDlpDownloader(
            cache_dir,
            cookies_from_browser=config.yt_dlp_cookies_from_browser,
            cookie_file=config.yt_dlp_cookie_file,
        )
        self.storage = storage or self._create_storage(config)
        self.asr = asr or DashScopeASR(
            api_key=config.dashscope_api_key,
            model=config.asr_model,
            base_url=config.dashscope_base_url,
            poll_interval_seconds=config.asr_poll_interval_seconds,
            timeout_seconds=config.asr_timeout_seconds,
            resolve_oss_resource=config.storage_backend == "bailian",
        )
        self.summarizer = summarizer or QwenSummarizer(
            api_key=config.dashscope_api_key,
            model=config.summary_model,
            base_url=config.summary_base_url,
            max_chunk_chars=config.max_summary_chunk_chars,
        )

    def ingest(self, input_text: str) -> IngestResult:
        self.progress("准备输入音频")
        download = self.downloader.download(input_text)

        now = now_shanghai()
        object_key = self._object_key(download.audio_path, now)
        self.progress("准备 ASR 输入资源")
        signed_url = self.storage.upload_and_sign(download.audio_path, object_key)

        try:
            self.progress("提交阿里云百炼 ASR 任务并轮询结果")
            transcript = self.asr.transcribe(signed_url)
        finally:
            try:
                self.storage.delete(object_key)
            except Exception as exc:
                self.progress(f"警告：临时音频清理失败：{exc}")
            try:
                download.audio_path.unlink(missing_ok=True)
            except OSError as exc:
                self.progress(f"警告：本地缓存音频删除失败：{exc}")

        self.progress("调用通义千问知识总结 agent")
        summary = self.summarizer.summarize(transcript.text, download.metadata)

        self.progress("写入 Obsidian LLMWiki Markdown 笔记")
        note_path = write_obsidian_note(
            vault_path=self.config.obsidian_vault_path,
            llmwiki_dir=self.config.llmwiki_dir,
            metadata=download.metadata,
            transcript=transcript,
            summary=summary,
            asr_model=self.config.asr_model,
            summary_model=self.config.summary_model,
            now=now,
        )
        return IngestResult(note_path=note_path, metadata=download.metadata)

    def _object_key(self, audio_path: Path, now: datetime) -> str:
        suffix = audio_path.suffix or ".mp3"
        safe_name = sanitize_filename(audio_path.stem, "douyin-audio", max_chars=48)
        return f"douyin-llmwiki/{now:%Y/%m/%d}/{uuid4().hex}_{safe_name}{suffix}"

    def _create_storage(self, config: Config) -> object:
        if config.storage_backend == "oss":
            return OssStorage(
                access_key_id=config.aliyun_access_key_id,
                access_key_secret=config.aliyun_access_key_secret,
                endpoint=config.aliyun_oss_endpoint,
                bucket_name=config.aliyun_oss_bucket,
                signed_url_expires=config.oss_signed_url_expires,
            )
        return BailianTemporaryFileStorage(
            api_key=config.dashscope_api_key,
            base_url=config.bailian_file_base_url,
            model=config.asr_model,
        )
