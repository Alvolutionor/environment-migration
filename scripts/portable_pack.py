import argparse
import hashlib
import json
import os
import pathlib
import platform
import re
import shutil
import sqlite3
import stat
import sys
import tempfile
import unicodedata
import zipfile


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))


def sha256(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    pathlib.Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def inside(path, parent):
    return path == parent or parent in path.parents


def portable_name(value):
    return unicodedata.normalize("NFC", str(value)).casefold()


def linked(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def clean_path(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError(f"Unsafe relative path: {value!r}")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"Unsafe relative path: {value!r}")
    return parts


def absolute_path(value):
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(f"An absolute path is required: {value}")
    cursor = path
    while True:
        if os.path.lexists(cursor) and linked(cursor):
            raise ValueError(f"Linked path component: {cursor}")
        if cursor == cursor.parent:
            break
        cursor = cursor.parent
    return path.resolve()


def roots_from(values, require_existing=False):
    if not isinstance(values, dict) or not values:
        raise ValueError("At least one logical root is required")
    result = {}
    for key, value in values.items():
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", key):
            raise ValueError(f"Unsafe root ID: {key!r}")
        path = absolute_path(value)
        if require_existing and not path.is_dir():
            raise ValueError(f"Missing source directory: {path}")
        for other in result.values():
            parts = tuple(portable_name(part) for part in path.parts)
            other_parts = tuple(portable_name(part) for part in other.parts)
            if parts[:len(other_parts)] == other_parts or other_parts[:len(parts)] == parts:
                raise ValueError("Overlapping roots are not supported")
        result[key] = path
    return result


def child(root, relative):
    result = root
    for part in clean_path(relative):
        if os.name == "nt":
            stem = part.split(".")[0].upper()
            if part.endswith((" ", ".")) or any(c in part for c in '<>"|?*') or stem in {
                "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))
            }:
                raise ValueError(f"Unsupported Windows filename: {part}")
        result = result / part
        if os.path.lexists(result) and linked(result):
            raise ValueError(f"Linked destination: {result}")
    return result


def pack(config_path, output):
    config = read_json(config_path)
    roots = roots_from(config["roots"], require_existing=True)
    excluded = config.get("exclude_names", [])
    if not isinstance(excluded, list) or any(not isinstance(item, str) or not item for item in excluded):
        raise ValueError("exclude_names must be an array of nonempty names")
    exports = config.get("sqlite_exports", [])
    if not isinstance(exports, list) or any(not isinstance(item, str) for item in exports):
        raise ValueError("sqlite_exports must be an array of logical root/path names")
    for export in exports:
        parts = clean_path(export)
        if len(parts) < 2 or parts[0] not in roots:
            raise ValueError(f"Unknown SQLite export path: {export}")
    output = absolute_path(output)
    if any(inside(output, root) or inside(root, output) for root in roots.values()):
        raise ValueError("Package and source directories must be disjoint")
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"version": 1, "source_host": platform.node(), "source_os": platform.system(),
                "source_roots": {key: str(value) for key, value in roots.items()},
                "files": [], "directories": [], "omissions": []}
    with zipfile.ZipFile(output / "payload.zip", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for key, root in roots.items():
            def walk(directory):
                for entry in sorted(directory.iterdir()):
                    relative = entry.relative_to(root).as_posix()
                    clean_path(relative)
                    if entry.name in excluded:
                        manifest["omissions"].append({"root": key, "path": relative, "reason": "explicit name exclusion"})
                        continue
                    if linked(entry):
                        raise ValueError(f"Link or reparse point requires a native adapter: {entry}")
                    info = entry.stat()
                    if stat.S_ISDIR(info.st_mode):
                        manifest["directories"].append({"root": key, "path": relative})
                        walk(entry)
                    elif stat.S_ISREG(info.st_mode):
                        with entry.open("rb") as source:
                            header = source.read(16)
                            source.seek(0)
                            if entry.name.endswith(("-wal", "-shm", "-journal")):
                                raise ValueError(f"SQLite state requires a consistent export: {entry}")
                            if header == b"SQLite format 3\x00":
                                if f"{key}/{relative}" not in exports:
                                    raise ValueError(f"SQLite state requires a consistent export: {entry}")
                                if any(pathlib.Path(str(entry) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
                                    raise ValueError(f"SQLite export has live sidecars: {entry}")
                                database = sqlite3.connect(entry.as_uri() + "?mode=ro&immutable=1", uri=True)
                                try:
                                    if database.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                                        raise ValueError(f"Invalid SQLite export: {entry}")
                                finally:
                                    database.close()
                            digest = hashlib.sha256()
                            size = 0
                            with archive.open(f"{key}/{relative}", "w", force_zip64=True) as target:
                                while block := source.read(1024 * 1024):
                                    target.write(block)
                                    digest.update(block)
                                    size += len(block)
                        after = entry.stat()
                        if size != info.st_size or (info.st_size, info.st_mtime_ns, info.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                            raise ValueError(f"Source changed during capture: {entry}")
                        manifest["files"].append({"root": key, "path": relative, "size": size,
                                                  "sha256": digest.hexdigest(), "mtime_ns": info.st_mtime_ns})
                    else:
                        raise ValueError(f"Special file requires a native adapter: {entry}")
            walk(root)
    manifest["archive_sha256"] = sha256(output / "payload.zip")
    write_json(output / "manifest.json", manifest)
    verify(output)
    print(json.dumps({"package": str(output), "manifest_sha256": sha256(output / "manifest.json"),
                      "files": len(manifest["files"]), "omissions": len(manifest["omissions"])}))


def verify(package):
    package = pathlib.Path(package)
    manifest = read_json(package / "manifest.json")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("source_roots"), dict):
        raise ValueError("Invalid manifest structure")
    if any(not isinstance(manifest.get(key), str) for key in ("source_host", "source_os", "archive_sha256")):
        raise ValueError("Invalid manifest source or digest")
    if any(not isinstance(manifest.get(key), list) for key in ("files", "directories", "omissions")):
        raise ValueError("Invalid manifest entry arrays")
    if manifest["version"] != 1 or sha256(package / "payload.zip") != manifest["archive_sha256"]:
        raise ValueError("Unsupported manifest or archive hash mismatch")
    root_ids = set(manifest["source_roots"])
    if not root_ids or any(not re.fullmatch(r"[a-zA-Z0-9_-]+", key) for key in root_ids):
        raise ValueError("Invalid manifest roots")
    paths = set()
    file_paths = set()
    portable_paths = set()
    for kind in ("directories", "files"):
        for item in manifest[kind]:
            if not isinstance(item, dict):
                raise ValueError("Invalid manifest entry")
            clean_path(item["path"])
            if item["root"] not in root_ids:
                raise ValueError("Unknown manifest root")
            name = f"{item['root']}/{item['path']}"
            if name in paths:
                raise ValueError("Duplicate manifest path")
            portable = (item["root"], portable_name(item["path"]))
            if portable in portable_paths:
                raise ValueError("Filename collision under case folding or Unicode normalization")
            portable_paths.add(portable)
            paths.add(name)
            if kind == "files":
                if type(item["size"]) is not int or item["size"] < 0:
                    raise ValueError("Invalid manifest file size")
                if type(item["mtime_ns"]) is not int or not 0 <= item["mtime_ns"] < 2**63:
                    raise ValueError("Unsupported manifest modification time")
                if not isinstance(item["sha256"], str) or not re.fullmatch("[a-f0-9]{64}", item["sha256"]):
                    raise ValueError("Invalid manifest file digest")
                file_paths.add(name)
    if any(parent.as_posix() in file_paths for name in paths for parent in pathlib.PurePosixPath(name).parents):
        raise ValueError("A manifest file is also a parent directory")
    for name in paths:
        for parent in pathlib.PurePosixPath(name).parents:
            if len(parent.parts) > 1 and parent.as_posix() not in paths:
                raise ValueError("Missing parent directory in manifest")
    with zipfile.ZipFile(package / "payload.zip") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != file_paths:
            raise ValueError("Archive entries differ from manifest")
        for item in manifest["files"]:
            name = f"{item['root']}/{item['path']}"
            digest = hashlib.sha256()
            size = 0
            with archive.open(name) as stream:
                while block := stream.read(1024 * 1024):
                    size += len(block)
                    digest.update(block)
            if size != item["size"] or digest.hexdigest() != item["sha256"]:
                raise ValueError(f"File integrity mismatch: {name}")
    return manifest


def restore(package, targets_path, apply=False):
    manifest = verify(package)
    roots = roots_from(read_json(targets_path))
    if set(roots) != set(manifest["source_roots"]):
        raise ValueError("Destination IDs must exactly match package root IDs")
    if manifest["source_host"].casefold() == platform.node().casefold():
        for value in manifest["source_roots"].values():
            source = pathlib.Path(value).resolve()
            if any(inside(target, source) or inside(source, target) for target in roots.values()):
                raise ValueError("Restoration overlaps source directories")
    package_path = pathlib.Path(package).resolve()
    if any(inside(package_path, root) or inside(root, package_path) for root in roots.values()):
        raise ValueError("Restoration overlaps package directory")
    destinations = {}
    for item in manifest["directories"] + manifest["files"]:
        path = child(roots[item["root"]], item["path"])
        canonical = os.path.normcase(str(path))
        if canonical in destinations:
            raise ValueError(f"Destination filename collision: {path}")
        destinations[canonical] = path
    conflicts = []
    for root in roots.values():
        if root.exists() and not root.is_dir():
            conflicts.append(str(root))
    for item in manifest["directories"]:
        path = child(roots[item["root"]], item["path"])
        if path.exists() and not path.is_dir():
            conflicts.append(str(path))
    pending = []
    for item in manifest["files"]:
        path = child(roots[item["root"]], item["path"])
        if path.exists():
            if not path.is_file() or sha256(path) != item["sha256"]:
                conflicts.append(str(path))
        else:
            pending.append((item, path))
    print(json.dumps({"apply": apply, "missing_files": len(pending), "conflicts": conflicts}))
    if conflicts:
        raise ValueError("Restore conflicts must be resolved before applying")
    if not apply:
        return
    for root in roots.values():
        root.mkdir(parents=True, exist_ok=True)
    for item in manifest["directories"]:
        child(roots[item["root"]], item["path"]).mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(pathlib.Path(package) / "payload.zip") as archive:
        for item, path in pending:
            path = child(roots[item["root"]], item["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(prefix=".migration-", dir=path.parent)
            temporary = pathlib.Path(temporary)
            try:
                with os.fdopen(descriptor, "wb") as output, archive.open(f"{item['root']}/{item['path']}") as source:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                if sha256(temporary) != item["sha256"]:
                    raise ValueError(f"Restored file hash mismatch: {path}")
                if os.path.lexists(path):
                    raise ValueError(f"Destination appeared during restore: {path}")
                os.replace(temporary, path)
                os.utime(path, ns=(item["mtime_ns"], item["mtime_ns"]))
            finally:
                temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Explicit-root portable file migration; no service exports or link restoration")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("pack")
    capture.add_argument("--config", required=True)
    capture.add_argument("--output", required=True)
    check = commands.add_parser("verify")
    check.add_argument("--package", required=True)
    recover = commands.add_parser("restore")
    recover.add_argument("--package", required=True)
    recover.add_argument("--targets", required=True)
    recover.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "pack":
            pack(args.config, args.output)
        elif args.command == "verify":
            manifest = verify(args.package)
            print(json.dumps({"verified_files": len(manifest["files"])}))
        else:
            restore(args.package, args.targets, args.apply)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error, zipfile.BadZipFile) as error:
        print(f"Migration failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
