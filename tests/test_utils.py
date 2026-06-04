from pathlib import Path
import tempfile
import unittest

from douyin_llmwiki.utils import ensure_unique_path, extract_first_url, format_ms, sanitize_filename
from douyin_llmwiki.downloader import parse_cookies_from_browser


class UtilsTest(unittest.TestCase):
    def test_extract_first_url_from_share_text(self) -> None:
        text = "看看这个视频 https://v.douyin.com/abc123/ 复制此链接"
        self.assertEqual(extract_first_url(text), "https://v.douyin.com/abc123/")

    def test_sanitize_filename_for_windows(self) -> None:
        self.assertEqual(sanitize_filename('a<b>c:"/\\|?* d'), "a b c d")

    def test_ensure_unique_path_appends_counter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "note.md"
            path.write_text("existing", encoding="utf-8")
            self.assertEqual(ensure_unique_path(path).name, "note_2.md")

    def test_format_ms(self) -> None:
        self.assertEqual(format_ms(3_723_045), "01:02:03.045")

    def test_parse_cookies_from_browser(self) -> None:
        self.assertEqual(parse_cookies_from_browser("chrome:Default"), ("chrome", "Default"))
        self.assertEqual(
            parse_cookies_from_browser(r"chrome:C:\Temp\Chrome Profile\Default"),
            ("chrome", r"C:\Temp\Chrome Profile\Default"),
        )


if __name__ == "__main__":
    unittest.main()
