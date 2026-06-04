from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from douyin_llmwiki.downloader import LocalFileDownloader


class LocalFileDownloaderTest(unittest.TestCase):
    def test_local_mp3_is_copied_to_cache_without_deleting_original(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.mp3"
            source.write_bytes(b"fake mp3")
            cache = root / "cache"

            with patch(
                "douyin_llmwiki.downloader.probe_audio",
                return_value={"streams": [{"codec_type": "audio"}], "format": {"duration": "12.5"}},
            ):
                result = LocalFileDownloader(
                    cache_dir=cache,
                    source_url="https://v.douyin.com/example/",
                    title="本地测试",
                    uploader="作者",
                    video_id="local-id",
                ).download(str(source))

            self.assertTrue(source.exists())
            self.assertEqual(result.audio_path.name, "local-id.mp3")
            self.assertEqual(result.audio_path.read_bytes(), b"fake mp3")
            self.assertEqual(result.metadata.title, "本地测试")
            self.assertEqual(result.metadata.source_url, "https://v.douyin.com/example/")
            self.assertEqual(result.metadata.duration_seconds, 12.5)

    def test_local_video_is_extracted_to_cache_mp3(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.mp4"
            source.write_bytes(b"fake video")
            cache = root / "cache"

            def fake_extract(source_path: Path, target_path: Path) -> Path:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(b"fake extracted audio")
                return target_path

            with patch(
                "douyin_llmwiki.downloader.probe_audio",
                return_value={"streams": [{"codec_type": "audio"}], "format": {"duration": "2"}},
            ), patch("douyin_llmwiki.downloader.extract_audio_to_mp3", side_effect=fake_extract):
                result = LocalFileDownloader(cache_dir=cache).download(str(source))

            self.assertTrue(source.exists())
            self.assertEqual(result.audio_path.suffix, ".mp3")
            self.assertEqual(result.audio_path.read_bytes(), b"fake extracted audio")


if __name__ == "__main__":
    unittest.main()
