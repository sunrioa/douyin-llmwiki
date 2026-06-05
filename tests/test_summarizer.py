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
  "knowledge_title": "知识沉淀",
  "knowledge_definition": "把输入整理成可复用知识。",
  "use_cases": ["学习笔记"],
  "prerequisites": ["有转写文本"],
  "workflow_steps": ["提取概念", "生成模板"],
  "decision_rules": ["能复用才沉淀"],
  "pitfalls": ["只写摘要"],
  "practice_template": ["目标：..."],
  "review_questions": ["如何复用？"],
  "transferable_methods": ["结构化萃取"],
  "actions": [],
  "tags": ["AI", "#知识库"],
  "related_topics": ["Obsidian"]
}
```"""
        )

        self.assertEqual(summary.summary, "这是一段摘要。")
        self.assertEqual(summary.key_points, ["观点一"])
        self.assertEqual(summary.concepts, ["概念：解释"])
        self.assertEqual(summary.knowledge_title, "知识沉淀")
        self.assertEqual(summary.workflow_steps, ["提取概念", "生成模板"])
        self.assertEqual(summary.review_questions, ["如何复用？"])
        self.assertEqual(summary.related_topics, ["Obsidian"])


if __name__ == "__main__":
    unittest.main()
