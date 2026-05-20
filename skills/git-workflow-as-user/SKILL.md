---
name: git-workflow-as-user
description: Perform Git workflows using the repository owner's identity and signing configuration. Use when Codex is asked to inspect status, stage files, commit, write commit messages, amend, tag, rebase, merge, push, open or update PR-ready history, verify signatures, troubleshoot signed commits, or otherwise operate Git on behalf of the user while preserving their author, committer, signing key, remotes, branches, and unrelated work.
---

# Git Workflow as User

## Overview

Operate Git as the user, not as the assistant. Preserve the user's local configuration, stage only the intended changes, use their existing signing setup for commits and tags, and verify the result before reporting success. Prefer the fast path for routine commits and reserve the strict path for risky or complex Git work.

## Choose Workflow Depth

Use the fast commit path when the request is a small, clear commit and the intended files are obvious.

Use the strict workflow path when any of these apply:

- The operation is amend, rebase, merge, tag, push, force-push, branch deletion, reset, clean, or other history/remote work.
- The worktree is confusing, has overlapping unrelated changes, requires partial staging, or includes generated files/lockfiles whose inclusion is uncertain.
- The staged changes include sensitive-looking filenames or values from the privacy and secret check.
- Identity or signing config is missing, inconsistent, or unclear for a required signed commit.
- A Git command failed, signing output is unclear, or the user asks for a careful/full verification pass.

## Git Metadata Writes

Commands that update `.git` metadata, such as `git add`, `git commit`, `git tag`, `git rebase`, and `git merge`, may require elevated permissions in sandboxed environments. If a Git metadata write fails with an index, lockfile, permission, or read-only filesystem error, rerun it with the required approval instead of changing the workflow. In the same repository/session, use the already-known required permission path directly for later metadata writes.

Do not use elevated permissions to bypass safety rules. Destructive or history-changing commands still require explicit user intent.

## User Approval Prompts

Some Git operations may pause until the user approves a sandbox escalation. When asking for approval, state the specific purpose and keep any suggested persistent approval narrowly scoped.

For repeated routine Git metadata writes, suggest a prefix rule only when it matches the operation being requested:

- `["git", "add"]` for staging selected paths.
- `["git", "commit"]` for creating commits with the user's configured identity and signing setup.
- `["git", "tag"]` only when the user has asked to create tags.

Tell the user that the approval UI may offer a persistent/default approval option for the suggested prefix. Choosing that option can avoid repeated prompts for the same class of Git command in later steps.

Persistent approval only removes the sandbox prompt. It does not replace the need for explicit user intent before remote, destructive, or history-changing actions such as push, force-push, reset, clean, branch deletion, rebase, amend, or tag movement. Do not request broad prefixes such as `["git"]`, and do not suggest persistent approval for destructive commands.

## Fast Commit Path

For routine commits:

1. Read the nearest `AGENTS.md`, repository README, and project manifest only when the commit depends on repository conventions that are not already clear.
2. Inspect the branch and intended changes:
   - `git status --short --branch`
   - `git diff --stat -- <paths>` for targeted commits, or `git diff --stat` when the whole dirty worktree is intended.
   - `git diff -- <paths>` for content that has not already been reviewed.
   - `git diff --cached --stat` only when staged changes already exist.
3. If identity and signing were not already confirmed in the current task, inspect the minimal effective config without changing it:
   - `git config --show-origin --get user.name`
   - `git config --show-origin --get user.email`
   - `git config --show-origin --get commit.gpgsign`
   - `git config --show-origin --get user.signingkey`
4. Stage only intended paths with `git add -- <paths>`.
5. Review the staged result:
   - `git diff --cached --stat`
   - `git diff --cached --name-status`
   - `git diff --cached -- <paths>` when staged content was not already reviewed or partial staging was used.
6. Run the privacy and secret check on the staged changes.
7. Commit with the chosen subject/body.
8. Verify the result:
   - `git log -1 --show-signature --format=fuller`
   - `git show --stat --oneline --decorate --no-renames HEAD`
   - Run `git verify-commit HEAD` only when the signature output is missing or unclear, or when using the strict path.

## Strict Workflow Path

For complex or high-risk Git work:

1. Read the nearest `AGENTS.md`, repository README, and project manifest when the Git operation depends on repo conventions.
2. Inspect the repository state before editing or committing:
   - `git status --short --branch`
   - `git diff --stat`
   - `git diff`
   - `git diff --cached`
3. Identify unrelated dirty files and leave them untouched unless the user explicitly includes them.
4. Inspect local identity and signing configuration without changing it:
   - `git config --show-origin --get user.name`
   - `git config --show-origin --get user.email`
   - `git config --show-origin --get commit.gpgsign`
   - `git config --show-origin --get user.signingkey`
   - `git config --show-origin --get gpg.format`
   - `git config --show-origin --get tag.gpgsign`
5. Treat missing identity or signing configuration as a blocker for signed user commits. Ask the user how to proceed instead of inventing identity values or generating keys.
6. Run the privacy and secret check on the staged changes. Prefer repository-configured scanners when available.
7. After committing, verify with both:
   - `git log -1 --show-signature --format=fuller`
   - `git verify-commit HEAD`
8. Inspect the final commit contents:
   - `git show --stat --oneline --decorate --no-renames HEAD`
   - Use `git show --name-status --format=fuller HEAD` when author, committer, or file list matters.

## Identity Rules

- Use the repository's effective `user.name`, `user.email`, `user.signingkey`, `gpg.format`, and signing-related hooks exactly as configured.
- Prefer repository-local config over global config when both exist because that is what Git will use.
- Do not set or rewrite `user.name`, `user.email`, `user.signingkey`, `commit.gpgsign`, `gpg.program`, `SSH_AUTH_SOCK`, `GPG_TTY`, or global Git config unless the user explicitly asks.
- Do not add `--author`, `--committer`, or environment variables such as `GIT_AUTHOR_*` or `GIT_COMMITTER_*` unless the user explicitly requests a different author.
- Do not use assistant, bot, noreply, placeholder, or guessed identity values.

## Staging

- Prefer pathspec-specific staging over broad staging. Use `git add -- <paths>` for complete files and `git add -p -- <paths>` when only part of a file belongs in the commit.
- Review the staged result before committing, using the fast or strict path above.
- Keep generated files, lockfiles, and docs in the same commit only when they are part of the requested change or repository workflow.
- Never stage unrelated user changes as a convenience.

## Privacy and Secret Check

Before committing, check only staged changes unless the user asks for a wider audit. Treat likely leaks as commit blockers until removed, redacted, or explicitly confirmed safe by the user.

Fast path:

1. Inspect staged filenames with `git diff --cached --name-status`.
2. Review staged added lines with `git diff --cached --unified=0 --no-color`.
3. Look for sensitive filenames and paths:
   - `.env`, `.env.*`, `.npmrc`, `.pypirc`, `.netrc`, kubeconfig files
   - `id_rsa`, `id_ed25519`, `*.pem`, `*.key`, `*.p12`, `*.pfx`
   - filenames containing `secret`, `credential`, `token`, `password`, or `private`
4. Look for sensitive values in added lines:
   - private keys, certificates, OAuth/JWT/Bearer tokens, API keys, access tokens, refresh tokens
   - assignments to names containing `password`, `passwd`, `pwd`, `secret`, `token`, `api_key`, `apikey`, `auth`, `credential`, or `private_key`
   - real personal data or local environment details: home directories, usernames, hostnames, email addresses, machine-specific absolute paths, production URLs, account IDs

Strict path:

- Use repository-configured scanners when present, without installing new tools or downloading rules unless the user approves. Examples include `pre-commit run --files <staged paths>`, `gitleaks protect --staged`, `detect-secrets-hook --baseline .secrets.baseline`, or equivalent local project scripts.
- If no scanner exists, do the fast path check plus a full review of `git diff --cached --name-only` and `git diff --cached --unified=0 --no-color`.
- Do not paste suspected secret values in final responses. Refer to the file and line or the variable/key name, and say the value was redacted.

False positives:

- Placeholders such as `example.com`, `your-token`, `REDACTED`, `<TOKEN>`, `changeme`, test fixtures, and documented fake keys may be committed when the surrounding context makes them clearly non-sensitive.
- If a value looks real or environment-specific, stop before committing and ask the user whether to redact, ignore, or intentionally commit it.

## Commit Message Convention

Use the repository's documented commit message convention when one exists. If no stricter local convention exists, use Conventional Commits in English.

Preferred subject format:

```text
<type>(<scope>): <summary>
```

Scope is optional when it does not add clarity:

```text
<type>: <summary>
```

Rules:

- `type` must be lowercase ASCII. Use `feat`, `fix`, `docs`, not `Feat`, `Fix`, or `DOCS`.
- Keep the summary in imperative mood, concise, and without a trailing period. Aim for 72 characters or fewer.
- Commit only one coherent change per commit. Do not bundle unrelated refactors, formatting churn, and behavior changes together unless the user explicitly asks for one combined commit.
- Add a body when the reason, tradeoff, migration, or risk is not obvious from the diff.
- Use a breaking-change marker when applicable: `<type>(<scope>)!: <summary>` and include `BREAKING CHANGE:` in the body if needed.

Preferred types:

- `feat`: new user-facing or developer-facing capability
- `fix`: bug fix or regression fix
- `refactor`: internal restructuring without behavior change
- `docs`: documentation-only change
- `test`: test-only change
- `perf`: measurable performance improvement
- `build`: build, packaging, or dependency pipeline change
- `ci`: CI workflow or automation change
- `chore`: maintenance work that does not fit the categories above

Example subjects:

- `feat(auth): add token refresh on expiry`
- `fix(api): handle empty pagination cursor`
- `docs(readme): clarify local setup steps`
- `refactor(cli): split flag parsing from command execution`

## Signed Commits

Use the user's existing signing setup. The normal path is:

```bash
git commit -S -m "type(scope): summary"
```

When repository config already has `commit.gpgsign=true`, `git commit -m ...` should still sign, but prefer `-S` when the user specifically requested a signed commit.

Before committing:

1. Confirm the staged diff is exactly the intended content.
2. Run the privacy and secret check above.
3. Choose the subject and body using the commit message convention above.
4. Avoid creating a commit if verification or tests that should gate the change have not run, unless the user asks to commit anyway and the final response calls out the skipped checks.

After committing:

1. Verify the signature and inspect commit contents using the fast or strict path above.
2. Report the commit hash, subject, signature verification status, and tests/checks run.

## Signed Tags

Use signed tags only when the user asks for a tag or release marker:

```bash
git tag -s <tag-name> -m "<tag message>"
git verify-tag <tag-name>
```

Do not create, move, or delete tags without explicit user intent.

## Amend, Rebase, Merge, and History Changes

- Treat amend, rebase, squash, reset, force-push, and tag movement as history changes that require explicit user intent.
- Before amending or rebasing, inspect `git status --short --branch` and the relevant recent history with `git log --oneline --decorate -n 10`.
- Preserve signing when amending: `git commit --amend -S`.
- Preserve signing during interactive or automated rebases when the user asked for signed rewritten commits, for example with `git rebase --exec 'git commit --amend --no-edit -S'` only after confirming the workflow is appropriate.
- Do not run destructive commands such as `git reset --hard`, `git checkout -- <path>`, `git clean`, branch deletion, or force-push unless the user explicitly asked for that exact class of operation.

## Pushes and Remotes

- Do not push unless the user asked to push, publish, update a PR branch, or perform an equivalent remote operation.
- Before pushing, inspect `git remote -v`, `git status --short --branch`, and the upstream relationship.
- Use plain `git push` only when the current branch tracks the intended upstream. Otherwise ask or use the explicit remote and branch requested by the user.
- For rewritten history, prefer `git push --force-with-lease` over `--force`, and only when the user explicitly asked for a rewrite that requires it.
- Never push to production, deployment, release, or protected branches unless the user explicitly requested that target.

## Troubleshooting Signing

If signing fails:

1. Preserve the failed command output for the final response.
2. Check effective configuration and available signing format:
   - `git config --show-origin --get gpg.format`
   - `git config --show-origin --get user.signingkey`
   - `git config --show-origin --get gpg.program`
3. For GPG signing, check whether `GPG_TTY` or pinentry may be needed, but do not set shell startup files or global config without user approval.
4. For SSH signing, check whether the configured key and `gpg.ssh.allowedSignersFile` are present, but do not create or modify key files without user approval.
5. Ask the user to unlock, configure, or authorize their signing key when interaction outside the sandbox is required.

## Final Response

Include:

- Branch and whether the worktree is clean or what remains dirty.
- Commit or tag hash/name and subject when created.
- Signature verification result.
- Verification commands run, or checks that were intentionally skipped.
- Any remote push result, only if a push was requested.
