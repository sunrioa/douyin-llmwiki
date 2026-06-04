import unittest

from douyin_llmwiki.summarizer import parse_summary_json


class SummarizerTest(unittest.TestCase):
    def test_parse_summary_json_from_fenced_content(self) -> None:
        summary = parse_summary_json(
            """```json
{
  "summary": "这是一段摘要。",
  "key_points": ["观点一"],
  "concepts": [{"name": "概念", "description": "解释"}],
  "actions": [],
  "tags": ["AI", "#知识库"],
  "related_topics": ["Obsidian"]
}
```"""
        )

        self.assertEqual(summary.summary, "这是一段摘要。")
        self.assertEqual(summary.key_points, ["观点一"])
        self.assertEqual(summary.concepts, ["概念：解释"])
        self.assertEqual(summary.related_topics, ["Obsidian"])


if __name__ == "__main__":
    unittest.main()
