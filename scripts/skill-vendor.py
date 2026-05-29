#!/usr/bin/env python3
"""Vendor third-party Codex skills from Git repositories.

The manifest is intentionally small and hand-editable. The lock file stores the
resolved commits that were copied into this dotfiles repo.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from dataclasses import dataclass


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "skills" / "third-party.toml"
DEFAULT_LOCK = ROOT / "skills" / "third-party.lock.json"
DEFAULT_CACHE = ROOT / ".tmp" / "skill-vendor" / "repos"


class VendorError(RuntimeError):
    pass


@dataclass(frozen=True)
class Skill:
    name: str
    repo: str
    path: str
    ref: str
    dest: Path

    @property
    def repo_url(self) -> str:
        if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repo):
            return f"https://github.com/{self.repo}.git"
        return self.repo


def run(args: list[str], cwd: Path | None = None, capture: bool = True) -> str:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            check=True,
            text=False,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode(errors="replace").strip()
        stdout = (exc.stdout or b"").decode(errors="replace").strip()
        detail = stderr or stdout or f"exit status {exc.returncode}"
        raise VendorError(f"{' '.join(args)} failed: {detail}") from exc
    if not capture:
        return ""
    return result.stdout.decode().strip()


def load_manifest(path: Path) -> dict[str, Skill]:
    if not path.exists():
        raise VendorError(f"manifest not found: {path}")
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    skills: dict[str, Skill] = {}
    for raw in data.get("skill", []):
        for key in ("name", "repo", "path", "ref"):
            if not raw.get(key):
                raise VendorError(f"skill entry is missing {key!r}: {raw!r}")

        name = raw["name"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise VendorError(f"invalid skill name {name!r}")
        if name in skills:
            raise VendorError(f"duplicate skill name {name!r}")

        dest = normalize_dest(Path(raw.get("dest", f"skills/{name}")))
        skills[name] = Skill(
            name=name,
            repo=raw["repo"],
            path=raw["path"].strip("/"),
            ref=raw["ref"],
            dest=dest,
        )
    return skills


def normalize_dest(path: Path) -> Path:
    dest = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    skills_root = (ROOT / "skills").resolve()
    try:
        relative_dest = dest.relative_to(skills_root)
    except ValueError as exc:
        raise VendorError(f"destination must be under skills/: {path}") from exc
    if dest == skills_root or relative_dest.parts[0] == ".system":
        raise VendorError(f"refusing unsafe destination: {path}")
    return dest


def load_lock(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "skills": {}}
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("version") != 1 or not isinstance(data.get("skills"), dict):
        raise VendorError(f"unsupported lock file format: {path}")
    return data


def write_lock(path: Path, data: dict) -> None:
    ordered = {
        "version": 1,
        "skills": {name: data["skills"][name] for name in sorted(data["skills"])},
    }
    text = json.dumps(ordered, indent=2, sort_keys=False) + "\n"
    path.write_text(text, encoding="utf-8")


def select_skills(skills: dict[str, Skill], names: list[str]) -> list[Skill]:
    if not names:
        return [skills[name] for name in sorted(skills)]
    missing = [name for name in names if name not in skills]
    if missing:
        raise VendorError(f"unknown skill(s): {', '.join(missing)}")
    return [skills[name] for name in names]


def repo_cache_dir(skill: Skill, cache_root: Path) -> Path:
    digest = hashlib.sha256(skill.repo_url.encode()).hexdigest()[:16]
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", skill.repo)
    return cache_root / f"{slug.strip('-')}-{digest}"


def ensure_repo(skill: Skill, cache_root: Path) -> Path:
    cache_root.mkdir(parents=True, exist_ok=True)
    repo_dir = repo_cache_dir(skill, cache_root)
    if not repo_dir.exists():
        run(["git", "clone", "--no-checkout", "--filter=blob:none", skill.repo_url, str(repo_dir)])
    else:
        current_url = run(["git", "config", "--get", "remote.origin.url"], cwd=repo_dir)
        if current_url != skill.repo_url:
            raise VendorError(f"cache remote mismatch for {skill.name}: {repo_dir}")
    run(["git", "fetch", "--tags", "--prune", "origin"], cwd=repo_dir)
    return repo_dir


def resolve_commit(repo_dir: Path, ref: str) -> str:
    candidates = [ref, f"origin/{ref}", f"refs/heads/{ref}", f"refs/tags/{ref}"]
    for candidate in candidates:
        try:
            return run(["git", "rev-parse", "--verify", f"{candidate}^{{commit}}"], cwd=repo_dir)
        except VendorError:
            pass
    run(["git", "fetch", "origin", ref], cwd=repo_dir)
    return run(["git", "rev-parse", "--verify", "FETCH_HEAD^{commit}"], cwd=repo_dir)


def extract_skill(repo_dir: Path, commit: str, source_path: str, output_dir: Path) -> Path:
    try:
        archive = subprocess.run(
            ["git", "archive", "--format=tar", commit, source_path],
            cwd=repo_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode(errors="replace").strip()
        raise VendorError(f"failed to export {source_path} at {commit[:12]}: {stderr}") from exc
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
        safe_extract(tar, output_dir)
    extracted = output_dir / source_path
    if not (extracted / "SKILL.md").exists():
        raise VendorError(f"source path does not contain SKILL.md: {source_path}")
    return extracted


def safe_extract(tar: tarfile.TarFile, dest: Path) -> None:
    dest = dest.resolve()
    for member in tar.getmembers():
        target = (dest / member.name).resolve()
        try:
            target.relative_to(dest)
        except ValueError as exc:
            raise VendorError(f"archive contains unsafe path: {member.name}") from exc
    tar.extractall(dest)


def ensure_clean_dest(dest: Path, force: bool) -> None:
    if force or not dest.exists():
        return
    rel = dest.relative_to(ROOT)
    status = run(["git", "status", "--short", "--", str(rel)], cwd=ROOT)
    if status:
        raise VendorError(f"destination has uncommitted changes; use --force to overwrite: {rel}")


def replace_dest(source: Path, dest: Path, force: bool) -> None:
    ensure_clean_dest(dest, force)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if not dest.is_dir():
            raise VendorError(f"destination exists and is not a directory: {dest.relative_to(ROOT)}")
        shutil.rmtree(dest)
    shutil.copytree(source, dest)


def get_repo(skill: Skill, args: argparse.Namespace, repos: dict[str, Path]) -> Path:
    if skill.repo_url not in repos:
        repos[skill.repo_url] = ensure_repo(skill, args.cache_dir)
    return repos[skill.repo_url]


def update_skills(args: argparse.Namespace) -> None:
    skills = load_manifest(args.manifest)
    lock = load_lock(args.lock)
    selected = select_skills(skills, args.names)
    if not selected:
        print("No third-party skills configured.")
        return

    repos: dict[str, Path] = {}
    for skill in selected:
        repo_dir = get_repo(skill, args, repos)
        commit = resolve_commit(repo_dir, skill.ref)
        with tempfile.TemporaryDirectory(prefix="skill-vendor-") as temp:
            source = extract_skill(repo_dir, commit, skill.path, Path(temp))
            replace_dest(source, skill.dest, args.force)
        lock["skills"][skill.name] = {
            "repo": skill.repo,
            "path": skill.path,
            "ref": skill.ref,
            "commit": commit,
        }
        print(f"updated {skill.name}: {commit[:12]} -> {skill.dest.relative_to(ROOT)}")

    write_lock(args.lock, lock)


def sync_skills(args: argparse.Namespace) -> None:
    skills = load_manifest(args.manifest)
    lock = load_lock(args.lock)
    selected = select_skills(skills, args.names)
    if not selected:
        print("No third-party skills configured.")
        return

    repos: dict[str, Path] = {}
    for skill in selected:
        locked = lock["skills"].get(skill.name)
        if not locked or not locked.get("commit"):
            raise VendorError(f"{skill.name} is not locked; run update first")
        repo_dir = get_repo(skill, args, repos)
        commit = locked["commit"]
        run(["git", "fetch", "origin", commit], cwd=repo_dir)
        with tempfile.TemporaryDirectory(prefix="skill-vendor-") as temp:
            source = extract_skill(repo_dir, commit, skill.path, Path(temp))
            replace_dest(source, skill.dest, args.force)
        print(f"synced {skill.name}: {commit[:12]} -> {skill.dest.relative_to(ROOT)}")


def list_skills(args: argparse.Namespace) -> None:
    skills = load_manifest(args.manifest)
    lock = load_lock(args.lock)
    if not skills:
        print("No third-party skills configured.")
        return
    for skill in select_skills(skills, args.names):
        locked = lock["skills"].get(skill.name, {})
        commit = locked.get("commit", "unlocked")
        print(f"{skill.name}\t{skill.repo}@{skill.ref}\t{commit}\t{skill.dest.relative_to(ROOT)}")


def verify_skills(args: argparse.Namespace) -> None:
    skills = load_manifest(args.manifest)
    lock = load_lock(args.lock)
    selected = select_skills(skills, args.names)
    if not selected:
        print("No third-party skills configured.")
        return

    failed = False
    repos: dict[str, Path] = {}
    for skill in selected:
        locked = lock["skills"].get(skill.name)
        if not locked or not locked.get("commit"):
            print(f"missing lock: {skill.name}", file=sys.stderr)
            failed = True
            continue
        repo_dir = get_repo(skill, args, repos)
        commit = locked["commit"]
        run(["git", "fetch", "origin", commit], cwd=repo_dir)
        with tempfile.TemporaryDirectory(prefix="skill-vendor-") as temp:
            source = extract_skill(repo_dir, commit, skill.path, Path(temp))
            if compare_dirs(source, skill.dest):
                print(f"ok {skill.name}: {commit[:12]}")
            else:
                print(f"mismatch {skill.name}: {skill.dest.relative_to(ROOT)}", file=sys.stderr)
                failed = True
    if failed:
        raise SystemExit(1)


def compare_dirs(left: Path, right: Path) -> bool:
    if not right.exists():
        return False
    left_entries = {entry.name: entry for entry in left.iterdir()}
    right_entries = {entry.name: entry for entry in right.iterdir()}
    if left_entries.keys() != right_entries.keys():
        return False
    for name, left_entry in left_entries.items():
        right_entry = right_entries[name]
        if left_entry.is_dir() != right_entry.is_dir() or left_entry.is_file() != right_entry.is_file():
            return False
        if left_entry.is_dir():
            if not compare_dirs(left_entry, right_entry):
                return False
        elif left_entry.is_file():
            if left_entry.read_bytes() != right_entry.read_bytes():
                return False
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command, help_text in (
        ("list", "show configured third-party skills"),
        ("update", "resolve refs, vendor skills, and update the lock file"),
        ("sync", "vendor skills from locked commits"),
        ("verify", "check vendored files against locked commits"),
    ):
        subparser = subparsers.add_parser(command, help=help_text)
        subparser.add_argument("names", nargs="*", help="skill names; defaults to all")
        if command in {"update", "sync"}:
            subparser.add_argument("--force", action="store_true", help="overwrite dirty destinations")
        subparser.set_defaults(func={
            "list": list_skills,
            "update": update_skills,
            "sync": sync_skills,
            "verify": verify_skills,
        }[command])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.manifest = (ROOT / args.manifest).resolve() if not args.manifest.is_absolute() else args.manifest.resolve()
    args.lock = (ROOT / args.lock).resolve() if not args.lock.is_absolute() else args.lock.resolve()
    args.cache_dir = (ROOT / args.cache_dir).resolve() if not args.cache_dir.is_absolute() else args.cache_dir.resolve()
    try:
        args.func(args)
    except VendorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
