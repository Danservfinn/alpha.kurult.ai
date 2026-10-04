#!/usr/bin/env python3
"""Cron entry. Drafts and raw commits only. No publish, no post, no push, no deploy.

Hermes job b7b7f666b0de runs ~/.hermes/profiles/kublai/scripts/pearl_desk_nightly.py,
which calls this module. The job stays paused until Orda PASS. Unpause is Temujin's
call, with deploy.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NIGHTLY = ROOT / "scripts" / "pearl_nightly.py"
ALLOWED_BRANCH = "kublai/pearl-always-on"
COMMIT_PATHS = ("data/pearl-kpi", "data/pearl-desk", "drafts")
# Dropped from the add. Pulls stay on disk. Commit derived numbers only.
# drafts/test/ is the self-test fixture. It is regenerated on every run and never committed.
EXCLUDED_COMMIT_PATHS = ("data/pearl-kpi/*/coingecko", "data/pearl-kpi/**/coingecko", "drafts/test")


def plan(skip_pull: bool = False) -> list[list[str]]:
    steps = [[sys.executable, str(NIGHTLY), "--self-test"]]
    if not skip_pull:
        steps.append([sys.executable, str(NIGHTLY), "--pull"])
    steps.append([sys.executable, str(NIGHTLY), "--grade"])
    return steps


def branch_name(root: Path) -> str:
    out = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        return ""
    return out.stdout.strip()


def is_coingecko_raw(rel: str) -> bool:
    """True for nightly CoinGecko bodies. The Oct 2 research archive is a different path."""
    norm = rel[2:] if rel.startswith("./") else rel
    return norm.startswith("data/pearl-kpi/") and "/coingecko/" in norm


def is_self_test_draft(rel: str) -> bool:
    """True for the self-test fixture under drafts/test/."""
    norm = rel[2:] if rel.startswith("./") else rel
    return norm == "drafts/test" or norm.startswith("drafts/test/")


def is_excluded(rel: str) -> bool:
    return is_coingecko_raw(rel) or is_self_test_draft(rel)


def files_to_commit(root: Path) -> list[str]:
    """Paths the cron may stage. CoinGecko raws and drafts/test/ are not in this list."""
    out: list[str] = []
    for item in COMMIT_PATHS:
        if item not in ("data/pearl-kpi", "drafts"):
            out.append(item)
            continue
        base = root / item
        if not base.is_dir():
            continue
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            rel = path.relative_to(root).as_posix()
            if is_excluded(rel):
                continue
            out.append(rel)
    return out


def commit_raws(root: Path) -> int:
    """Commit derived desk files and non-CoinGecko raws. Never pushes."""
    branch = branch_name(root)
    if branch != ALLOWED_BRANCH:
        print(f"refusing commit: branch {branch} is not {ALLOWED_BRANCH}", file=sys.stderr)
        return 3
    paths = files_to_commit(root)
    if paths:
        subprocess.run(["git", "add", "--", *paths], cwd=root, check=True)
    staged_names = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    leaked = [line for line in staged_names.stdout.splitlines() if is_excluded(line)]
    if leaked:
        subprocess.run(["git", "reset", "-q", "--", *leaked], cwd=root, check=True)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root)
    if staged.returncode == 0:
        print("NOTHING_TO_COMMIT")
        return 0
    if staged.returncode != 1:
        print(f"git diff --cached failed: {staged.returncode}", file=sys.stderr)
        return staged.returncode
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "Pearl desk nightly: raws, manifest, drafts. No deploy.",
        ],
        cwd=root,
        check=True,
    )
    print("COMMIT_OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--push" in args or "--deploy" in args:
        print("refusing push or deploy", file=sys.stderr)
        return 4
    if "--plan" in args:
        for step in plan(skip_pull="--skip-pull" in args):
            print(" ".join(step))
        print("NO_PUSH")
        return 0
    for step in plan(skip_pull="--skip-pull" in args):
        result = subprocess.run(step, cwd=ROOT)
        if result.returncode != 0:
            return result.returncode
    return commit_raws(ROOT)


if __name__ == "__main__":
    sys.exit(main())
