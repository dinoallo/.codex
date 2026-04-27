---
name: write-readmes
description: Create or revise repository README documentation, including `README.md` and translated sibling files such as `README.zh-CN.md`, `README_ZH.md`, or `README.ja.md`. Use when Codex needs to write a new README, refresh setup or usage sections, restructure project documentation, translate a README, or update existing README files while keeping English and localized variants synchronized. If the user writes in a non-English language, ensure there is also a README version in that language.
---

# Write READMEs

## Overview

Create or revise repository README files with synchronized translations. For new README sets, treat `README.md` as the English source file, then create or update localized sibling files when the user writes in another language or when the repository already maintains them.

## Inspect First

1. Read the target `README.md`, sibling `README*.md` files, and nearby project manifests before drafting.
2. Reuse the repository's existing structure, tone, section order, and translation filename convention.
3. Classify the request before editing:
   - new README set
   - partial section update
   - full rewrite
   - translation sync

## Author the English Source

- Draft or revise the English `README.md` first for new work.
- If an existing repository already uses a non-English `README.md`, preserve that layout unless the user explicitly asks to normalize it.
- Keep commands, file paths, environment variables, identifiers, and code blocks unchanged unless the repository already localizes them.
- Preserve existing links, badges, and anchors unless the change requires updating them.
- Reuse repository terminology instead of inventing new names for features, commands, or modules.

## Protect Privacy

- Do not expose the operator's current working directory, absolute local filesystem paths, username, hostname, email address, or other identifiable local environment details in README content.
- When examples need a path or machine-specific value, replace it with repository-relative paths or neutral placeholders such as `$PROJECT_ROOT`, `$HOME`, `/path/to/project`, `example.com`, or `your-name`.
- Apply the same sanitization rule to translated README variants, screenshots, copied terminal snippets, and generated examples.

## Synchronize Translations

- If the user writes in a non-English language X, ensure there is also a README variant in language X.
- When any README content changes, update all related translated README siblings in the same directory that document the same content, not only the language mentioned in the request.
- Preserve section order, heading hierarchy, examples, tables, notes, and warnings across languages.
- Translate prose and explanatory labels. Do not translate command lines, filenames, config keys, code, or product names unless the repository already does so.
- If the repository has language-switch links or a list of translated files, update those references everywhere they appear.

## Choose Translation Filenames

- Reuse established local naming first, for example `README_ZH.md`, `README.zh-CN.md`, `README_JP.md`, `README_zh.md`, or `README_EN.md`.
- If no convention exists and a new translation is required, prefer `README.<language-tag>.md` with a specific BCP 47 tag when known, for example `README.zh-CN.md`, `README.ja.md`, or `README.fr.md`.
- Do not rename existing translation files just to normalize style unless the user asks.

## Handle Updates Carefully

- For partial README edits, identify the changed English sections and mirror those exact updates into each translated sibling.
- Do not leave new English-only sections behind after updating a translated README set.
- If the current README files disagree, reconcile the English source first, then propagate the resolved structure and facts.
- If a safe translation update cannot be inferred from the repository or user request, state that limitation in the final response instead of inventing project details.

## Verify Before Finishing

- Confirm that every touched README variant reflects the same feature set and section order.
- Check that copied commands, code blocks, tables, and links still match after translation.
- Report which README files were updated and whether any existing translations were intentionally left untouched.
