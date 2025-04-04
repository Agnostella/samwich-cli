import argparse
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
from samcli.lib.providers import provider

from samwich_cli import model

logger = logging.getLogger(__name__)


def copy_requirements(
    ctx: model.Context, target_dir: pathlib.Path
) -> pathlib.Path | None:
    """
    Copy requirements.txt to the target directory.

    Args:
        ctx (model.Context): The context object containing the workspace and requirements path.
        target_dir (pathlib.Path): The target directory where the requirements.txt file will be copied.
    Returns:
        pathlib.Path | None: The path to the destination requirements.txt file, or None if no requirements were copied.
    """
    if not ctx.requirements.exists():
        logger.debug(
            "No requirements found at %s. Skipping copy to %s",
            str(ctx.requirements),
            os.path.relpath(start=ctx.workspace_root, path=target_dir),
        )
        return None

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        req_path = target_dir / "requirements.txt"
        shutil.copy(ctx.requirements, req_path)
    except shutil.SameFileError:
        return None
    else:
        return req_path


def determine_relative_lambda_path(
    ctx: model.Context, artifact_dir: str
) -> pathlib.Path:
    """Get the relative path from the workspace directory to the artifact directory."""
    return pathlib.Path(os.path.relpath(start=ctx.workspace_root, path=artifact_dir))


def copy_contents(
    ctx: model.Context, source_path: pathlib.Path, relative_path: pathlib.Path
) -> None:
    """Copy contents using a scratch directory approach."""
    scratch_dir = ctx.temp_dir / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch_dir) as scratch_temp:
        scratch_temp = pathlib.Path(scratch_temp)

        glob_pattern = "**/*"

        # Copy with parent directories
        scratch_artifact = scratch_temp / relative_path
        scratch_artifact.mkdir(parents=True, exist_ok=True)

        logger.debug(
            "    Source path contents: %s",
            list(
                os.path.relpath(start=ctx.workspace_root, path=p)
                for p in source_path.glob(glob_pattern)
            ),
        )

        logger.debug(
            "    Copying contents from %s to %s",
            os.path.relpath(start=ctx.workspace_root, path=source_path),
            scratch_artifact,
        )

        for item in source_path.glob("*"):
            if item.is_dir():
                shutil.copytree(item, scratch_artifact / item.name, dirs_exist_ok=False)
            else:
                shutil.copy(item, scratch_artifact / item.name)
        logger.debug(
            "    Scratch artifact contents: %s",
            list(
                os.path.relpath(start=scratch_temp, path=p)
                for p in scratch_artifact.glob(glob_pattern)
            ),
        )

        # Remove original
        shutil.rmtree(source_path)

        # Copy all contents back
        for item in scratch_temp.glob("*"):
            logger.debug(
                "    Copying %s to %s",
                os.path.relpath(start=scratch_temp, path=item),
                os.path.relpath(start=ctx.workspace_root, path=source_path / item.name),
            )
            if item.is_dir():
                shutil.copytree(item, source_path / item.name, dirs_exist_ok=False)
            else:
                shutil.copy(item, source_path / item.name)

        logger.debug(
            "    Source path contents after copy: %s",
            list(
                os.path.relpath(start=ctx.workspace_root, path=p)
                for p in source_path.glob(glob_pattern)
            ),
        )


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

    def _is_python_resource(
        resource: provider.LayerVersion | provider.Function,
    ) -> bool:
        if isinstance(resource, provider.LayerVersion):
            return any(
                runtime.startswith("python")
                for runtime in resource.compatible_runtimes or []
            )
        if isinstance(resource, provider.Function):
            return (resource.runtime or "").startswith("python")
        return False

    return {
        "layers": [
            model.ArtifactDetails(codeuri=r.codeuri, name=r.name)
            for r in resources.layers
            if r.codeuri and r.name and _is_python_resource(r)
        ],
        "functions": [
            model.ArtifactDetails(codeuri=r.codeuri, name=r.name)
            for r in resources.functions
            if r.codeuri and r.name and _is_python_resource(r)
        ],
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Prepare the build environment for AWS Lambda functions and layers."
    )
    parser.add_argument(
        "--requirements",
        required=False,
        default=pathlib.Path("requirements.txt"),
        action="store",
        type=pathlib.Path,
        help="Path to the requirements.txt file for the project. If you use a tool like Poetry or uv, export the requirements to a file before using samwich-cli.",
    )
    parser.add_argument(
        "--template-file",
        required=False,
        default=pathlib.Path("template.yaml"),
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
    log_handler = logging.StreamHandler(sys.stderr)
    log_formatter = logging.Formatter("%(levelname)s: %(message)s")
    log_handler.setFormatter(log_formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)

    cli_logger = logging.getLogger("samwich_cli")
    cli_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    cli_logger.addHandler(log_handler)
    cli_logger.propagate = False


def create_context(args: argparse.Namespace) -> model.Context:
    """Create a context object from the command line arguments."""
    repo_root: Final[str] = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()
    workspace_root = pathlib.Path(
        os.environ.get("SAMWICH_WORKSPACE", repo_root)
    ).resolve()
    return model.Context(
        workspace_root=workspace_root,
        requirements=pathlib.Path(
            os.path.relpath(start=workspace_root, path=args.requirements)
        ).resolve(),
        template_file=pathlib.Path(
            os.path.relpath(start=workspace_root, path=args.template_file)
        ).resolve(),
        temp_dir=pathlib.Path(
            os.environ.get("SAMWICH_TEMP", tempfile.mkdtemp())
        ).resolve(),
    )
