from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .errors import DownloadError
from .media import duration_seconds, extract_audio_to_mp3, has_audio_stream, probe_audio
from .models import DownloadResult, VideoMetadata
from .utils import extract_first_url, sanitize_filename


class YtDlpDownloader:
    def __init__(
        self,
        cache_dir: Path,
        cookies_from_browser: str = "",
        cookie_file: Path | None = None,
    ) -> None:
        self.cache_dir = cache_dir
        self.cookies_from_browser = cookies_from_browser
        self.cookie_file = cookie_file

    def download(self, input_text: str) -> DownloadResult:
        try:
            import yt_dlp
        except ImportError as exc:
            raise DownloadError(
                "yt-dlp Python package is not installed. Run `pip install -e .` first."
            ) from exc

        url = extract_first_url(input_text)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        options: dict[str, Any] = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "outtmpl": str(self.cache_dir / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        if self.cookie_file:
            if not self.cookie_file.exists():
                raise DownloadError(f"YT_DLP_COOKIE_FILE does not exist: {self.cookie_file}")
            options["cookiefile"] = str(self.cookie_file)
        elif self.cookies_from_browser:
            options["cookiesfrombrowser"] = parse_cookies_from_browser(self.cookies_from_browser)

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                audio_path = self._resolve_audio_path(ydl, info)
        except Exception as exc:  # yt-dlp raises multiple custom exception types.
            message = str(exc)
            if "Fresh cookies" in message and (self.cookie_file or self.cookies_from_browser):
                raise DownloadError(
                    "yt-dlp loaded the configured cookie source, but Douyin still rejected "
                    "the web detail API response. This usually means the current Douyin Web "
                    "API requires additional signed parameters such as a_bogus/X-Bogus that "
                    "yt-dlp does not handle for this page. Use `ingest --source file` with a "
                    "locally saved mp4, or switch to a dedicated Douyin downloader backend."
                ) from exc
            raise DownloadError(
                "Failed to download public Douyin audio. Verify the link is public, "
                "then try upgrading yt-dlp if Douyin changed its page format."
            ) from exc

        if not audio_path.exists():
            raise DownloadError(f"Downloaded audio file was not found: {audio_path}")

        probe = probe_audio(audio_path)
        if not has_audio_stream(probe):
            raise DownloadError(f"Downloaded file has no audio stream: {audio_path}")

        return DownloadResult(audio_path=audio_path, metadata=self._metadata(url, info))

    def _resolve_audio_path(self, ydl: Any, info: dict[str, Any]) -> Path:
        requested = info.get("requested_downloads") or []
        for item in requested:
            filepath = item.get("filepath") or item.get("_filename")
            if filepath and Path(filepath).exists():
                return Path(filepath)

        prepared = Path(ydl.prepare_filename(info))
        mp3_path = prepared.with_suffix(".mp3")
        if mp3_path.exists():
            return mp3_path
        if prepared.exists():
            return prepared

        video_id = str(info.get("id") or "")
        if video_id:
            candidates = sorted(self.cache_dir.glob(f"{video_id}.*"), key=lambda p: p.stat().st_mtime)
            if candidates:
                return candidates[-1]
        raise DownloadError("yt-dlp completed but no audio output path could be resolved.")

    def _metadata(self, source_url: str, info: dict[str, Any]) -> VideoMetadata:
        tags = info.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        return VideoMetadata(
            source_url=source_url,
            video_id=str(info.get("id") or "douyin-video"),
            title=str(info.get("title") or info.get("id") or "Douyin Video"),
            webpage_url=info.get("webpage_url") or source_url,
            uploader=info.get("uploader") or info.get("creator") or info.get("channel"),
            duration_seconds=info.get("duration"),
            upload_date=info.get("upload_date"),
            description=info.get("description"),
            tags=[str(tag) for tag in tags],
        )


def parse_cookies_from_browser(value: str) -> tuple[str, ...]:
    browser, separator, profile = value.strip().partition(":")
    browser = browser.strip()
    profile = profile.strip()
    if not browser:
        raise DownloadError("YT_DLP_COOKIES_FROM_BROWSER is empty.")
    if not separator:
        return (browser,)
    if not profile:
        raise DownloadError(
            "YT_DLP_COOKIES_FROM_BROWSER must be like 'edge', 'chrome:Default', "
            "or 'chrome:C:\\path\\to\\Profile'."
        )
    return (browser, profile)


class LocalFileDownloader:
    def __init__(
        self,
        cache_dir: Path,
        source_url: str | None = None,
        title: str | None = None,
        uploader: str | None = None,
        video_id: str | None = None,
    ) -> None:
        self.cache_dir = cache_dir
        self.source_url = source_url
        self.title = title
        self.uploader = uploader
        self.video_id = video_id

    def download(self, input_text: str) -> DownloadResult:
        source_path = Path(input_text).expanduser()
        if not source_path.exists():
            raise DownloadError(f"Local media file does not exist: {source_path}")
        if not source_path.is_file():
            raise DownloadError(f"Local media path is not a file: {source_path}")

        probe = probe_audio(source_path)
        if not has_audio_stream(probe):
            raise DownloadError(f"Local media file has no audio stream: {source_path}")

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        title = self.title or source_path.stem
        video_id = self.video_id or sanitize_filename(source_path.stem, "local-media", max_chars=48)
        target_path = self.cache_dir / f"{sanitize_filename(video_id, 'local-media', max_chars=48)}.mp3"

        if source_path.suffix.lower() == ".mp3":
            shutil.copy2(source_path, target_path)
        else:
            extract_audio_to_mp3(source_path, target_path)

        metadata = VideoMetadata(
            source_url=self.source_url or source_path.resolve().as_uri(),
            video_id=video_id,
            title=title,
            webpage_url=self.source_url,
            uploader=self.uploader,
            duration_seconds=duration_seconds(probe),
        )
        return DownloadResult(audio_path=target_path, metadata=metadata)
