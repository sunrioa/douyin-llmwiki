from pathlib import Path
import tempfile
import unittest

from douyin_llmwiki.douyin_crawl_adapter import cookie_file_to_header


class DouyinCrawlAdapterTest(unittest.TestCase):
    def test_netscape_cookie_file_is_converted_to_raw_cookie_header(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cookie_file = Path(temp_dir) / "cookies.txt"
            cookie_file.write_text(
                "\n".join(
                    [
                        "# Netscape HTTP Cookie File",
                        ".douyin.com\tTRUE\t/\tTRUE\t1812109825\tttwid\tabc",
                        "www.douyin.com\tFALSE\t/\tTRUE\t1812109825\ts_v_web_id\tverify_x",
                        ".example.com\tTRUE\t/\tTRUE\t1812109825\tignored\tvalue",
                    ]
                ),
                encoding="utf-8",
            )

            header = cookie_file_to_header(cookie_file)

        self.assertIn("ttwid=abc", header)
        self.assertIn("s_v_web_id=verify_x", header)
        self.assertNotIn("ignored=value", header)

    def test_raw_cookie_file_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cookie_file = Path(temp_dir) / "raw.txt"
            cookie_file.write_text("Cookie: a=1; b=2", encoding="utf-8")

            header = cookie_file_to_header(cookie_file)

        self.assertEqual(header, "a=1; b=2")


if __name__ == "__main__":
    unittest.main()
