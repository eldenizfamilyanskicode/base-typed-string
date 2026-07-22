from __future__ import annotations

import pytest
import scripts.check_release as release_checks
from scripts.check_release import (
    ReleaseCheckError,
    check_git_release,
    check_source_contract,
    read_project_version,
)


def test_source_release_contract_is_self_consistent() -> None:
    version = read_project_version()

    check_source_contract(version)

    assert version == "0.2.0"


def test_release_tag_must_exactly_match_the_source_version() -> None:
    with pytest.raises(
        ReleaseCheckError,
        match=r"Release tag must be 'v0\.2\.0'.*Got: 'v0\.2\.1'",
    ):
        check_git_release(
            tag="v0.2.1",
            require_annotated_tag=False,
            require_clean=False,
            require_tag_on_main=False,
            main_ref="refs/remotes/origin/main",
        )


def test_git_release_contract_accepts_matching_annotated_main_tag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_commit = "a" * 40

    def fake_git(*arguments: str) -> str:
        responses: dict[tuple[str, ...], str] = {
            ("cat-file", "-t", "refs/tags/v0.2.0"): "tag",
            ("rev-parse", "refs/tags/v0.2.0^{}"): release_commit,
            ("rev-parse", "HEAD"): release_commit,
            ("status", "--porcelain", "--untracked-files=all"): "",
        }
        return responses[arguments]

    def fake_git_succeeds(*arguments: str) -> bool:
        return arguments == (
            "merge-base",
            "--is-ancestor",
            release_commit,
            "refs/remotes/origin/main",
        )

    monkeypatch.setattr(release_checks, "_git", fake_git)
    monkeypatch.setattr(release_checks, "_git_succeeds", fake_git_succeeds)

    check_git_release(
        tag="v0.2.0",
        require_annotated_tag=True,
        require_clean=True,
        require_tag_on_main=True,
        main_ref="refs/remotes/origin/main",
    )


def test_git_release_contract_rejects_lightweight_tag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_git(*arguments: str) -> str:
        del arguments
        return "commit"

    monkeypatch.setattr(release_checks, "_git", fake_git)

    with pytest.raises(
        ReleaseCheckError,
        match=r"v0\.2\.0 must be an annotated Git tag",
    ):
        check_git_release(
            tag="v0.2.0",
            require_annotated_tag=True,
            require_clean=False,
            require_tag_on_main=False,
            main_ref="refs/remotes/origin/main",
        )
