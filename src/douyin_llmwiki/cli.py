from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from .asr import QwenFlashASR
from .config import Config, load_env_file
from .douyin_crawl_adapter import DouyinCrawlDownloader
from .downloader import LocalFileDownloader
from .errors import LLMWikiError
from .preflight import check_preflight, doctor_lines
from .storage import LocalPathStorage
from .workflow import IngestWorkflow


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return run_doctor(args)
    if args.command == "ingest":
        return run_ingest(args)
    if args.command == "ingest-file":
        return run_ingest_file(args)

    parser.print_help()
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="douyin-llmwiki",
        description="Ingest public Douyin video audio into an Obsidian LLMWiki note.",
    )
    parser.add_argument("--env-file", default=".env", help="Path to .env file. Default: .env")
    parser.add_argument(
        "--cache-dir",
        default=".cache/douyin-llmwiki",
        help="Local working cache directory. Default: .cache/douyin-llmwiki",
    )
    subparsers = parser.add_subparsers(dest="command")

    ingest = subparsers.add_parser("ingest", help="Process one Douyin URL or local media file.")
    ingest.add_argument("input", help="Douyin share text/URL or local media file path.")
    ingest.add_argument(
        "--source",
        choices=("url", "file", "auto"),
        default="url",
        help="Input source mode. Default: url.",
    )
    add_local_metadata_options(ingest)
    ingest.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip local ffmpeg/yt-dlp dependency checks.",
    )

    ingest_file = subparsers.add_parser(
        "ingest-file",
        help="Process one local audio/video file without downloading from Douyin.",
    )
    ingest_file.add_argument("path", help="Local audio/video file path.")
    add_local_metadata_options(ingest_file)
    ingest_file.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip local ffmpeg/yt-dlp dependency checks.",
    )

    subparsers.add_parser("doctor", help="Check local tools and configuration.")
    return parser


def run_ingest(args: argparse.Namespace) -> int:
    if args.source == "file" or (args.source == "auto" and Path(args.input).expanduser().exists()):
        args.path = args.input
        return run_ingest_file(args)

    try:
        load_env_file(Path(args.env_file))
        if not args.skip_preflight:
            check_preflight()
        config = Config.from_env()
        if config.douyin_downloader == "douyin-crawl":
            return run_ingest_douyin_crawl(args, config)
        workflow = IngestWorkflow(
            config=config,
            cache_dir=Path(args.cache_dir),
            progress=lambda message: print(f"[douyin-llmwiki] {message}", file=sys.stderr),
        )
        result = workflow.ingest(args.input)
    except LLMWikiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130

    print(result.note_path)
    return 0


def run_ingest_douyin_crawl(args: argparse.Namespace, config: Config) -> int:
    try:
        if not config.douyin_crawl_path:
            raise LLMWikiError("DOUYIN_CRAWL_PATH is required when DOUYIN_DOWNLOADER=douyin_crawl.")
        if not config.douyin_cookie_file:
            raise LLMWikiError("DOUYIN_COOKIE_FILE or YT_DLP_COOKIE_FILE is required for douyin_crawl.")

        cache_dir = Path(args.cache_dir)
        local_config = replace(config, asr_model=config.local_asr_model)
        downloader = DouyinCrawlDownloader(
            cache_dir=cache_dir,
            crawl_path=config.douyin_crawl_path,
            cookie_file=config.douyin_cookie_file,
            download_dir=config.douyin_download_dir,
        )
        workflow = IngestWorkflow(
            config=local_config,
            cache_dir=cache_dir,
            downloader=downloader,
            storage=LocalPathStorage(),
            asr=QwenFlashASR(
                api_key=config.dashscope_api_key,
                model=config.local_asr_model,
                base_url=config.summary_base_url,
            ),
            progress=lambda message: print(f"[douyin-llmwiki] {message}", file=sys.stderr),
        )
        result = workflow.ingest(args.input)
    except LLMWikiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130

    print(result.note_path)
    return 0


def add_local_metadata_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-url", help="Original source URL to write into the note.")
    parser.add_argument("--title", help="Note title. Defaults to the file name.")
    parser.add_argument("--uploader", help="Uploader/author metadata.")
    parser.add_argument("--video-id", help="Stable source id. Defaults to the file name.")


def run_ingest_file(args: argparse.Namespace) -> int:
    try:
        load_env_file(Path(args.env_file))
        if not args.skip_preflight:
            check_preflight()
        config = Config.from_env()
        local_config = replace(config, asr_model=config.local_asr_model)
        cache_dir = Path(args.cache_dir)
        downloader = LocalFileDownloader(
            cache_dir=cache_dir,
            source_url=args.source_url,
            title=args.title,
            uploader=args.uploader,
            video_id=args.video_id,
        )
        workflow = IngestWorkflow(
            config=local_config,
            cache_dir=cache_dir,
            downloader=downloader,
            storage=LocalPathStorage(),
            asr=QwenFlashASR(
                api_key=config.dashscope_api_key,
                model=config.local_asr_model,
                base_url=config.summary_base_url,
            ),
            progress=lambda message: print(f"[douyin-llmwiki] {message}", file=sys.stderr),
        )
        result = workflow.ingest(args.path)
    except LLMWikiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130

    print(result.note_path)
    return 0


def run_doctor(args: argparse.Namespace) -> int:
    load_env_file(Path(args.env_file))
    for line in doctor_lines():
        print(line)

    try:
        Config.from_env()
    except LLMWikiError as exc:
        print(f"config: {exc}")
        return 1

    print("config: OK")
    return 0
