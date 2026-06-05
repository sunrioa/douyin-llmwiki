from datetime import datetime
from datetime import timedelta, timezone
import unittest

from douyin_llmwiki.models import Summary, Transcript, TranscriptSegment, VideoMetadata
from douyin_llmwiki.obsidian import render_note


class ObsidianTest(unittest.TestCase):
    def test_render_note_contains_expected_sections(self) -> None:
        note = render_note(
            metadata=VideoMetadata(
                source_url="https://v.douyin.com/abc/",
                video_id="abc",
                title="测试视频",
                uploader="作者",
            ),
            transcript=Transcript(
                text="你好",
                segments=[TranscriptSegment(text="你好", start_ms=0, end_ms=1000)],
            ),
            summary=Summary(
                summary="摘要",
                key_points=["观点"],
                concepts=["概念"],
                actions=[],
                tags=["测试"],
                related_topics=["主题"],
                knowledge_title="测试知识",
                knowledge_definition="把视频变成知识卡。",
                use_cases=["学习"],
                workflow_steps=["观看", "提炼", "复用"],
                decision_rules=["优先沉淀可执行方法"],
                pitfalls=["只复制原文"],
                practice_template=["场景：..."],
                review_questions=["如何判断适用？"],
                transferable_methods=["结构化总结"],
            ),
            asr_model="qwen3-asr-flash-filetrans",
            summary_model="qwen-plus",
            created_at=datetime(2026, 5, 24, 12, 0, tzinfo=timezone(timedelta(hours=8))),
        )

        self.assertIn("## 摘要", note)
        self.assertIn("note_type: llmwiki-video-summary", note)
        self.assertIn("## 知识沉淀", note)
        self.assertIn("**主题**：测试知识", note)
        self.assertIn("## 操作流程", note)
        self.assertIn("1. 观看", note)
        self.assertIn("## 实践模板", note)
        self.assertIn("## 复习问题", note)
        self.assertIn("## 完整转写", note)
        self.assertIn('- "llmwiki"', note)
        self.assertIn('- "测试"', note)


if __name__ == "__main__":
    unittest.main()
