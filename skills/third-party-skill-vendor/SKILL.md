---
name: third-party-skill-vendor
description: Use when adding, installing, syncing, or updating third-party Codex skills under ~/.codex, including requests that mention npx skills add, skills add, GitHub skill repositories, external skill installers, third-party skills, vendor diffs, skills/third-party.toml, or skills/third-party.lock.json. Ensures third-party skills are vendored through this repo's manifest and lock workflow instead of being installed directly as final state.
metadata:
  short-description: Vendor third-party Codex skills with lock files
---

# Third-Party Skill Vendor

Use this skill before generic skill installers for any third-party Codex skill work in
`~/.codex`.

## Rule

Do not treat external installer commands, such as `npx skills add ...`, as the
final installation path for third-party skills in this repo. They may be used
only to discover metadata when necessary.

The durable source of truth is:

- `skills/third-party.toml` for configured sources
- `skills/third-party.lock.json` for resolved commits
- `skills/<name>` for vendored skill files

## Workflow

1. Read the relevant local context:
   - `AGENTS.md`
   - `README.md`
   - `skills/third-party.toml`
   - `scripts/skill-vendor.py` when command behavior is unclear
2. Parse the request into:
   - skill `name`
   - Git repository, usually `owner/repo` or a Git URL
   - source `path` inside the repo
   - `ref`, defaulting to `main` unless the request or repo requires another ref
   - destination, normally `skills/<name>`
3. If the source path is unknown, inspect the repository metadata or tree and
   choose the path containing the desired `SKILL.md`. Prefer an explicit user
   value over inference.
4. Add or update exactly one `[[skill]]` block in `skills/third-party.toml`.
5. Run:

```bash
python3 scripts/skill-vendor.py update <name>
python3 scripts/skill-vendor.py verify <name>
git diff -- skills/third-party.toml skills/third-party.lock.json skills/<name>
```

6. Report the vendored path, locked commit, verification result, and any
   remaining blocker. Tell the user to restart Codex to pick up new skills after
   a successful install or update.

## Guardrails

- Preserve unrelated dirty files and unrelated third-party skill entries.
- Do not use `--force` unless the user explicitly approves overwriting dirty
  vendored files.
- Do not remove existing skill directories unless `skill-vendor.py update` or
  `sync` is replacing the configured destination.
- If the user supplies an installer command, translate it into this manifest
  workflow rather than running it directly as the installation.
- If a network command fails because of sandbox restrictions, rerun it with the
  required escalation instead of switching to an untracked install path.
