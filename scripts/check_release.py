from __future__ import annotations

import argparse
import ast
import re
import subprocess
from collections.abc import Sequence
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = PROJECT_ROOT / "src" / "base_typed_string" / "_version.py"
PYPROJECT_FILE = PROJECT_ROOT / "pyproject.toml"
CHANGELOG_FILE = PROJECT_ROOT / "CHANGELOG.md"
UV_LOCK_FILE = PROJECT_ROOT / "uv.lock"

STABLE_VERSION_PATTERN = re.compile(
    r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$"
)


class ReleaseCheckError(RuntimeError):
    """Raised when a release invariant is not satisfied."""


def read_project_version() -> str:
    module = ast.parse(VERSION_FILE.read_text(encoding="utf-8"), VERSION_FILE.name)

    for statement in module.body:
        if not isinstance(statement, ast.AnnAssign):
            continue
        if not isinstance(statement.target, ast.Name):
            continue
        if statement.target.id != "__version__":
            continue
        if not isinstance(statement.value, ast.Constant):
            break
        if not isinstance(statement.value.value, str):
            break

        return statement.value.value

    raise ReleaseCheckError(
        f"{VERSION_FILE.relative_to(PROJECT_ROOT)} must declare one literal "
        "__version__ value."
    )


def check_source_contract(version: str) -> None:
    if STABLE_VERSION_PATTERN.fullmatch(version) is None:
        raise ReleaseCheckError(
            f"Release version must be a stable X.Y.Z value. Got: {version!r}."
        )

    pyproject = PYPROJECT_FILE.read_text(encoding="utf-8")
    project_section = _toml_section(pyproject, "project")
    setuptools_dynamic_section = _toml_section(pyproject, "tool.setuptools.dynamic")

    if re.search(r"(?m)^version\s*=", project_section) is not None:
        raise ReleaseCheckError(
            "pyproject.toml must not duplicate the version in [project]."
        )
    if (
        re.search(
            r'(?m)^dynamic\s*=\s*\[\s*"version"\s*\]\s*$',
            project_section,
        )
        is None
    ):
        raise ReleaseCheckError(
            'pyproject.toml [project] must declare dynamic = ["version"].'
        )
    if (
        re.search(
            r"(?m)^version\s*=\s*\{\s*attr\s*=\s*"
            r'"base_typed_string\._version\.__version__"\s*\}\s*$',
            setuptools_dynamic_section,
        )
        is None
    ):
        raise ReleaseCheckError(
            "pyproject.toml must read its version from "
            "base_typed_string._version.__version__."
        )

    changelog = CHANGELOG_FILE.read_text(encoding="utf-8")
    changelog_heading = re.compile(
        rf"(?m)^## \[{re.escape(version)}\] - [0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$"
    )
    if changelog_heading.search(changelog) is None:
        raise ReleaseCheckError(
            f"CHANGELOG.md must contain a dated [{version}] release heading."
        )

    uv_lock = UV_LOCK_FILE.read_text(encoding="utf-8")
    locked_project = re.compile(
        r'(?ms)^\[\[package\]\]\s*\nname = "base-typed-string"\s*\n'
        r'source = \{ editable = "\." \}(.*?)(?=^\[\[package\]\]|\Z)'
    )
    locked_project_match = locked_project.search(uv_lock)
    if locked_project_match is None:
        raise ReleaseCheckError(
            "uv.lock must contain the dynamic editable base-typed-string project."
        )
    if re.search(r"(?m)^version\s*=", locked_project_match.group(1)) is not None:
        raise ReleaseCheckError(
            "uv.lock must not duplicate the dynamically sourced project version."
        )


def check_git_release(
    *,
    tag: str,
    require_annotated_tag: bool,
    require_clean: bool,
    require_tag_on_main: bool,
    main_ref: str,
) -> None:
    version = read_project_version()
    expected_tag = f"v{version}"
    if tag != expected_tag:
        raise ReleaseCheckError(
            f"Release tag must be {expected_tag!r} for version {version}. Got: {tag!r}."
        )

    tag_ref = f"refs/tags/{tag}"
    if require_annotated_tag and _git("cat-file", "-t", tag_ref) != "tag":
        raise ReleaseCheckError(f"{tag} must be an annotated Git tag.")

    tag_commit = _git("rev-parse", f"{tag_ref}^{{}}")
    head_commit = _git("rev-parse", "HEAD")
    if tag_commit != head_commit:
        raise ReleaseCheckError(
            f"{tag} resolves to {tag_commit}, but the checked-out commit is "
            f"{head_commit}."
        )

    if require_tag_on_main and not _git_succeeds(
        "merge-base",
        "--is-ancestor",
        tag_commit,
        main_ref,
    ):
        raise ReleaseCheckError(
            f"{tag} commit {tag_commit} must be contained in {main_ref}."
        )

    if require_clean:
        dirty_paths = _git("status", "--porcelain", "--untracked-files=all")
        if dirty_paths:
            raise ReleaseCheckError(
                "Release checkout must be clean before building distributions."
            )


def _toml_section(document: str, section_name: str) -> str:
    section_match = re.search(
        rf"(?ms)^\[{re.escape(section_name)}\]\s*$\n(.*?)(?=^\[|\Z)",
        document,
    )
    if section_match is None:
        raise ReleaseCheckError(f"pyproject.toml is missing [{section_name}].")

    return section_match.group(1)


def _git(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip()
        raise ReleaseCheckError(
            f"git {' '.join(arguments)} failed with exit code "
            f"{process.returncode}: {detail}"
        )

    return process.stdout.strip()


def _git_succeeds(*arguments: str) -> bool:
    process = subprocess.run(
        ["git", *arguments],
        cwd=PROJECT_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return process.returncode == 0


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate source, version, changelog, and Git release invariants."
    )
    parser.add_argument("--tag", help="Release tag, for example v0.2.0.")
    parser.add_argument(
        "--require-annotated-tag",
        action="store_true",
        help="Require the supplied tag to be an annotated Git tag.",
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="Require a clean checkout, including no untracked files.",
    )
    parser.add_argument(
        "--require-tag-on-main",
        action="store_true",
        help="Require the supplied tag commit to be contained in main-ref.",
    )
    parser.add_argument(
        "--main-ref",
        default="refs/remotes/origin/main",
        help="Git ref used by --require-tag-on-main.",
    )
    parser.add_argument(
        "--print-version",
        action="store_true",
        help="Print only the validated project version.",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parsed_arguments = build_argument_parser().parse_args(arguments)
    version = read_project_version()
    check_source_contract(version)

    git_checks_requested = (
        parsed_arguments.require_annotated_tag
        or parsed_arguments.require_clean
        or parsed_arguments.require_tag_on_main
    )
    if git_checks_requested and parsed_arguments.tag is None:
        raise ReleaseCheckError("Git release checks require --tag.")

    if parsed_arguments.tag is not None:
        check_git_release(
            tag=parsed_arguments.tag,
            require_annotated_tag=parsed_arguments.require_annotated_tag,
            require_clean=parsed_arguments.require_clean,
            require_tag_on_main=parsed_arguments.require_tag_on_main,
            main_ref=parsed_arguments.main_ref,
        )

    if parsed_arguments.print_version:
        print(version)
    else:
        print(f"Release contract is valid for base-typed-string {version}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
