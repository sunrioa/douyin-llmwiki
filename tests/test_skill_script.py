from pathlib import Path
import importlib.util
import unittest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "douyin-llmwiki-skill"
    / "douyin-llmwiki"
    / "scripts"
    / "run_douyin_llmwiki.py"
)


def load_script_module():
    spec = importlib.util.spec_from_file_location("run_douyin_llmwiki", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SkillScriptTest(unittest.TestCase):
    def test_builds_installed_cli_command_for_url_input(self) -> None:
        script = load_script_module()

        command, cwd, env = script.build_command(
            input_text="https://v.douyin.com/abc/",
            source="url",
            env_file=".env",
            cache_dir=".cache/douyin-llmwiki",
            project=None,
            source_url=None,
            title=None,
            uploader=None,
            video_id=None,
            skip_preflight=False,
        )

        self.assertEqual(
            command,
            [
                "douyin-llmwiki",
                "--env-file",
                ".env",
                "--cache-dir",
                ".cache/douyin-llmwiki",
                "ingest",
                "--source",
                "url",
                "https://v.douyin.com/abc/",
            ],
        )
        self.assertIsNone(cwd)
        self.assertEqual(env, {})

    def test_builds_project_python_command_for_local_file_input(self) -> None:
        script = load_script_module()
        project = Path("C:/repo/douyin-llmwiki")

        command, cwd, env = script.build_command(
            input_text="C:/video.mp4",
            source="file",
            env_file="C:/repo/douyin-llmwiki/.env",
            cache_dir="C:/repo/douyin-llmwiki/.cache/douyin-llmwiki",
            project=project,
            source_url="https://v.douyin.com/abc/",
            title="视频标题",
            uploader=None,
            video_id="abc",
            skip_preflight=True,
        )

        self.assertEqual(command[1:3], ["-m", "douyin_llmwiki.cli"])
        self.assertIn(str(project / "src"), env["PYTHONPATH"])
        self.assertEqual(cwd, project)
        self.assertIn("--skip-preflight", command)
        self.assertIn("--source-url", command)
        self.assertIn("https://v.douyin.com/abc/", command)
        self.assertIn("--title", command)
        self.assertIn("视频标题", command)
        self.assertIn("--video-id", command)
        self.assertIn("abc", command)


if __name__ == "__main__":
    unittest.main()
