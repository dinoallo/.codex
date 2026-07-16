---
name: git-signing-troubleshooter
description: Diagnose Git commit or tag signing failures without changing user identity or signing configuration. Use when Codex sees GPG or SSH signing errors, unclear signature verification output, failed `git commit -S`, failed signed tags, failed `git verify-commit`, failed `git verify-tag`, or requests to inspect signing setup.
---

# Git Signing Troubleshooter

## Overview

Diagnose signing failures while preserving the user's configured identity, key material, and trust settings. Inspect effective configuration and local error signals; do not weaken signing or create keys unless the user explicitly asks.

## Workflow

1. Preserve the failing command and error output for the final response.
2. Inspect effective signing configuration without changing it:
   - `git config --show-origin --get user.name`
   - `git config --show-origin --get user.email`
   - `git config --show-origin --get commit.gpgsign`
   - `git config --show-origin --get tag.gpgsign`
   - `git config --show-origin --get user.signingkey`
   - `git config --show-origin --get gpg.format`
   - `git config --show-origin --get gpg.program`
   - `git config --show-origin --get gpg.ssh.allowedSignersFile`
3. Inspect the relevant object when verification failed:
   - `git log -1 --show-signature --format=fuller` for commit verification.
   - `git verify-commit HEAD` for the current commit.
   - `git show --show-signature --no-renames <tag>` and `git verify-tag <tag>` for tag verification.
4. Diagnose by signing format:
   - For GPG signing, check whether the configured key exists, pinentry is available, and the user may need to unlock the key.
   - For SSH signing, check whether the signing key and allowed signers file are configured and readable.
   - Treat trust database or allowed signers warnings as diagnostic details, not automatic reasons to rewrite commits.
5. Recommend the smallest next step:
   - Ask the user to unlock or authorize the key when interactive key access is required.
   - Suggest the exact config or environment item that appears missing, but do not set it automatically.
   - Retry the original signing command only after the blocker is addressed.

## Guardrails

- Do not disable `commit.gpgsign` or `tag.gpgsign` to make a Git operation pass.
- Do not change global or repository Git config unless the user explicitly asks.
- Do not generate, import, delete, trust, or publish keys unless the user explicitly asks.
- Do not paste private keys, secret key material, or token-like values in responses.
- Do not amend or rewrite commits from this skill unless the user explicitly asks after signing is fixed.

## Final Response

Report the failing command, likely cause, relevant non-secret config origins, recommended next action, and whether any verification command succeeded.
