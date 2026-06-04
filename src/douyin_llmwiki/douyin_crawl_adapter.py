from __future__ import annotations

import http.cookiejar as cookiejar
import os
import re
import subprocess
import sys
from pathlib import Path

from .downloader import LocalFileDownloader
from .errors import DownloadError
from .models import DownloadResult
from .utils import extract_first_url, sanitize_filename


class DouyinCrawlDownloader:
    MEDIA_EXTENSIONS = {".mp4", ".m4v", ".mov", ".webm"}

    def __init__(
        self,
        cache_dir: Path,
        crawl_path: Path,
        cookie_file: Path,
        download_dir: Path | None = None,
        python_executable: str | None = None,
    ) -> None:
        self.cache_dir = cache_dir.resolve()
        self.crawl_path = crawl_path.resolve()
        self.cookie_file = cookie_file.resolve()
        self.download_dir = (download_dir or (cache_dir / "douyin-crawl-downloads")).resolve()
        self.python_executable = python_executable or sys.executable

    def download(self, input_text: str) -> DownloadResult:
        url = extract_first_url(input_text)
        self._validate()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        raw_cookie_file = self._prepare_raw_cookie_file()
        before = self._media_files()

        command = [
            self.python_executable,
            str(self.crawl_path / "douyin_cli.py"),
            "-u",
            url,
            "-o",
            str(self.download_dir),
            "--cookie",
            str(raw_cookie_file),
        ]
        completed = subprocess.run(
            command,
            cwd=self.crawl_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            check=False,
        )
        if completed.returncode != 0:
            raise DownloadError(
                "douyin_crawl failed to download the video: "
                + _trim_output(completed.stderr or completed.stdout)
            )

        media_path = self._resolve_downloaded_media(before, completed.stdout + "\n" + completed.stderr)
        local = LocalFileDownloader(
            cache_dir=self.cache_dir,
            source_url=url,
            title=media_path.stem,
            video_id=sanitize_filename(media_path.stem, "douyin-video", max_chars=48),
        )
        result = local.download(str(media_path))
        return result

    def _validate(self) -> None:
        if not self.crawl_path.exists():
            raise DownloadError(f"DOUYIN_CRAWL_PATH does not exist: {self.crawl_path}")
        cli_path = self.crawl_path / "douyin_cli.py"
        if not cli_path.exists():
            raise DownloadError(f"douyin_cli.py was not found under DOUYIN_CRAWL_PATH: {cli_path}")
        if not self.cookie_file.exists():
            raise DownloadError(f"DOUYIN_COOKIE_FILE does not exist: {self.cookie_file}")

    def _prepare_raw_cookie_file(self) -> Path:
        raw_cookie = cookie_file_to_header(self.cookie_file)
        if not raw_cookie:
            raise DownloadError(f"No Douyin cookies were found in {self.cookie_file}")
        output = self.cache_dir / "douyin-crawl-cookie.txt"
        output.write_text(raw_cookie, encoding="utf-8")
        return output

    def _media_files(self) -> set[Path]:
        return {
            path
            for path in self.download_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in self.MEDIA_EXTENSIONS
        }

    def _resolve_downloaded_media(self, before: set[Path], output: str) -> Path:
        after = self._media_files()
        new_files = sorted(after - before, key=lambda path: path.stat().st_mtime, reverse=True)
        if new_files:
            return new_files[0]

        for candidate in _candidate_paths_from_output(output):
            path = candidate if candidate.is_absolute() else (self.crawl_path / candidate)
            if path.exists() and path.suffix.lower() in self.MEDIA_EXTENSIONS:
                return path

        all_files = sorted(after, key=lambda path: path.stat().st_mtime, reverse=True)
        if all_files:
            return all_files[0]

        raise DownloadError(
            "douyin_crawl completed but no downloaded mp4/mov/webm file was found under "
            f"{self.download_dir}."
        )


def cookie_file_to_header(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return ""
    if not text.startswith("# Netscape HTTP Cookie File"):
        return _normalize_raw_cookie_text(text)

    jar = cookiejar.MozillaCookieJar(str(path))
    jar.load(ignore_discard=True, ignore_expires=True)
    pairs: list[str] = []
    seen: set[str] = set()
    for cookie in jar:
        if "douyin.com" not in cookie.domain and "iesdouyin.com" not in cookie.domain:
            continue
        if not cookie.value:
            continue
        key = cookie.name
        if key in seen:
            continue
        seen.add(key)
        pairs.append(f"{cookie.name}={cookie.value}")
    return "; ".join(pairs)


def _normalize_raw_cookie_text(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.lower().startswith("cookie:"):
            return line.split(":", 1)[1].strip()
    return " ".join(line.strip() for line in text.splitlines() if line.strip())


def _candidate_paths_from_output(output: str) -> list[Path]:
    candidates: list[Path] = []
    for match in re.finditer(r"([A-Za-z]:\\[^\r\n]+?\.(?:mp4|m4v|mov|webm))", output, re.IGNORECASE):
        candidates.append(Path(match.group(1).strip().strip('"')))
    return candidates


def _trim_output(output: str, max_chars: int = 1200) -> str:
    output = output.strip()
    if len(output) <= max_chars:
        return output
    return output[:max_chars].rstrip() + "..."
