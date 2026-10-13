import argparse
import hashlib
import json
import pathlib
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_FILES = ["SKILL.md", "scripts/portable_pack.py", "scripts/demo.py", "references/platforms.md",
               "references/capture-and-restore.md", "references/transport.md"]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def add_bytes(archive, name, content):
    entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
    entry.compress_type = zipfile.ZIP_DEFLATED
    entry.create_system = 3
    entry.external_attr = 0o100644 << 16
    archive.writestr(entry, content)


def build(output):
    output = pathlib.Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    claude = read_json(ROOT / ".claude-plugin/plugin.json")
    codex = read_json(ROOT / ".codex-plugin/plugin.json")
    if (claude["name"], claude["version"]) != (codex["name"], codex["version"]):
        raise ValueError("Plugin identities and versions must match")
    if "screenshots" in codex.get("interface", {}):
        raise ValueError("Skills-only submissions must not include interface.screenshots")
    portable = {"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"}
    for key in ("name", "version", "description", "author", "homepage", "repository", "license", "keywords"):
        portable[key] = codex[key]
    portable["extensions"] = {"com.openai": {
        "requires_local_executor": True,
        "interface": codex["interface"],
    }}
    claude["skills"] = ["./skills/"]
    version = portable["version"]
    packages = {}
    for kind in ("skill", "plugin"):
        filename = f"environment-migration-{kind}-v{version}.zip"
        target = output / filename
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            prefix = "environment-migration/"
            for name in SKILL_FILES:
                path = ROOT / name
                entry = prefix + (f"skills/environment-migration/{name}" if kind == "plugin" else name)
                add_bytes(archive, entry, path.read_bytes())
            for name in ("README.md", "LICENSE", "PRIVACY.md"):
                source = ROOT / f"publishing/{kind}-readme.md" if name == "README.md" else ROOT / name
                add_bytes(archive, prefix + name, source.read_bytes())
            if kind == "plugin":
                add_bytes(archive, prefix + "plugin.json", json.dumps(portable, indent=2) + "\n")
                add_bytes(archive, prefix + ".claude-plugin/plugin.json", json.dumps(claude, indent=2) + "\n")
                add_bytes(archive, prefix + "assets/icon.svg", (ROOT / "assets/icon.svg").read_bytes())
        packages[filename] = hashlib.sha256(target.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text("".join(f"{digest}  {name}\n" for name, digest in packages.items()), encoding="utf-8")
    print(json.dumps({"version": version, "artifacts": packages}, indent=2))
    return packages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build allowlisted standalone skill and portable plugin ZIPs")
    parser.add_argument("--output", default=str(ROOT / "dist"))
    build(parser.parse_args().output)
