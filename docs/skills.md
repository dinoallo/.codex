# Skills

[中文](skills.zh-CN.md)

This deck uses skills as the durable behavior layer for Codex. A skill should
teach an agent how to do a specific kind of work, not act as user-facing
documentation for its own sake.

## Layout

```text
skills/<name>/
|-- SKILL.md
`-- agents/
    `-- openai.yaml
```

`SKILL.md` is the agent-facing contract. `agents/openai.yaml` provides UI
metadata. Optional `references/`, `scripts/`, and `assets/` directories are
reserved for larger supporting material.

Do not add README files inside individual skill folders. Put shareable
human-facing explanation in `docs/`, and keep per-skill execution instructions
inside `SKILL.md` or `references/`.

## Skill Groups

The current maintained areas are:

| Area | Skills |
| --- | --- |
| Git workflow | `git-workflow-as-user`, `git-commit-as-user`, `git-push-as-user`, `git-history-as-user`, `git-tag-as-user`, `git-signing-troubleshooter` |
| GitHub CLI | `gh-auth-profile`, `gh-create-pr`, `gh-edit-pr`, `github-actions-debugger` |
| Documentation and repo writing | `write-readmes`, `write-github-actions-workflows`, `write-cluster-image` |
| Skill maintenance | `third-party-skill-vendor` |
| Infrastructure and operations | `infra`, `sealos-install`, `codex-token-usage-dashboard` |
| Lark integrations | `lark-*` skills, when present on the target machine |

Before publishing a fork or public copy, review any private or company-specific
skills and remove material that should not be shared.

## GitHub Auth Profiles

GitHub-facing skills should not rely on one global `gh` account. Some repos
need different users, organization approvals, SSO authorization, or fine-grained
PAT scopes. Use `gh-auth-profile` to route each repository to a private token
provider.

Private profile config lives outside the repository:

```text
$HOME/.codex/private/gh-auth-profiles.toml
```

Use [gh-auth-profiles.example.toml](gh-auth-profiles.example.toml) as the
sanitized template. Do not commit the real profile file, encrypted secret files,
age identities, or plaintext tokens.

Recommended token storage for development servers is SOPS + age:

```bash
mkdir -p "$HOME/.codex/private" "$HOME/.config/sops/age"
chmod 700 "$HOME/.codex/private" "$HOME/.config/sops/age"
age-keygen -o "$HOME/.config/sops/age/keys.txt"
chmod 600 "$HOME/.config/sops/age/keys.txt"
age-keygen -y "$HOME/.config/sops/age/keys.txt"
SOPS_AGE_RECIPIENTS="age1..." sops "$HOME/.codex/private/github-work-fgpat.sops.yaml"
```

Inside the SOPS editor, use this plaintext shape before saving:

```yaml
token: github_pat_xxx
```

After saving, the file on disk should be encrypted by SOPS. The profile command
then extracts only the token field:

```toml
[profiles.work]
host = "github.com"
token_command = "sops decrypt --extract '[\"token\"]' \"$HOME/.codex/private/github-work-fgpat.sops.yaml\""

[rules]
"github.com/your-org/*" = "work"
```

GitHub skills inject that command into a single `gh` process with `GH_TOKEN` or
`GH_ENTERPRISE_TOKEN`. They should not run `gh auth switch`, `gh auth token`, or
store tokens in this repository.

## Maintenance Checks

After editing skills or this documentation, run the smallest relevant checks:

```bash
python3 skills/.system/skill-creator/scripts/quick_validate.py skills/<name>
git diff --check
git status --short
```
