import json
import tempfile
import unittest
from pathlib import Path

from scripts.bootstrap_project import create_project
from scripts.validate_project import validate_project


class ProjectToolsTest(unittest.TestCase):
    def test_bootstrap_creates_rebuildable_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "demo", 1.1)
            config = json.loads((project / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["production_mode"], "html_explainer")
            self.assertEqual(config["playback_speed"], 1.1)
            self.assertTrue((project / "build_composition.py").is_file())
            self.assertTrue((project / "assets/sfx/transition-click.wav").is_file())
            self.assertTrue((project / "assets/product").is_dir())
            self.assertTrue((project / "assets/ai-broll").is_dir())
            self.assertEqual(validate_project(project), [])

    def test_validator_rejects_speed_outside_audio_filter_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "bad-speed", 1.1)
            config_path = project / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["playback_speed"] = 2.5
            config_path.write_text(json.dumps(config), encoding="utf-8")
            self.assertTrue(any("playback_speed" in item for item in validate_project(project)))

    def test_validator_rejects_other_production_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "wrong-mode", 1.1)
            config_path = project / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["production_mode"] = "talking_head_broll"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            self.assertTrue(any("production_mode" in item for item in validate_project(project)))

    def test_validator_rejects_chapter_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "bad-chapters", 1.1)
            path = project / "chapters.json"
            chapters = json.loads(path.read_text(encoding="utf-8"))
            chapters[1]["start"] += 1
            path.write_text(json.dumps(chapters), encoding="utf-8")
            self.assertTrue(any("章节时间" in item for item in validate_project(project)))

    def test_validator_rejects_missing_visual_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "bad-asset", 1.1)
            path = project / "scenes.json"
            scenes = json.loads(path.read_text(encoding="utf-8"))
            scenes[0]["type"] = "product"
            scenes[0]["asset"] = "assets/product/missing.png"
            path.write_text(json.dumps(scenes), encoding="utf-8")
            self.assertTrue(any("素材不存在" in item for item in validate_project(project)))


if __name__ == "__main__":
    unittest.main()
