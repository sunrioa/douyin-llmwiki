from pathlib import Path
import tempfile
import unittest

from douyin_llmwiki.config import Config
from douyin_llmwiki.models import DownloadResult, Summary, Transcript, TranscriptSegment, VideoMetadata
from douyin_llmwiki.workflow import IngestWorkflow


class FakeDownloader:
    def __init__(self, audio_path: Path) -> None:
        self.audio_path = audio_path

    def download(self, input_text: str) -> DownloadResult:
        return DownloadResult(
            audio_path=self.audio_path,
            metadata=VideoMetadata(
                source_url="https://v.douyin.com/abc/",
                video_id="abc",
                title="测试视频",
                uploader="作者",
            ),
        )


class FakeStorage:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    def upload_and_sign(self, path: Path, object_key: str) -> str:
        self.object_key = object_key
        return "https://oss.example.com/audio.mp3?signature=1"

    def delete(self, object_key: str) -> None:
        self.deleted.append(object_key)


class FakeASR:
    def transcribe(self, file_url: str) -> Transcript:
        return Transcript(
            text="这是一段测试转写。",
            segments=[TranscriptSegment(text="这是一段测试转写。", start_ms=0, end_ms=1200)],
        )


class FakeSummarizer:
    def summarize(self, transcript_text: str, metadata: VideoMetadata) -> Summary:
        return Summary(
            summary="这是一段测试摘要。",
            key_points=["核心观点"],
            concepts=["关键概念"],
            actions=["后续行动"],
            tags=["测试"],
            related_topics=["相关主题"],
        )


class WorkflowTest(unittest.TestCase):
    def test_ingest_writes_obsidian_note_and_deletes_oss_object(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vault = root / "vault"
            vault.mkdir()
            audio_path = root / "audio.mp3"
            audio_path.write_bytes(b"fake")
            storage = FakeStorage()
            config = Config(
                dashscope_api_key="key",
                aliyun_access_key_id="ak",
                aliyun_access_key_secret="sk",
                aliyun_oss_endpoint="https://oss-cn-hangzhou.aliyuncs.com",
                aliyun_oss_bucket="bucket",
                obsidian_vault_path=vault,
            )

            result = IngestWorkflow(
                config=config,
                cache_dir=root / "cache",
                downloader=FakeDownloader(audio_path),
                storage=storage,
                asr=FakeASR(),
                summarizer=FakeSummarizer(),
            ).ingest("https://v.douyin.com/abc/")

            self.assertTrue(result.note_path.exists())
            self.assertIn("LLMWiki", str(result.note_path))
            self.assertIn("这是一段测试摘要。", result.note_path.read_text(encoding="utf-8"))
            self.assertEqual(storage.deleted, [storage.object_key])
            self.assertFalse(audio_path.exists())


if __name__ == "__main__":
    unittest.main()
