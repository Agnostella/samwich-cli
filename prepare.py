import argparse
import os
import pathlib
import subprocess
import sys
import tempfile
import shutil
from typing import Final

from samcli.commands._utils import constants
from samcli.commands.build import build_context

args = argparse.ArgumentParser(
    description="Prepare the build environment for AWS Lambda functions and layers."
)
args.add_argument(
    "--requirements-path",
    required=True,
    action="store",
    type=pathlib.Path,
    help="Path to the requirements.txt file for the Python package.",
)
args.add_argument(
    "--template-file",
    required=True,
    action="store",
    type=pathlib.Path,
    help="Path to the AWS SAM template file.",
)

args = args.parse_args()

REPO_ROOT: Final[str] = subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True
).strip()
WORKSPACE_ROOT: Final[pathlib.Path] = pathlib.Path(
    os.environ.get("GITHUB_WORKSPACE", REPO_ROOT)
)

TEMP_DIR: Final[pathlib.Path] = pathlib.Path(
    os.environ.get("TEMP_DIR", tempfile.mkdtemp())
)
BUILD_DIR: Final[pathlib.Path] = TEMP_DIR / "build"

REQUIREMENTS_PATH: Final[pathlib.Path] = args.requirements_path
TEMPLATE_FILE: Final[pathlib.Path] = args.template_file


def copy_requirements(target_dir: pathlib.Path) -> None:
    """Copy requirements.txt to the target directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REQUIREMENTS_PATH, target_dir / "requirements.txt")


def determine_relative_lambda_path(lambda_dir: str) -> str:
    """Get the relative path from the workspace directory to the lambda directory."""
    return os.path.relpath(lambda_dir, WORKSPACE_ROOT)


def copy_contents(relative_path: str) -> None:
    """Copy contents using a scratch directory approach."""
    scratch_dir = TEMP_DIR / "scratch"
    scratch_dir.mkdir(exist_ok=True)

    # Copy with parent directories
    source_path = WORKSPACE_ROOT / relative_path
    target_path = scratch_dir / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_path, target_path, dirs_exist_ok=True)

    # Remove original and recreate directory
    shutil.rmtree(source_path)
    source_path.mkdir(parents=True, exist_ok=True)

    # Copy all contents back
    for item in target_path.glob("*"):
        if item.is_dir():
            shutil.copytree(item, source_path / item.name, dirs_exist_ok=True)
        else:
            shutil.copy(item, source_path / item.name)

    # Clean up
    shutil.rmtree(scratch_dir)


def get_build_resources():
    """Get the functions and layers from SAM build context."""
    with build_context.BuildContext(
        template_file=str(TEMPLATE_FILE),
        resource_identifier=None,
        base_dir=None,
        build_dir=constants.DEFAULT_BUILD_DIR,
        cache_dir=constants.DEFAULT_CACHE_DIR,
        cached=False,
        parallel=False,
        mode=None,
    ) as ctx:
        resources = ctx.get_resources_to_build()

    return {
        "layers": [f.codeuri for f in resources.layers if f.codeuri is not None],
        "functions": [f.codeuri for f in resources.functions if f.codeuri is not None],
    }


def main():
    build_resources = get_build_resources()
    layers = build_resources["layers"]
    functions = build_resources["functions"]

    # Process functions
    for fn in functions:
        relative_path = determine_relative_lambda_path(fn)
        copy_contents(relative_path)

    # Handle layers based on count
    if len(layers) == 1:
        layer_path = pathlib.Path(layers[0])
        if layer_path.exists():
            relative_path = determine_relative_lambda_path(str(layer_path))
            copy_contents(relative_path)
        else:
            layer_path.mkdir(parents=True, exist_ok=True)

        copy_requirements(layer_path)
    elif len(layers) == 0:
        for fn in functions:
            copy_requirements(pathlib.Path(fn))
    else:
        print(
            "::warning:: More than one layer found, skipping poetry export",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
