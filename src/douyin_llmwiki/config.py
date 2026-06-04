from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError


@dataclass(frozen=True)
class Config:
    dashscope_api_key: str
    obsidian_vault_path: Path
    aliyun_access_key_id: str = ""
    aliyun_access_key_secret: str = ""
    aliyun_oss_endpoint: str = ""
    aliyun_oss_bucket: str = ""
    storage_backend: str = "bailian"
    llmwiki_dir: str = "LLMWiki/Douyin"
    summary_model: str = "qwen-plus"
    asr_model: str = "qwen3-asr-flash-filetrans"
    local_asr_model: str = "qwen3-asr-flash"
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    bailian_file_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    summary_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    oss_signed_url_expires: int = 7200
    asr_poll_interval_seconds: float = 5.0
    asr_timeout_seconds: int = 7200
    max_summary_chunk_chars: int = 12000
    yt_dlp_cookies_from_browser: str = ""
    yt_dlp_cookie_file: Path | None = None
    douyin_downloader: str = "yt-dlp"
    douyin_crawl_path: Path | None = None
    douyin_cookie_file: Path | None = None
    douyin_download_dir: Path | None = None

    @classmethod
    def from_env(cls) -> "Config":
        storage_backend = os.getenv("STORAGE_BACKEND", "bailian").strip().lower()
        if storage_backend not in {"bailian", "oss"}:
            raise ConfigError("STORAGE_BACKEND must be either 'bailian' or 'oss'.")
        douyin_downloader = normalize_downloader(os.getenv("DOUYIN_DOWNLOADER", "yt-dlp"))

        required = list(BASE_REQUIRED_ENV)
        if storage_backend == "oss":
            required.extend(OSS_REQUIRED_ENV)

        missing = [name for name in required if not os.getenv(name)]
        if missing:
            joined = ", ".join(missing)
            raise ConfigError(f"Missing required environment variables: {joined}")

        vault_path = Path(os.environ["OBSIDIAN_VAULT_PATH"]).expanduser()
        if not vault_path.exists():
            raise ConfigError(f"OBSIDIAN_VAULT_PATH does not exist: {vault_path}")
        if not vault_path.is_dir():
            raise ConfigError(f"OBSIDIAN_VAULT_PATH is not a directory: {vault_path}")

        return cls(
            dashscope_api_key=os.environ["DASHSCOPE_API_KEY"],
            obsidian_vault_path=vault_path,
            aliyun_access_key_id=os.getenv("ALIYUN_ACCESS_KEY_ID", ""),
            aliyun_access_key_secret=os.getenv("ALIYUN_ACCESS_KEY_SECRET", ""),
            aliyun_oss_endpoint=normalize_optional_oss_endpoint(os.getenv("ALIYUN_OSS_ENDPOINT", "")),
            aliyun_oss_bucket=os.getenv("ALIYUN_OSS_BUCKET", ""),
            storage_backend=storage_backend,
            llmwiki_dir=os.getenv("LLMWIKI_DIR", "LLMWiki/Douyin").strip("/\\"),
            summary_model=os.getenv("SUMMARY_MODEL", "qwen-plus"),
            asr_model=os.getenv("ASR_MODEL", "qwen3-asr-flash-filetrans"),
            local_asr_model=os.getenv("LOCAL_ASR_MODEL", "qwen3-asr-flash"),
            dashscope_base_url=os.getenv(
                "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1"
            ).rstrip("/"),
            bailian_file_base_url=os.getenv(
                "BAILIAN_FILE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1"
            ).rstrip("/"),
            summary_base_url=os.getenv(
                "SUMMARY_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ).rstrip("/"),
            oss_signed_url_expires=int(os.getenv("OSS_SIGNED_URL_EXPIRES", "7200")),
            asr_poll_interval_seconds=float(os.getenv("ASR_POLL_INTERVAL_SECONDS", "5")),
            asr_timeout_seconds=int(os.getenv("ASR_TIMEOUT_SECONDS", "7200")),
            max_summary_chunk_chars=int(os.getenv("MAX_SUMMARY_CHUNK_CHARS", "12000")),
            yt_dlp_cookies_from_browser=os.getenv("YT_DLP_COOKIES_FROM_BROWSER", "").strip(),
            yt_dlp_cookie_file=optional_path(os.getenv("YT_DLP_COOKIE_FILE", "")),
            douyin_downloader=douyin_downloader,
            douyin_crawl_path=optional_path(os.getenv("DOUYIN_CRAWL_PATH", "")),
            douyin_cookie_file=optional_path(
                os.getenv("DOUYIN_COOKIE_FILE", "") or os.getenv("YT_DLP_COOKIE_FILE", "")
            ),
            douyin_download_dir=optional_path(os.getenv("DOUYIN_DOWNLOAD_DIR", "")),
        )


BASE_REQUIRED_ENV = (
    "DASHSCOPE_API_KEY",
    "OBSIDIAN_VAULT_PATH",
)

OSS_REQUIRED_ENV = (
    "ALIYUN_ACCESS_KEY_ID",
    "ALIYUN_ACCESS_KEY_SECRET",
    "ALIYUN_OSS_ENDPOINT",
    "ALIYUN_OSS_BUCKET",
)


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(path, override=False)
        return
    except ImportError:
        pass

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def normalize_oss_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip().rstrip("/")
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    return f"https://{endpoint}"


def normalize_optional_oss_endpoint(endpoint: str) -> str:
    if not endpoint.strip():
        return ""
    return normalize_oss_endpoint(endpoint)


def optional_path(value: str) -> Path | None:
    value = value.strip()
    if not value:
        return None
    return Path(value).expanduser()


def normalize_downloader(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if normalized not in {"yt-dlp", "douyin-crawl"}:
        raise ConfigError("DOUYIN_DOWNLOADER must be either 'yt-dlp' or 'douyin_crawl'.")
    return normalized
