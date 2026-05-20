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
| `prompts/` | Custom prompt files, currently focused on the OPSX/OpenSpec change workflow. |
| `skills/` | User-maintained skills that extend agent behavior for Git, README writing, and GitHub Actions. |
| `.gitignore` | Allowlist-style ignore rules that keep runtime state and private config out of commits. |

## Console Map

```text
.
|-- AGENTS.md
|-- README.md
|-- README.zh-CN.md
|-- prompts/
|   `-- opsx-*.md
|-- skills/
|   |-- git-workflow-as-user/
|   |-- write-github-actions-workflows/
|   `-- write-readmes/
`-- .gitignore
```

## Operating Notes

- Treat this repo as personal dotfiles with a sharper edge: small changes can alter future agent behavior.
- Keep project artifacts in English by default; add localized companion docs when useful.
- Do not commit `auth.json`, `config.toml`, session logs, memories, shell snapshots, caches, or generated runtime state.
- Prefer targeted edits to prompts and skills. Avoid broad rewrites unless the behavior contract is changing.
- When adding a new maintained area, update `.gitignore` first so the intended files are trackable and the private files stay ignored.

## Quick Checks

```bash
git status --short
git diff --check
git check-ignore -v auth.json config.toml version.json
```

If those checks look clean, the deck is probably ready to fly.
