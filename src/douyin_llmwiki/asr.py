from __future__ import annotations

import base64
import shutil
import time
from pathlib import Path
from typing import Any

from .errors import ASRError
from .media import duration_seconds, probe_audio, split_audio_to_mp3_chunks
from .models import Transcript, TranscriptSegment
from .transcript import parse_asr_result


class DashScopeASR:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        poll_interval_seconds: float,
        timeout_seconds: int,
        resolve_oss_resource: bool = False,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.resolve_oss_resource = resolve_oss_resource
        self.poll_interval_seconds = poll_interval_seconds
        self.timeout_seconds = timeout_seconds

    def transcribe(self, file_url: str):
        task_id = self._submit(file_url)
        result_url = self._poll(task_id)
        result_json = self._fetch_result(result_url)
        transcript = parse_asr_result(result_json)
        if not transcript.text:
            raise ASRError("ASR succeeded but returned empty transcript text.")
        return transcript

    def _submit(self, file_url: str) -> str:
        requests = _requests()
        response = requests.post(
            f"{self.base_url}/services/audio/asr/transcription",
            headers=self._headers(async_task=True),
            json={
                "model": self.model,
                "input": {"file_urls": [file_url]},
                "parameters": {"enable_words": False},
            },
            timeout=60,
        )
        data = _json_or_error(response, "submit ASR task")
        task_id = (
            data.get("output", {}).get("task_id")
            or data.get("task_id")
            or data.get("output", {}).get("taskId")
        )
        if not task_id:
            raise ASRError(f"ASR submit response did not include task_id: {data}")
        return str(task_id)

    def _poll(self, task_id: str) -> str:
        requests = _requests()
        deadline = time.monotonic() + self.timeout_seconds
        last_payload: dict[str, Any] | None = None

        while time.monotonic() < deadline:
            response = requests.get(
                f"{self.base_url}/tasks/{task_id}",
                headers=self._headers(async_task=False),
                timeout=30,
            )
            data = _json_or_error(response, f"poll ASR task {task_id}")
            last_payload = data
            output = data.get("output", {})
            status = str(output.get("task_status") or output.get("status") or "").upper()

            if status == "SUCCEEDED":
                result = output.get("results") or output.get("result") or output
                result_url = _find_first_key(result, "transcription_url", "url")
                if not result_url:
                    raise ASRError(f"ASR task succeeded without transcription URL: {data}")
                return str(result_url)
            if status in {"FAILED", "CANCELED", "UNKNOWN"}:
                message = output.get("message") or data.get("message") or data
                raise ASRError(f"ASR task {task_id} failed: {message}")

            time.sleep(self.poll_interval_seconds)

        raise ASRError(f"ASR task {task_id} timed out. Last response: {last_payload}")

    def _fetch_result(self, result_url: str) -> dict[str, Any]:
        requests = _requests()
        response = requests.get(result_url, timeout=60)
        return _json_or_error(response, "fetch ASR result")

    def _headers(self, async_task: bool) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if async_task:
            headers["X-DashScope-Async"] = "enable"
        if self.resolve_oss_resource:
            headers["X-DashScope-OssResourceResolve"] = "enable"
        return headers


def _requests():
    try:
        import requests
    except ImportError as exc:
        raise ASRError("requests is not installed. Run `pip install -e .` first.") from exc
    return requests


def _json_or_error(response: Any, action: str) -> dict[str, Any]:
    if response.status_code >= 400:
        raise ASRError(f"Failed to {action}: HTTP {response.status_code} {response.text}")
    try:
        data = response.json()
    except ValueError as exc:
        raise ASRError(f"Failed to {action}: response was not JSON") from exc
    if not isinstance(data, dict):
        raise ASRError(f"Failed to {action}: response JSON was not an object")
    return data


def _find_first_key(value: Any, *keys: str) -> str | None:
    if isinstance(value, dict):
        for key in keys:
            child = value.get(key)
            if isinstance(child, str):
                return child
        for child in value.values():
            result = _find_first_key(child, *keys)
            if result:
                return result
    elif isinstance(value, list):
        for item in value:
            result = _find_first_key(item, *keys)
            if result:
                return result
    return None


class QwenFlashASR:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        segment_seconds: int = 240,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.segment_seconds = segment_seconds

    def transcribe(self, file_url: str) -> Transcript:
        audio_path = Path(file_url)
        if not audio_path.exists():
            raise ASRError(f"Local ASR audio path does not exist: {audio_path}")

        chunk_dir = audio_path.parent / f"{audio_path.stem}_chunks"
        chunks = split_audio_to_mp3_chunks(audio_path, chunk_dir, self.segment_seconds)
        segments: list[TranscriptSegment] = []
        raw_chunks: list[dict[str, Any]] = []
        cursor_ms = 0

        try:
            for index, chunk in enumerate(chunks, start=1):
                text, raw = self._transcribe_chunk(chunk)
                raw_chunks.append(raw)
                chunk_duration = duration_seconds(probe_audio(chunk)) or self.segment_seconds
                end_ms = cursor_ms + int(chunk_duration * 1000)
                segments.append(
                    TranscriptSegment(
                        text=text,
                        start_ms=cursor_ms,
                        end_ms=end_ms,
                        speaker=f"chunk-{index}",
                    )
                )
                cursor_ms = end_ms
        finally:
            shutil.rmtree(chunk_dir, ignore_errors=True)

        full_text = "\n".join(segment.text for segment in segments if segment.text).strip()
        if not full_text:
            raise ASRError("Qwen3-ASR-Flash returned empty transcript text.")
        return Transcript(text=full_text, segments=segments, raw={"chunks": raw_chunks})

    def _transcribe_chunk(self, audio_path: Path) -> tuple[str, dict[str, Any]]:
        requests = _requests()
        data_uri = self._audio_data_uri(audio_path)
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {"data": data_uri},
                            }
                        ],
                    }
                ],
                "stream": False,
            },
            timeout=180,
        )
        data = _json_or_error(response, f"transcribe local audio chunk {audio_path.name}")
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        text = _content_to_text(content).strip()
        if not text:
            raise ASRError(f"Qwen3-ASR-Flash returned empty text for {audio_path.name}: {data}")
        return text, data

    def _audio_data_uri(self, audio_path: Path) -> str:
        encoded = base64.b64encode(audio_path.read_bytes()).decode("ascii")
        return f"data:audio/mpeg;base64,{encoded}"


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                value = item.get("text") or item.get("content")
                if value:
                    parts.append(str(value))
            elif item:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content or "")
