import importlib.util
import contextlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = pathlib.Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("build_release", ROOT / "scripts/build_release.py")
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class DistributionTests(unittest.TestCase):
    def test_portable_plugin_contains_working_resources_and_local_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = pathlib.Path(temporary)
            with contextlib.redirect_stdout(io.StringIO()):
                artifacts = release.build(output)
            filename = next(name for name in artifacts if "-plugin-" in name)
            with zipfile.ZipFile(output / filename) as archive:
                self.assertFalse(any("/.git/" in name or "inventory/" in name or "__pycache__" in name for name in archive.namelist()))
                archive.extractall(output / "extracted")
            plugin = output / "extracted/environment-migration"
            manifest = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["extensions"]["com.openai"]["requires_local_executor"])
            for key in ("composerIcon", "logo"):
                self.assertTrue((plugin / manifest["extensions"]["com.openai"]["interface"][key]).is_file())
            skill = plugin / "skills/environment-migration"
            self.assertTrue((skill / "SKILL.md").is_file())
            result = subprocess.run([sys.executable, str(skill / "scripts/portable_pack.py"), "--help"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_standalone_download_runs_the_full_synthetic_demo(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = pathlib.Path(temporary)
            with contextlib.redirect_stdout(io.StringIO()):
                artifacts = release.build(output)
            filename = next(name for name in artifacts if "-skill-" in name)
            with zipfile.ZipFile(output / filename) as archive:
                archive.extractall(output / "extracted")
            script = output / "extracted/environment-migration/scripts/demo.py"
            result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
