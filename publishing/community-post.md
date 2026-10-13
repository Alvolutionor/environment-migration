# Environment Migration: a local-first skill for moving to a new computer

I built an open-source skill for Codex and Claude Code that helps prepare a working environment for a different computer without hardcoded home paths or drive letters.

It discovers the source setup, separates portable files from rebuildable tools and native service exports, and requires explicit destination folder mappings. The bundled Python transport checks archive and per-file SHA-256 hashes, previews restoration, and refuses to overwrite differing destination files.

Install:

```sh
npx skills add Alvolutionor/environment-migration --skill environment-migration
```

Try the self-contained synthetic demo after cloning:

```sh
python scripts/demo.py
```

The core transport was tested on Windows, macOS, and Linux with Python 3.10 and 3.13. Real new-machine software installation, service imports, and device-bound credential recovery are separate procedures and remain outside that test coverage. Migration ZIPs are unencrypted.

- Source and demo: https://github.com/Alvolutionor/environment-migration
- Skill listing: https://skills.sh/alvolutionor/environment-migration/environment-migration
- Downloads: https://github.com/Alvolutionor/environment-migration/releases

MIT licensed. No hosted migration service, account requirement, or transport telemetry. I would welcome reports of successful migrations, missing native adapters, and reproducible failures using synthetic files. Please do not post real migration payloads or credentials.
