# Codex Control Deck

[中文](README.zh-CN.md)

```text
 ____   ___ _____    ____ ___  ____  _______  __
|  _ \ / _ \_   _|  / ___/ _ \|  _ \| ____\ \/ /
| | | | | | || |   | |  | | | | | | |  _|  \  /
| |_| | |_| || |   | |__| |_| | |_| | |___ /  \
|____/ \___/ |_|    \____\___/|____/|_____/_/\_\
```

Codex Control Deck is my personal `.codex` dotfiles repo: the hand-tuned layer of global agent rules, custom slash-command prompts, and local skills that shapes how Codex works on my machines. It tracks only the behavior-defining files and leaves secrets, logs, sessions, caches, and machine-local state outside version control.

## What Lives Here

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Personal global working rules for agents operating under the Codex config tree. |
| `docs/` | Human-facing notes for sharing this deck, including the skill catalog and safe auth setup examples. |
| `prompts/` | Custom prompt files, currently focused on the OPSX/OpenSpec change workflow. |
| `skills/` | User-maintained skills that extend agent behavior for Git, README writing, GitHub Actions, and Proxmox infrastructure workflows. |
| `scripts/` | Local maintenance helpers for repeatable dotfiles operations. |
| `.gitignore` | Allowlist-style ignore rules that keep runtime state and private config out of commits. |

## Console Map

```text
.
|-- AGENTS.md
|-- README.md
|-- README.zh-CN.md
|-- docs/
|   |-- gh-auth-profiles.example.toml
|   |-- skills.md
|   `-- skills.zh-CN.md
|-- prompts/
|   `-- opsx-*.md
|-- scripts/
|   `-- skill-vendor.py
|-- skills/
|   |-- git-workflow-as-user/
|   |-- infra/
|   |-- third-party.lock.json
|   |-- third-party.toml
|   |-- write-github-actions-workflows/
|   `-- write-readmes/
`-- .gitignore
```

## Skills

Skills are the main extension point in this deck. Each skill lives under
`skills/<name>/` and uses `SKILL.md` for agent-facing instructions plus
optional `agents/openai.yaml` UI metadata.

See [docs/skills.md](docs/skills.md) for the skill catalog, maintenance
conventions, and the recommended GitHub auth profile setup. The sanitized
example profile at [docs/gh-auth-profiles.example.toml](docs/gh-auth-profiles.example.toml)
shows how to route `gh` CLI commands through SOPS-encrypted fine-grained PATs.

Do not add README files inside individual skill folders. Put human-facing
overview material in `docs/`, and keep detailed agent instructions in each
skill's `SKILL.md` or `references/` files.

## Third-Party Skills

Third-party skills are vendored into `skills/<name>` so a normal `git pull` is
enough to sync machines. The source manifest is `skills/third-party.toml`; the
resolved commits live in `skills/third-party.lock.json`.

When adding or updating a third-party Codex skill, use the
`third-party-skill-vendor` skill. External installer commands such as
`npx skills add ...` may help identify a source, but the final repo state should
come from the manifest, lock file, and vendored diff below.

Add an entry like this:

```toml
[[skill]]
name = "example"
repo = "owner/repo"
path = "skills/.curated/example"
ref = "main"
dest = "skills/example"
```

Then run:

```bash
python3 scripts/skill-vendor.py update example
python3 scripts/skill-vendor.py verify example
git diff
```

`update` follows the configured `ref`, copies the skill into `skills/<name>`,
and records the exact commit in the lock file. `sync` reinstalls from locked
commits, and `verify` checks that the vendored files still match the lock. The
script refuses to overwrite uncommitted destination changes unless `--force` is
provided.

## Operating Notes

- Treat this repo as personal dotfiles with a sharper edge: small changes can alter future agent behavior.
- Keep project artifacts in English by default; add localized companion docs when useful.
- Do not commit `auth.json`, `config.toml`, session logs, memories, shell snapshots, caches, or generated runtime state.
- Prefer targeted edits to prompts and skills. Avoid broad rewrites unless the behavior contract is changing.
- Keep third-party skill updates as reviewable vendor diffs with a lock-file commit change.
- Keep infra skill stack secrets and generated artifacts in ignored files such as `tf.vars`, `.terraform/`, `.artifacts/`, and Terraform state.
- When adding a new maintained area, update `.gitignore` first so the intended files are trackable and the private files stay ignored.

### Code Repository Worktrees

For local Git repository work, Codex first creates a dedicated branch worktree
under the current invocation directory:
`./.worktrees/codex-<repo>-<timestamp>-<pid>`.

All source reads, edits, tests, and builds happen in that worktree. The primary
worktree is never edited automatically. Existing uncommitted changes remain in
the primary worktree and are not copied into the new worktree. Worktrees are not
removed automatically; their path and branch are reported when the task ends.

## Quick Checks

```bash
git status --short
git diff --check
git check-ignore -v auth.json config.toml version.json
```

If those checks look clean, the deck is probably ready to fly.
