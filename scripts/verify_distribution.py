from __future__ import annotations

import argparse
import os
import subprocess
import tarfile
import tempfile
import venv
import zipfile
from collections.abc import Sequence
from email.parser import Parser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = PROJECT_ROOT / "scripts" / "smoke_installed.py"


class DistributionVerificationError(RuntimeError):
    """Raised when built distributions do not satisfy the release contract."""


def verify_archive_contents(
    *,
    wheel: Path,
    source_distribution: Path,
    expected_version: str,
) -> None:
    expected_package_files = {
        "base_typed_string/__init__.py",
        "base_typed_string/_base_constrained_typed_string/__init__.py",
        "base_typed_string/_base_constrained_typed_string/_base.py",
        "base_typed_string/_base_constrained_typed_string/_constraints.py",
        "base_typed_string/_version.py",
        "base_typed_string/py.typed",
    }

    with zipfile.ZipFile(wheel) as wheel_archive:
        wheel_names = set(wheel_archive.namelist())
        missing_wheel_files = expected_package_files - wheel_names
        if missing_wheel_files:
            raise DistributionVerificationError(
                f"Wheel is missing files: {sorted(missing_wheel_files)!r}."
            )

        metadata_names = [
            name for name in wheel_names if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_names) != 1:
            raise DistributionVerificationError(
                f"Wheel must contain one METADATA file. Got: {metadata_names!r}."
            )
        metadata = wheel_archive.read(metadata_names[0]).decode("utf-8")
        parsed_metadata = Parser().parsestr(metadata)
        if parsed_metadata.get("Version") != expected_version:
            raise DistributionVerificationError(
                f"Wheel metadata does not declare version {expected_version}."
            )

    source_root = f"base_typed_string-{expected_version}"
    with tarfile.open(source_distribution, mode="r:gz") as source_archive:
        source_names = set(source_archive.getnames())
        expected_source_files = {
            f"{source_root}/CHANGELOG.md",
            f"{source_root}/LICENSE",
            f"{source_root}/README.md",
            f"{source_root}/pyproject.toml",
            f"{source_root}/src/base_typed_string/_version.py",
        }
        missing_source_files = expected_source_files - source_names
        if missing_source_files:
            raise DistributionVerificationError(
                f"Source distribution is missing files: "
                f"{sorted(missing_source_files)!r}."
            )


def install_and_smoke(
    *,
    package_requirement: str,
    expected_version: str,
    with_pydantic: bool,
) -> None:
    with tempfile.TemporaryDirectory(prefix="base-typed-string-smoke-") as directory:
        temporary_directory = Path(directory)
        environment_directory = temporary_directory / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment_directory)
        python = _environment_python(environment_directory)

        _run(
            python,
            "-m",
            "pip",
            "--disable-pip-version-check",
            "install",
            package_requirement,
            cwd=temporary_directory,
        )
        _run(
            python,
            str(SMOKE_SCRIPT),
            "--expected-version",
            expected_version,
            "--with-pydantic" if with_pydantic else "--without-pydantic",
            cwd=temporary_directory,
        )


def _environment_python(environment_directory: Path) -> Path:
    if os.name == "nt":
        return environment_directory / "Scripts" / "python.exe"

    return environment_directory / "bin" / "python"


def _run(*arguments: object, cwd: Path) -> None:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    process = subprocess.run(
        [str(argument) for argument in arguments],
        cwd=cwd,
        env=environment,
        check=False,
    )
    if process.returncode != 0:
        rendered_command = " ".join(str(argument) for argument in arguments)
        raise DistributionVerificationError(
            f"Command failed with exit code {process.returncode}: {rendered_command}"
        )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect, install, and smoke-test wheel and sdist artifacts."
    )
    parser.add_argument("--dist-dir", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parsed_arguments = build_argument_parser().parse_args(arguments)
    distribution_directory = parsed_arguments.dist_dir.resolve()
    expected_version = parsed_arguments.expected_version
    normalized_version = expected_version.replace("-", "_")

    expected_wheel_name = f"base_typed_string-{normalized_version}-py3-none-any.whl"
    expected_source_name = f"base_typed_string-{expected_version}.tar.gz"
    wheel = distribution_directory / expected_wheel_name
    source_distribution = distribution_directory / expected_source_name

    actual_files = {
        path.name for path in distribution_directory.iterdir() if path.is_file()
    }
    expected_files = {expected_wheel_name, expected_source_name}
    if actual_files != expected_files:
        raise DistributionVerificationError(
            f"dist must contain exactly {sorted(expected_files)!r}. "
            f"Got: {sorted(actual_files)!r}."
        )

    verify_archive_contents(
        wheel=wheel,
        source_distribution=source_distribution,
        expected_version=expected_version,
    )
    install_and_smoke(
        package_requirement=str(wheel),
        expected_version=expected_version,
        with_pydantic=False,
    )
    install_and_smoke(
        package_requirement=str(source_distribution),
        expected_version=expected_version,
        with_pydantic=False,
    )
    install_and_smoke(
        package_requirement=(
            f"base-typed-string[pydantic] @ {wheel.resolve().as_uri()}"
        ),
        expected_version=expected_version,
        with_pydantic=True,
    )

    print(f"Distribution verification passed for base-typed-string {expected_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
