from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command, cwd, env_overlay = build_command(
        input_text=args.input,
        source=args.source,
        env_file=args.env_file,
        cache_dir=args.cache_dir,
        project=args.project,
        source_url=args.source_url,
        title=args.title,
        uploader=args.uploader,
        video_id=args.video_id,
        skip_preflight=args.skip_preflight,
    )
    if args.dry_run:
        print(format_command(command))
        return 0

    env = os.environ.copy()
    env.update(env_overlay)
    completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the douyin-llmwiki CLI from an installed package or local project checkout."
    )
    parser.add_argument("input", help="Douyin share text/URL or local media file path.")
    parser.add_argument("--source", choices=("url", "file", "auto"), default="auto")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--cache-dir", default=".cache/douyin-llmwiki")
    parser.add_argument(
        "--project",
        type=Path,
        default=_default_project(),
        help="Optional douyin-llmwiki project checkout. Defaults to DOUYIN_LLMWIKI_PROJECT.",
    )
    parser.add_argument("--source-url")
    parser.add_argument("--title")
    parser.add_argument("--uploader")
    parser.add_argument("--video-id")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without running it.")
    return parser


def build_command(
    *,
    input_text: str,
    source: str,
    env_file: str,
    cache_dir: str,
    project: Path | None,
    source_url: str | None,
    title: str | None,
    uploader: str | None,
    video_id: str | None,
    skip_preflight: bool,
) -> tuple[list[str], Path | None, dict[str, str]]:
    command, cwd, env = _base_command(project)
    command.extend(["--env-file", env_file, "--cache-dir", cache_dir, "ingest", "--source", source])
    if skip_preflight:
        command.append("--skip-preflight")
    for option, value in (
        ("--source-url", source_url),
        ("--title", title),
        ("--uploader", uploader),
        ("--video-id", video_id),
    ):
        if value:
            command.extend([option, value])
    command.append(input_text)
    return command, cwd, env


def _base_command(project: Path | None) -> tuple[list[str], Path | None, dict[str, str]]:
    if project is None:
        return ["douyin-llmwiki"], None, {}

    project = project.expanduser().resolve()
    python_exe = _project_python(project)
    pythonpath = str(project / "src")
    existing = os.environ.get("PYTHONPATH")
    if existing:
        pythonpath = os.pathsep.join([pythonpath, existing])
    return [str(python_exe), "-m", "douyin_llmwiki.cli"], project, {"PYTHONPATH": pythonpath}


def _project_python(project: Path) -> Path:
    if os.name == "nt":
        candidate = project / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = project / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else Path(sys.executable)


def _default_project() -> Path | None:
    value = os.environ.get("DOUYIN_LLMWIKI_PROJECT", "").strip()
    return Path(value) if value else None


def format_command(command: list[str]) -> str:
    return subprocess.list2cmdline(command) if os.name == "nt" else " ".join(_shell_quote(part) for part in command)


def _shell_quote(value: str) -> str:
    if not value or any(char.isspace() or char in "'\"\\$`" for char in value):
        return "'" + value.replace("'", "'\"'\"'") + "'"
    return value


if __name__ == "__main__":
    raise SystemExit(main())
