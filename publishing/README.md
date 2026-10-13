# Distribution and directory submissions

## Available channels

| Channel | Status | Entry point |
| --- | --- | --- |
| GitHub | Public source and release downloads | https://github.com/Alvolutionor/environment-migration |
| skills.sh | Skill page publicly reachable; real isolated installation completed | https://skills.sh/alvolutionor/environment-migration/environment-migration |
| Codex community marketplace | Repository catalog provided; native packaged-plugin installation tested | `codex plugin marketplace add Alvolutionor/environment-migration` |
| Claude Code community marketplace | Repository catalog provided; strict manifest validation and isolated installation tested | `claude plugin marketplace add Alvolutionor/environment-migration` |
| OpenAI public directory | Package prepared; not submitted or approved | https://platform.openai.com/plugins |
| Anthropic public directory | Package prepared; not submitted or approved | https://claude.ai/directory/manage |
| SkillHub | CLI available, but no authenticated publishing session; not published | https://www.skillhub.club/app/skills |

Directory status is a publication record, not an endorsement. Repository catalogs and public vendor directories are different distribution sources.

## Build the upload packages

```sh
python scripts/build_release.py
```

The builder reads the canonical root skill and emits allowlisted standalone and portable plugin ZIPs in `dist/`, plus `SHA256SUMS.txt`. It does not copy `.git`, inventories, caches, or user migration payloads. The plugin archive contains `plugin.json`, a Claude-compatible manifest, and `skills/environment-migration/`. The root skill remains the single source of runtime files.

## OpenAI directory

Upload the **plugin** ZIP from the matching GitHub release. Select the verified publisher that owns this repository. The package declares `requires_local_executor: true` because migration requires access to local files. It is skills-only and does not need an MCP endpoint.

Wait for metadata and skill checks. Correct findings in the source manifests or skill, rebuild, and upload a new package. Review identity information and any policy attestations personally before submitting. After approval, publish from the portal. Local CLI validation cannot establish portal eligibility or approval.

Official references: [package layout](https://developers.openai.com/plugins/build/plugins), [submission](https://developers.openai.com/plugins/deploy/submission), [desktop-only skills](https://developers.openai.com/plugins/deploy/desktop-only).

## Anthropic directory

Use the public repository URL and plugin path `.` in the developer portal, or upload the compatible plugin archive when offered. The repository's `.claude-plugin/plugin.json` points to its canonical root skill; the generated upload archive points to the packaged `skills/` directory.

Submission requires an eligible paid Claude account and the appropriate organization role. The public directory and the curated `claude-plugins-official` marketplace have different entry paths. Do not claim an official-marketplace listing from a community repository install.

Official references: [publish a plugin](https://code.claude.com/docs/en/plugins/publish), [manifest validation](https://code.claude.com/docs/en/plugins-reference).

## SkillHub

The public CLI is `@skill-hub/cli`. Its `whoami` command reports no authenticated session in the publication environment. Complete the publisher login, then create or upload this skill through the web publishing flow. Do not repurpose GitHub CLI credentials as a third-party service token.

## Community outreach

Use the factual announcement in [community-post.md](community-post.md). Link the live skills.sh page, source, demo, and release. Invite synthetic bug reports and successful migration reports. Do not claim unattended software migration, guaranteed ranking, or new-machine validation that has not occurred.

Some curated lists require existing community adoption or prohibit automated submissions. Respect those rules; do not submit a brand-new skill to those lists simply to acquire links.
