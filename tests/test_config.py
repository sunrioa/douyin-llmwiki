import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from douyin_llmwiki.config import Config
from douyin_llmwiki.errors import ConfigError


class ConfigTest(unittest.TestCase):
    def test_bailian_storage_is_default_and_does_not_require_oss_env(self) -> None:
        with tempfile.TemporaryDirectory() as vault:
            with patch.dict(
                os.environ,
                {
                    "DASHSCOPE_API_KEY": "dashscope-key",
                    "OBSIDIAN_VAULT_PATH": vault,
                    "YT_DLP_COOKIES_FROM_BROWSER": "edge",
                    "YT_DLP_COOKIE_FILE": str(Path(vault) / "cookies.txt"),
                    "DOUYIN_DOWNLOADER": "douyin_crawl",
                    "DOUYIN_CRAWL_PATH": str(Path(vault) / "douyin_crawl"),
                },
                clear=True,
            ):
                config = Config.from_env()

        self.assertEqual(config.storage_backend, "bailian")
        self.assertEqual(config.obsidian_vault_path, Path(vault))
        self.assertEqual(config.aliyun_oss_bucket, "")
        self.assertEqual(config.yt_dlp_cookies_from_browser, "edge")
        self.assertEqual(config.yt_dlp_cookie_file, Path(vault) / "cookies.txt")
        self.assertEqual(config.douyin_downloader, "douyin-crawl")
        self.assertEqual(config.douyin_crawl_path, Path(vault) / "douyin_crawl")
        self.assertEqual(config.douyin_cookie_file, Path(vault) / "cookies.txt")

    def test_oss_storage_requires_oss_env(self) -> None:
        with tempfile.TemporaryDirectory() as vault:
            with patch.dict(
                os.environ,
                {
                    "DASHSCOPE_API_KEY": "dashscope-key",
                    "OBSIDIAN_VAULT_PATH": vault,
                    "STORAGE_BACKEND": "oss",
                },
                clear=True,
            ):
                with self.assertRaises(ConfigError) as context:
                    Config.from_env()

        self.assertIn("ALIYUN_ACCESS_KEY_ID", str(context.exception))


if __name__ == "__main__":
    unittest.main()
