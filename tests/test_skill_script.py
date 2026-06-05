from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import tempfile
import unittest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "douyin-llmwiki-skill"
    / "douyin-llmwiki"
    / "scripts"
    / "obsidian_transcript_note.py"
)


def load_script_module():
    spec = importlib.util.spec_from_file_location("obsidian_transcript_note", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SkillScriptTest(unittest.TestCase):
    def test_discovers_obsidian_vaults_from_roots(self) -> None:
        script = load_script_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vault = root / "Knowledge Vault"
            (vault / ".obsidian").mkdir(parents=True)
            (root / "not-a-vault").mkdir()

            found = script.discover_vaults([root], max_depth=3)

            self.assertEqual(found, [vault])

    def test_writes_note_to_user_directory_with_summary_and_transcript(self) -> None:
        script = load_script_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vault = root / "Vault"
            (vault / ".obsidian").mkdir(parents=True)
            transcript = root / "111.txt"
            transcript.write_text("这是本地语音转写后的文字。", encoding="utf-8")

            note_path = script.write_note(
                transcript_path=transcript,
                vault_path=vault,
                directory_template="LLMWiki/Local/{year}",
                title="Agent 推理架构",
                source="local-asr",
                summary={
                    "knowledge_title": "Agent 推理架构选择",
                    "knowledge_definition": "根据任务复杂度选择合适的 Agent 推理方式。",
                    "summary": "这是一段由本地 agent 总结出的摘要。",
                    "key_points": ["ReAct 适合交互式推理", "ReWOO 适合减少模型调用"],
                    "workflow_steps": ["判断任务是否需要工具反馈", "选择推理架构"],
                    "actions": ["整理自己的 Agent 场景"],
                    "tags": ["Agent", "知识库"],
                    "related_topics": ["ReAct", "ReWOO"],
                },
                created_at=datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc),
            )

            self.assertEqual(note_path.parent, vault / "LLMWiki" / "Local" / "2026")
            content = note_path.read_text(encoding="utf-8")
            self.assertIn("note_type: local-transcript-summary", content)
            self.assertIn("# Agent 推理架构", content)
            self.assertIn("## 知识沉淀", content)
            self.assertIn("**主题**：Agent 推理架构选择", content)
            self.assertIn("## 操作流程", content)
            self.assertIn("1. 判断任务是否需要工具反馈", content)
            self.assertIn("## 完整转写", content)
            self.assertIn("这是本地语音转写后的文字。", content)

    def test_rejects_directory_template_that_escapes_vault(self) -> None:
        script = load_script_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vault = root / "Vault"
            (vault / ".obsidian").mkdir(parents=True)
            transcript = root / "111.txt"
            transcript.write_text("转写文本", encoding="utf-8")

            with self.assertRaises(ValueError):
                script.write_note(
                    transcript_path=transcript,
                    vault_path=vault,
                    directory_template="../outside",
                    title="测试",
                    source="",
                    summary={},
                    created_at=datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc),
                )


if __name__ == "__main__":
    unittest.main()
