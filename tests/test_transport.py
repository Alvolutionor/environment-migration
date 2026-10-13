import contextlib
import importlib.util
import io
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


SPEC = importlib.util.spec_from_file_location("portable_pack", pathlib.Path(__file__).parents[1] / "scripts" / "portable_pack.py")
transport = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transport)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name).resolve()
        self.source = self.base / "source"
        self.source.mkdir()
        (self.source / "empty").mkdir()
        (self.source / "unicode-\u8fc1\u79fb.txt").write_text("portable \u6587\u4ef6", encoding="utf-8")
        (self.source / "bun.lock").write_text("preserve dependency state", encoding="utf-8")
        (self.source / "binary.bin").write_bytes(bytes(range(256)) * 8193)
        self.package = self.base / "package"
        self.destination = self.base / "destination"
        self.config = self.base / "scope.json"
        self.targets = self.base / "targets.json"
        transport.write_json(self.config, {"roots": {"work": str(self.source)}})
        transport.write_json(self.targets, {"work": str(self.destination)})

    def capture(self):
        with contextlib.redirect_stdout(io.StringIO()):
            transport.pack(self.config, self.package)

    def restore(self, apply=False):
        with contextlib.redirect_stdout(io.StringIO()):
            transport.restore(self.package, self.targets, apply)

    def rewrite_manifest(self, change):
        manifest = transport.read_json(self.package / "manifest.json")
        change(manifest)
        transport.write_json(self.package / "manifest.json", manifest)

    def test_round_trip_preview_idempotence_and_empty_directory(self):
        self.capture()
        self.restore()
        self.assertFalse(self.destination.exists())
        self.restore(True)
        self.assertTrue((self.destination / "empty").is_dir())
        for original in self.source.iterdir():
            if original.is_file():
                self.assertEqual(original.read_bytes(), (self.destination / original.name).read_bytes())
        self.restore(True)
        self.assertEqual(len(transport.verify(self.package)["files"]), 3)

    def test_conflict_never_overwritten(self):
        self.capture()
        self.destination.mkdir()
        conflict = self.destination / "bun.lock"
        conflict.write_text("destination work", encoding="utf-8")
        for apply in (False, True):
            with self.assertRaisesRegex(ValueError, "conflicts"):
                self.restore(apply)
        self.assertEqual(conflict.read_text(encoding="utf-8"), "destination work")
        self.assertFalse((self.destination / "binary.bin").exists())

    def test_corruption_prevents_any_restore(self):
        self.capture()
        with (self.package / "payload.zip").open("ab") as stream:
            stream.write(b"corrupt")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.restore(True)
        self.assertFalse(self.destination.exists())

    def test_file_hash_mismatch_detected(self):
        self.capture()
        self.rewrite_manifest(lambda data: data["files"][0].update(sha256="0" * 64))
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            transport.verify(self.package)

    def test_traversal_manifest_rejected(self):
        self.capture()
        self.rewrite_manifest(lambda data: data["files"][0].update(path="../escape"))
        with self.assertRaisesRegex(ValueError, "Unsafe relative"):
            self.restore(True)
        self.assertFalse((self.base / "escape").exists())

    def test_unlisted_archive_entry_rejected(self):
        self.capture()
        with zipfile.ZipFile(self.package / "payload.zip", "a") as archive:
            archive.writestr("work/extra", b"extra")
        self.rewrite_manifest(lambda data: data.update(archive_sha256=transport.sha256(self.package / "payload.zip")))
        with self.assertRaisesRegex(ValueError, "entries differ"):
            self.restore(True)

    def test_live_sqlite_rejected(self):
        with contextlib.closing(sqlite3.connect(self.source / "state.db")) as database:
            database.execute("create table state (value text)")
            database.commit()
        with self.assertRaisesRegex(ValueError, "SQLite state"):
            self.capture()
        self.assertFalse((self.package / "manifest.json").exists())

    def test_completed_sqlite_export_round_trip(self):
        with contextlib.closing(sqlite3.connect(self.source / "export.sqlite")) as database:
            database.execute("create table state (value text)")
            database.execute("insert into state values ('portable')")
            database.commit()
        transport.write_json(self.config, {"roots": {"work": str(self.source)}, "sqlite_exports": ["work/export.sqlite"]})
        self.capture()
        self.restore(True)
        with contextlib.closing(sqlite3.connect(self.destination / "export.sqlite")) as database:
            self.assertEqual(database.execute("select value from state").fetchall(), [("portable",)])

    def test_sqlite_export_with_sidecar_rejected(self):
        with contextlib.closing(sqlite3.connect(self.source / "export.sqlite")) as database:
            database.execute("create table state (value text)")
            database.commit()
        (self.source / "export.sqlite-wal").write_bytes(b"active state")
        transport.write_json(self.config, {"roots": {"work": str(self.source)}, "sqlite_exports": ["work/export.sqlite"]})
        with self.assertRaisesRegex(ValueError, "sidecars"):
            self.capture()

    def test_case_and_unicode_collisions_rejected_before_restore(self):
        self.capture()
        for first, second in (("Folder", "folder"), ("caf\u00e9", "cafe\u0301")):
            manifest = transport.read_json(self.package / "manifest.json")
            manifest["directories"] = [{"root": "work", "path": first}, {"root": "work", "path": second}]
            transport.write_json(self.package / "manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "Filename collision"):
                self.restore(True)
            self.assertFalse(self.destination.exists())

    def test_malformed_metadata_rejected_before_restore(self):
        self.capture()
        self.rewrite_manifest(lambda data: data["files"][0].update(mtime_ns=-1))
        with self.assertRaisesRegex(ValueError, "modification time"):
            self.restore(True)
        self.assertFalse(self.destination.exists())

    def test_missing_parent_directory_rejected(self):
        self.capture()
        self.rewrite_manifest(lambda data: data["files"][0].update(path="missing/file.txt"))
        with self.assertRaisesRegex(ValueError, "Missing parent"):
            self.restore(True)

    def test_source_change_during_capture_rejected(self):
        original_open = zipfile.ZipFile.open

        @contextlib.contextmanager
        def changing_open(archive, name, mode="r", **kwargs):
            with original_open(archive, name, mode, **kwargs) as stream:
                yield stream
            if mode == "w" and name == "work/bun.lock":
                (self.source / "bun.lock").write_text("changed during capture", encoding="utf-8")

        with mock.patch.object(zipfile.ZipFile, "open", changing_open):
            with self.assertRaisesRegex(ValueError, "Source changed"):
                self.capture()
        self.assertFalse((self.package / "manifest.json").exists())

    def test_command_line_round_trip_and_failure_exit(self):
        script = str(pathlib.Path(transport.__file__))

        def run(*arguments):
            return subprocess.run([sys.executable, script, *map(str, arguments)], capture_output=True, text=True, encoding="utf-8")

        captured = run("pack", "--config", self.config, "--output", self.package)
        self.assertEqual(captured.returncode, 0, captured.stderr)
        self.assertEqual(len(json.loads(captured.stdout)["manifest_sha256"]), 64)
        checked = run("verify", "--package", self.package)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        preview = run("restore", "--package", self.package, "--targets", self.targets)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertFalse(self.destination.exists())
        applied = run("restore", "--package", self.package, "--targets", self.targets, "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        (self.destination / "bun.lock").write_text("conflict", encoding="utf-8")
        conflict = run("restore", "--package", self.package, "--targets", self.targets, "--apply")
        self.assertEqual(conflict.returncode, 1)
        self.assertIn("conflicts", conflict.stderr)

    def test_output_cannot_be_inside_source(self):
        with self.assertRaisesRegex(ValueError, "disjoint"):
            transport.pack(self.config, self.source / "package")

    def test_explicit_exclusion_recorded_without_dropping_lockfile(self):
        (self.source / "node_modules").mkdir()
        (self.source / "node_modules" / "dependency.js").write_text("generated", encoding="utf-8")
        transport.write_json(self.config, {"roots": {"work": str(self.source)}, "exclude_names": ["node_modules"]})
        self.capture()
        manifest = transport.verify(self.package)
        self.assertEqual(manifest["omissions"][0]["path"], "node_modules")
        self.assertIn("bun.lock", [item["path"] for item in manifest["files"]])

    def test_same_source_restore_rejected(self):
        self.capture()
        transport.write_json(self.targets, {"work": str(self.source)})
        with self.assertRaisesRegex(ValueError, "overlaps source"):
            self.restore(True)

    def test_package_destination_overlap_rejected(self):
        self.capture()
        transport.write_json(self.targets, {"work": str(self.package / "restored")})
        with self.assertRaisesRegex(ValueError, "overlaps package"):
            self.restore(True)

    def test_symlink_source_rejected(self):
        link = self.source / "linked"
        try:
            link.symlink_to(self.source / "bun.lock")
        except OSError:
            self.skipTest("Symlink creation is unavailable")
        with self.assertRaisesRegex(ValueError, "Link or reparse"):
            self.capture()

    def test_symlink_destination_parent_rejected(self):
        self.capture()
        actual = self.base / "actual"
        actual.mkdir()
        try:
            self.destination.symlink_to(actual, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink creation is unavailable")
        with self.assertRaisesRegex(ValueError, "Linked path"):
            self.restore(True)
        self.assertEqual(list(actual.iterdir()), [])

    def test_nested_source_roots_rejected(self):
        transport.write_json(self.config, {"roots": {"work": str(self.source), "nested": str(self.source / "empty")}})
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            self.capture()

    def test_file_directory_collision_rejected(self):
        self.capture()
        self.rewrite_manifest(lambda data: data["directories"].append({"root": "work", "path": "bun.lock/child"}))
        with self.assertRaisesRegex(ValueError, "parent directory"):
            self.restore(True)


if __name__ == "__main__":
    unittest.main()
