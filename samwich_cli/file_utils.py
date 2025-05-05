from __future__ import annotations

import os
import pathlib
import shutil
import tempfile
from typing import Final

import click

from samwich_cli import model

RECURSIVE_GLOB_PATTERN: Final[str] = "**/*"
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
    if ctx.requirements is None:
        return None
    if not ctx.requirements.exists():
        if ctx.debug:
            click.echo(
                f"No requirements found at {ctx.requirements}. Skipping copy to "
                f"{os.path.relpath(start=ctx.workspace_root, path=target_dir)}"
            )
        return None

    try:
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=False)
            click.echo(
                "Creating directory for requirements.txt: "
                + click.style(
                    os.path.relpath(start=ctx.workspace_root, path=target_dir),
                    fg="magenta",
                )
            )
        req_path = target_dir / "requirements.txt"
        shutil.copy(ctx.requirements, req_path)
    except shutil.SameFileError:
        return None
    else:
        return req_path


def determine_relative_artifact_path(
    ctx: model.Context, artifact_dir: pathlib.Path
) -> pathlib.Path:
    """Get the relative path from the source directory to the artifact directory."""
    return pathlib.Path(os.path.relpath(start=ctx.source_dir, path=artifact_dir))


def restructure_layer(
    ctx: model.Context,
    build_path: pathlib.Path,
    relative_path: pathlib.Path,
    code_uri: pathlib.Path,
) -> None:
    """Copy contents directly to the build path."""
    if ctx.debug:
        source_contents = list(
            os.path.relpath(start=ctx.workspace_root, path=p)
            for p in code_uri.glob(RECURSIVE_GLOB_PATTERN)
        )
        click.secho(f"{INDENT}Source path contents:", fg="cyan")
        click.echo(f"{LIST_INDENT}- " + f"\n{LIST_INDENT}- ".join(source_contents))

    python_path = build_path / "python"
    target_dir = python_path / relative_path
    target_dir.mkdir(parents=True, exist_ok=False)

    for item in code_uri.glob(pattern="*"):
        if (python_path / item.name).exists():
            shutil.move(python_path / item.name, target_dir)
        elif ctx.debug:
            click.echo(
                f"{INDENT}Item {item} does not exist in the build path, skipping."
            )
    _remove_compiled_cache(target_dir)

    if ctx.debug:
        click.echo(
            f"{INDENT}Copied {code_uri} to {target_dir}",
        )


def restructure_lambda_function(
    ctx: model.Context,
    build_path: pathlib.Path,
    relative_path: pathlib.Path,
    code_uri: pathlib.Path,
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
            build_contents = list(
                os.path.relpath(start=ctx.workspace_root, path=p)
                for p in build_path.glob(RECURSIVE_GLOB_PATTERN)
            )
            click.secho(f"{INDENT}Build contents:", fg="cyan")
            click.echo(f"{LIST_INDENT}- " + f"\n{LIST_INDENT}- ".join(build_contents))

        if ctx.debug:
            source_contents = list(
                os.path.relpath(start=ctx.workspace_root, path=p)
                for p in code_uri.glob(RECURSIVE_GLOB_PATTERN)
            )
            click.secho(f"{INDENT}Source path contents:", fg="cyan")
            click.echo(f"{LIST_INDENT}- " + f"\n{LIST_INDENT}- ".join(source_contents))

        for item in code_uri.glob(pattern="*"):
            if (build_path / item.name).exists():
                shutil.move(build_path / item.name, scratch_artifact)
            elif ctx.debug:
                click.echo(
                    f"{INDENT}Item {item} does not exist in the build path, skipping."
                )

        if ctx.debug:
            scratch_contents = list(
                os.path.relpath(start=scratch_temp, path=p)
                for p in scratch_artifact.glob(RECURSIVE_GLOB_PATTERN)
            )
            click.secho(f"{INDENT}Scratch artifact contents:", fg="cyan")
            click.echo(f"{LIST_INDENT}- " + f"\n{LIST_INDENT}- ".join(scratch_contents))

        # Move all contents back
        shutil.move(scratch_temp / relative_path.parts[0], build_path)
        if ctx.debug:
            click.echo(
                f"{INDENT}Copied {os.path.relpath(start=ctx.temp_dir, path=scratch_artifact)} to "
                f"{build_path}",
            )


def _remove_compiled_cache(target_dir: pathlib.Path) -> None:
    """Remove compiled cache files."""
    for req_path in target_dir.glob(RECURSIVE_GLOB_PATTERN):
        if not req_path.exists():
            # It may have been deleted in a previous loop iteration
            continue
        if req_path.is_dir() and req_path.name == "__pycache__":
            shutil.rmtree(req_path, ignore_errors=True)
        elif req_path.is_file() and req_path.name.endswith(".pyc"):
            req_path.unlink(missing_ok=True)
