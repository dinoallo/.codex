#!/usr/bin/env python3
"""Create detached Git worktrees for commit/branch or GitHub PR review."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence


class ReviewSetupError(RuntimeError):
    pass


def run(
    cmd: Sequence[str],
    *,
    cwd: Path | None = None,
    dry_run: bool = False,
    capture: bool = True,
) -> str:
    shown = " ".join(shell_quote(part) for part in cmd)
    if cwd is not None:
        shown = f"(cd {shell_quote(str(cwd))} && {shown})"
    print(f"+ {shown}", file=sys.stderr)
    if dry_run:
        return ""

    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            check=True,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
        )
    except FileNotFoundError as exc:
        raise ReviewSetupError(f"Missing command: {cmd[0]}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout or f"exit code {exc.returncode}"
        raise ReviewSetupError(f"Command failed: {shown}\n{detail}") from exc

    return (completed.stdout or "").strip()


def shell_quote(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_@%+=:,./-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def require_git_root(repo_path: str, *, dry_run: bool) -> Path:
    repo = Path(repo_path).expanduser().resolve()
    if not repo.exists():
        raise ReviewSetupError(
            f"Local repository path does not exist: {repo}\n"
            "Ask the user for an existing repo path or explicit approval to clone."
        )

    root = run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"])
    if not root:
        raise ReviewSetupError(f"Not a Git repository: {repo}")
    return Path(root).resolve()


def infer_repo_path(repo_path: str | None, *, dry_run: bool) -> Path:
    if repo_path:
        return require_git_root(repo_path, dry_run=dry_run)

    try:
        return require_git_root(os.getcwd(), dry_run=dry_run)
    except ReviewSetupError as exc:
        raise ReviewSetupError(
            "No local repository path was provided and the current directory is not a Git repository.\n"
            "Ask the user for a local repo path or explicit approval to clone before continuing."
        ) from exc


def slugify(value: str, *, default: str = "review") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    slug = re.sub(r"-{2,}", "-", slug).strip(".-")
    return (slug or default)[:80]


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 100):
        candidate = path.with_name(f"{path.name}-{index}")
        if not candidate.exists():
            return candidate
    raise ReviewSetupError(f"Could not find an unused worktree path near {path}")


def ensure_worktrees_excluded(repo: Path, *, dry_run: bool) -> None:
    git_dir = run(["git", "-C", str(repo), "rev-parse", "--git-common-dir"])

    git_common_dir = Path(git_dir)
    if not git_common_dir.is_absolute():
        git_common_dir = (repo / git_common_dir).resolve()
    exclude_path = git_common_dir / "info" / "exclude"
    if dry_run:
        print(f"+ ensure .worktrees/ is listed in {exclude_path}", file=sys.stderr)
        return

    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    if ".worktrees/" not in {line.strip() for line in existing.splitlines()}:
        print(f"+ append .worktrees/ to {exclude_path}", file=sys.stderr)
        with exclude_path.open("a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write(".worktrees/\n")


def resolve_ref(repo: Path, ref: str, *, dry_run: bool) -> str:
    return run(["git", "-C", str(repo), "rev-parse", "--verify", f"{ref}^{{commit}}"])


def parse_pr(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"#?\d+", value):
        return value.lstrip("#")
    match = re.search(r"/pull/(\d+)(?:\D|$)", value)
    if match:
        return match.group(1)
    raise ReviewSetupError(f"Could not parse a PR number from: {value}")


def infer_github_repo(remote_url: str) -> str:
    patterns = [
        r"^git@([^:]+):([^/]+)/(.+?)(?:\.git)?$",
        r"^https?://([^/]+)/([^/]+)/(.+?)(?:\.git)?$",
        r"^ssh://git@([^/]+)/([^/]+)/(.+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, remote_url)
        if not match:
            continue
        host, owner, repo = match.groups()
        repo = repo.removesuffix(".git")
        if host == "github.com":
            return f"{owner}/{repo}"
        return f"{host}/{owner}/{repo}"
    raise ReviewSetupError(
        f"Could not infer OWNER/REPO from remote URL: {remote_url}\n"
        "Pass --github-repo explicitly."
    )


def remote_url(repo: Path, remote: str, *, dry_run: bool) -> str:
    return run(["git", "-C", str(repo), "remote", "get-url", remote])


def default_worktree_base(repo: Path) -> Path:
    return repo / ".worktrees"


def add_worktree(repo: Path, target: str, path: Path, *, dry_run: bool) -> None:
    run(["git", "-C", str(repo), "worktree", "add", "--detach", str(path), target], dry_run=dry_run, capture=False)


def setup_ref(args: argparse.Namespace) -> dict[str, str]:
    repo = infer_repo_path(args.repo_path, dry_run=args.dry_run)
    sha = resolve_ref(repo, args.ref, dry_run=args.dry_run)
    short_sha = sha[:12] if sha != "DRYRUN" else "dryrun"
    worktree_path = (
        Path(args.worktree_path).expanduser().resolve()
        if args.worktree_path
        else unique_path(default_worktree_base(repo) / f"review-{slugify(args.ref)}-{short_sha}")
    )

    ensure_worktrees_excluded(repo, dry_run=args.dry_run)
    add_worktree(repo, sha, worktree_path, dry_run=args.dry_run)
    return {
        "mode": "ref",
        "repo": str(repo),
        "ref": args.ref,
        "commit": sha,
        "worktree_path": str(worktree_path),
    }


def gh_pr_view(repo_slug: str, pr_number: str, *, dry_run: bool) -> dict[str, object]:
    fields = [
        "number",
        "url",
        "title",
        "headRefName",
        "headRefOid",
        "baseRefName",
        "isCrossRepository",
    ]
    if dry_run:
        run(["gh", "pr", "view", pr_number, "-R", repo_slug, "--json", ",".join(fields)], dry_run=True)
        return {
            "number": int(pr_number),
            "url": f"https://github.com/{repo_slug}/pull/{pr_number}",
            "title": "DRY RUN",
            "headRefName": "dry-run-head",
            "headRefOid": "DRYRUN",
            "baseRefName": "dry-run-base",
            "isCrossRepository": False,
        }

    output = run(["gh", "pr", "view", pr_number, "-R", repo_slug, "--json", ",".join(fields)])
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise ReviewSetupError(f"gh returned invalid JSON for PR {pr_number}") from exc


def setup_pr(args: argparse.Namespace) -> dict[str, object]:
    repo = infer_repo_path(args.repo_path, dry_run=args.dry_run)
    pr_number = parse_pr(args.pr)
    selected_remote = args.remote or "origin"
    selected_repo = args.github_repo
    if not selected_repo:
        url = remote_url(repo, selected_remote, dry_run=args.dry_run)
        selected_repo = infer_github_repo(url)

    pr = gh_pr_view(selected_repo, pr_number, dry_run=args.dry_run)
    local_ref = f"refs/review-worktree/pr-{pr_number}"
    run(
        [
            "git",
            "-C",
            str(repo),
            "fetch",
            selected_remote,
            f"refs/pull/{pr_number}/head:{local_ref}",
        ],
        dry_run=args.dry_run,
        capture=False,
    )

    head_ref = str(pr.get("headRefName") or f"pr-{pr_number}")
    head_oid = str(pr.get("headRefOid") or "")
    short_sha = head_oid[:12] if head_oid and head_oid != "DRYRUN" else "dryrun"
    worktree_path = (
        Path(args.worktree_path).expanduser().resolve()
        if args.worktree_path
        else unique_path(default_worktree_base(repo) / f"pr-{pr_number}-{slugify(head_ref)}-{short_sha}")
    )

    ensure_worktrees_excluded(repo, dry_run=args.dry_run)
    add_worktree(repo, local_ref, worktree_path, dry_run=args.dry_run)
    return {
        "mode": "pr",
        "repo": str(repo),
        "github_repo": selected_repo,
        "remote": selected_remote,
        "pr": pr,
        "local_ref": local_ref,
        "worktree_path": str(worktree_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create detached Git worktrees for commit/branch or GitHub PR review."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    ref_parser = subparsers.add_parser("ref", help="Create a worktree for a commit, branch, tag, or ref.")
    add_common_args(ref_parser)
    ref_parser.add_argument("--ref", required=True, help="Commit, branch, tag, or ref to review.")
    ref_parser.set_defaults(func=setup_ref)

    pr_parser = subparsers.add_parser("pr", help="Create a worktree for a GitHub pull request.")
    add_common_args(pr_parser)
    pr_parser.add_argument("--pr", required=True, help="PR number or GitHub PR URL.")
    pr_parser.add_argument("--github-repo", help="GitHub repository as OWNER/REPO or HOST/OWNER/REPO.")
    pr_parser.add_argument("--remote", default="origin", help="Local git remote to fetch PR refs from.")
    pr_parser.set_defaults(func=setup_pr)

    return parser


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-path", help="Existing local repository path. Defaults to current Git repo.")
    parser.add_argument("--worktree-path", help="Explicit output worktree path.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without making changes.")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        result = args.func(args)
    except ReviewSetupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
