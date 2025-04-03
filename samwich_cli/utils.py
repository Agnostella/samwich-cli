import argparse
import contextlib
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import Final

from samcli.commands._utils import constants
from samcli.commands.build import build_context

from samwich_cli import model

logger = logging.getLogger(__name__)


def copy_requirements(ctx: model.Context, target_dir: pathlib.Path) -> None:
    """Copy requirements.txt to the target directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(shutil.SameFileError):
        shutil.copy(ctx.requirements_path, target_dir / "requirements.txt")


def determine_relative_lambda_path(
    ctx: model.Context, artifact_dir: str
) -> pathlib.Path:
    """Get the relative path from the workspace directory to the artifact directory."""
    return pathlib.Path(os.path.relpath(artifact_dir, ctx.workspace_root))


def copy_contents(
    ctx: model.Context, source_path: pathlib.Path, relative_path: pathlib.Path
) -> None:
    """Copy contents using a scratch directory approach."""
    with tempfile.TemporaryDirectory(dir=ctx.temp_dir) as scratch_dir:
        scratch_dir = ctx.temp_dir / "scratch"

        # Copy with parent directories
        scratch_artifact = scratch_dir / relative_path
        scratch_artifact.mkdir(parents=True, exist_ok=True)

        logger.debug("Copying contents from %s to %s", source_path, scratch_artifact)

        for item in source_path.glob("*"):
            if item.is_dir():
                # Copy the directory with its contents
                shutil.copytree(item, scratch_artifact / item.name, dirs_exist_ok=True)
            else:
                # Copy the file
                shutil.copy(item, scratch_artifact / item.name)

        logger.debug("Source path contents: %s", list(source_path.glob("*")))
        logger.debug("Scratch artifact contents: %s", list(scratch_artifact.glob("*")))

        # Remove original
        shutil.rmtree(source_path)

        # Copy all contents back
        for item in scratch_dir.glob("*"):
            if item.is_dir():
                shutil.copytree(item, source_path / item.name, dirs_exist_ok=True)
            else:
                shutil.copy(item, source_path / item.name)


def get_build_resources(ctx: model.Context) -> dict[str, list[model.ArtifactDetails]]:
    """Get the functions and layers from SAM build context."""
    with build_context.BuildContext(
        template_file=str(ctx.template_file),
        resource_identifier=None,
        base_dir=None,
        build_dir=constants.DEFAULT_BUILD_DIR,
        cache_dir=constants.DEFAULT_CACHE_DIR,
        cached=False,
        parallel=False,
        mode=None,
    ) as build_ctx:
        resources = build_ctx.get_resources_to_build()

    return {
        "layers": [
            model.ArtifactDetails(codeuri=_.codeuri, name=_.name)
            for _ in resources.layers
            if _.codeuri and _.name
        ],
        "functions": [
            model.ArtifactDetails(codeuri=_.codeuri, name=_.name)
            for _ in resources.functions
            if _.codeuri and _.name
        ],
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Prepare the build environment for AWS Lambda functions and layers."
    )
    parser.add_argument(
        "--requirements-path",
        required=False,
        default=pathlib.Path.cwd() / "requirements.txt",
        action="store",
        type=pathlib.Path,
        help="Path to the requirements.txt file for the Python package.",
    )
    parser.add_argument(
        "--template-file",
        required=False,
        default=pathlib.Path.cwd() / "template.yaml",
        action="store",
        type=pathlib.Path,
        help="Path to the AWS SAM template file.",
    )
    parser.add_argument(
        "--debug",
        required=False,
        default=False,
        action="store_true",
        help="Enable debug logging.",
    )

    return parser.parse_args()


def configure_logging(debug: bool) -> None:
    """Configure logging for the script."""
    logging.basicConfig(
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger.setLevel(logging.DEBUG if debug else logging.INFO)


def create_context(args: argparse.Namespace) -> model.Context:
    """Create a context object from the command line arguments."""
    repo_root: Final[str] = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()
    return model.Context(
        workspace_root=pathlib.Path(
            os.environ.get("SAMWICH_WORKSPACE", repo_root)
        ).resolve(),
        requirements_path=args.requirements_path.resolve(),
        template_file=args.template_file.resolve(),
        temp_dir=pathlib.Path(
            os.environ.get("SAMWICH_TEMP", tempfile.mkdtemp())
        ).resolve(),
    )
