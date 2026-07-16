---
name: git-tag-as-user
description: Create, inspect, and verify Git tags using the repository owner's identity and signing configuration. Use when Codex is asked to create a signed tag, annotate a release tag, verify a tag signature, inspect tag contents, or prepare a tag for later publication without moving or deleting tags unexpectedly.
---

# Git Tag as User

## Overview

Create and verify tags as the repository owner. Prefer signed annotated tags when a release marker is requested, inspect the target commit, and avoid moving or deleting tags without explicit user intent.

## Workflow

1. Confirm the tag intent:
   - Identify the tag name, target commit or ref, and message.
   - Use `HEAD` only when the user did not specify another target and current branch state is clear.
2. Inspect repository state and target:
   - `git status --short --branch`
   - `git log --oneline --decorate -n 10`
   - `git show --stat --oneline --decorate --no-renames <target>`
   - `git tag --list <tag-name>`
3. Inspect signing config without changing it:
   - `git config --show-origin --get user.name`
   - `git config --show-origin --get user.email`
   - `git config --show-origin --get user.signingkey`
   - `git config --show-origin --get gpg.format`
   - `git config --show-origin --get tag.gpgsign`
4. Create the tag:
   - Prefer `git tag -s <tag-name> <target> -m "<message>"`.
   - Use an unsigned or lightweight tag only when the user explicitly asks or the repository convention clearly requires it.
5. Verify the tag:
   - `git verify-tag <tag-name>` for signed tags.
   - `git show --stat --show-signature --no-renames <tag-name>`.
6. Leave publication to `git-push-as-user`:
   - Do not push the tag unless the user asked to publish it.
   - When publishing is requested, push the single tag explicitly: `git push <remote> <tag-name>`.

## Guardrails

- Do not create, move, delete, or overwrite tags without explicit user intent.
- Do not use `git tag -f` unless the user explicitly asked to move an existing tag and understands the rewrite.
- Do not push `--tags` unless the user explicitly asked to publish all local tags.
- If signing fails, stop and use `git-signing-troubleshooter` instead of creating an unsigned fallback tag.

## Final Response

Report the tag name, target commit, signature verification result, whether it was published, and remaining worktree state.
