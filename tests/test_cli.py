import unittest

from douyin_llmwiki.cli import build_parser


class CliTest(unittest.TestCase):
    def test_ingest_defaults_to_url_source(self) -> None:
        args = build_parser().parse_args(["ingest", "https://v.douyin.com/example/"])
        self.assertEqual(args.command, "ingest")
        self.assertEqual(args.source, "url")

    def test_ingest_accepts_file_source_metadata(self) -> None:
        args = build_parser().parse_args(
            [
                "ingest",
                "--source",
                "file",
                "C:\\video.mp4",
                "--source-url",
                "https://v.douyin.com/example/",
                "--title",
                "标题",
            ]
        )
        self.assertEqual(args.source, "file")
        self.assertEqual(args.input, "C:\\video.mp4")
        self.assertEqual(args.source_url, "https://v.douyin.com/example/")
        self.assertEqual(args.title, "标题")


if __name__ == "__main__":
    unittest.main()
