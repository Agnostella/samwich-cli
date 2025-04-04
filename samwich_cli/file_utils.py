import os
import pathlib
import shutil
import tempfile
from typing import Final

import click

from samwich_cli import model

GLOB_PATTERN: Final[str] = "**/*"
INDENT: Final[str] = " " * 4
LIST_INDENT: Final[str] = " " * 6


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
        if ctx.debug:
            click.echo(
                f"No requirements found at {str(ctx.requirements)}. Skipping copy to "
                f"{os.path.relpath(start=ctx.workspace_root, path=target_dir)}"
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

        # Copy with parent directories
        scratch_artifact = scratch_temp / relative_path
        scratch_artifact.mkdir(parents=True, exist_ok=True)

        if ctx.debug:
            source_contents = list(
                os.path.relpath(start=ctx.workspace_root, path=p)
                for p in source_path.glob(GLOB_PATTERN)
            )
            click.secho(f"{INDENT}Source path contents:", fg="cyan")
            click.echo(f"{LIST_INDENT}- " + f"\n{LIST_INDENT}- ".join(source_contents))

        for item in source_path.glob("*"):
            if item.is_dir():
                shutil.copytree(item, scratch_artifact / item.name, dirs_exist_ok=False)
            else:
                shutil.copy(item, scratch_artifact / item.name)

        if ctx.debug:
            scratch_contents = list(
                os.path.relpath(start=scratch_temp, path=p)
                for p in scratch_artifact.glob(GLOB_PATTERN)
            )
            click.secho(f"{INDENT}Scratch artifact contents:", fg="cyan")
            click.echo(f"{LIST_INDENT}- " + f"\n{LIST_INDENT}- ".join(scratch_contents))

        # Remove original
        shutil.rmtree(source_path)

        # Copy all contents back
        for item in scratch_temp.glob("*"):
            if ctx.debug:
                click.echo(
                    f"{INDENT}Copying {os.path.relpath(start=scratch_temp, path=item)} to "
                    f"{os.path.relpath(start=ctx.workspace_root, path=source_path / item.name)}",
                )
            if item.is_dir():
                shutil.copytree(item, source_path / item.name, dirs_exist_ok=False)
            else:
                shutil.copy(item, source_path / item.name)

        if ctx.debug:
            contents_after_copy = list(
                os.path.relpath(start=ctx.workspace_root, path=p)
                for p in source_path.glob(GLOB_PATTERN)
            )
            click.secho(f"{INDENT}Source path contents after copy:", fg="cyan")
            click.echo(
                f"{LIST_INDENT}- " + f"\n{LIST_INDENT}- ".join(contents_after_copy)
            )
