import contextlib
import io
import pathlib
import tempfile

import portable_pack


def main():
    print("Environment Migration | synthetic local demo")
    print("All files are temporary. No personal files are read.")
    with tempfile.TemporaryDirectory() as temporary:
        workspace = pathlib.Path(temporary).resolve()
        source = workspace / "old-computer"
        source.mkdir()
        (source / "notes.txt").write_text("User-owned project notes", encoding="utf-8")
        (source / "project.lock").write_text("Pinned dependency versions", encoding="utf-8")
        (source / "empty-folder").mkdir()
        scope = workspace / "scope.json"
        targets = workspace / "targets.json"
        package = workspace / "transfer"
        destination = workspace / "new-computer"
        portable_pack.write_json(scope, {"roots": {"work": str(source)}})
        portable_pack.write_json(targets, {"work": str(destination)})
        with contextlib.redirect_stdout(io.StringIO()):
            portable_pack.pack(scope, package)
        manifest = portable_pack.verify(package)
        print(f"1. Capture: {len(manifest['files'])} files + empty folder")
        print("2. Verify: archive + per-file SHA-256 passed")
        with contextlib.redirect_stdout(io.StringIO()):
            portable_pack.restore(package, targets)
        if destination.exists():
            raise RuntimeError("Preview unexpectedly wrote files")
        print("3. Preview: target mapping checked, zero writes")
        with contextlib.redirect_stdout(io.StringIO()):
            portable_pack.restore(package, targets, apply=True)
        for item in manifest["files"]:
            if portable_pack.sha256(destination / item["path"]) != item["sha256"]:
                raise RuntimeError("Restored bytes differ")
        print("4. Restore: files match captured hashes")
        (destination / "notes.txt").write_text("Keep my destination changes", encoding="utf-8")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                portable_pack.restore(package, targets, apply=True)
        except ValueError as error:
            if "conflicts" not in str(error):
                raise
        else:
            raise RuntimeError("A differing file was not rejected")
        if (destination / "notes.txt").read_text(encoding="utf-8") != "Keep my destination changes":
            raise RuntimeError("Destination changes were lost")
        print("5. Conflict: differing file refused and preserved")
    print("PASS | temporary workspace removed")


if __name__ == "__main__":
    main()
