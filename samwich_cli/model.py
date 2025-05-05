from __future__ import annotations

import os
import pathlib
import platform
import shlex
import subprocess
import tempfile
from typing import TYPE_CHECKING, Final, NamedTuple

from samwich_cli import sam_utils

if TYPE_CHECKING:
    from typing import Self

import click

IS_WINDOWS: Final[bool] = platform.system().lower() == "windows"


class Context(NamedTuple):
    """Context for the SAMWICH CLI."""

    debug: bool
    requirements: pathlib.Path | None
    sam_args: tuple[str, ...]
    source_dir: pathlib.Path
    temp_dir: pathlib.Path
    template_file: pathlib.Path
    workspace_root: pathlib.Path
    sam_build_dir: pathlib.Path

    @staticmethod
    def build(
        debug: bool,
        requirements: pathlib.Path | None,
        sam_args: str,
        source_dir: pathlib.Path | None,
        template_file: pathlib.Path,
        workspace_root: pathlib.Path | None,
    ) -> Self:
        """Create a context object from the command line arguments."""
        temp_path = os.environ.get("SAMWICH_TEMP", tempfile.mkdtemp())

        if not workspace_root:
            try:
                workspace_root = pathlib.Path(
                    subprocess.check_output(
                        ["git", "rev-parse", "--show-toplevel"],
                        text=True,
                        stderr=subprocess.DEVNULL,
                    ).strip()
                )
            except Exception:
                workspace_root = pathlib.Path.cwd()

        resolved_workspace = workspace_root.resolve()
        template_file = template_file.resolve()

        if source_dir and (
            source_dir.is_absolute()
            or not source_dir.resolve().is_relative_to(resolved_workspace)
        ):
            raise click.BadOptionUsage(
                option_name="source_dir",
                message=f"source_dir must be relative and a child of the workspace root: {resolved_workspace}",
            )

        return Context(
            workspace_root=resolved_workspace,
            requirements=requirements.resolve() if requirements else None,
            template_file=template_file,
            temp_dir=pathlib.Path(temp_path).resolve(),
            sam_args=Context._parse_sam_args(sam_args, template_file),
            source_dir=resolved_workspace / source_dir
            if source_dir
            else resolved_workspace,
            sam_build_dir=pathlib.Path.cwd() / sam_utils.constants.DEFAULT_BUILD_DIR,
            debug=debug,
        )

    @staticmethod
    def _parse_sam_args(sam_args: str, template_file: pathlib.Path) -> tuple[str, ...]:
        sam_args_temp = [
            "--template-file",
            os.path.relpath(start=pathlib.Path.cwd(), path=template_file),
        ]
        if sam_args:
            # Stripping the single quote that can be parsed from several shells
            sam_args_temp.extend(shlex.split(sam_args.strip("'"), posix=not IS_WINDOWS))
        return tuple(sam_args_temp)


class DependenciesState(NamedTuple):
    """State of the dependencies."""

    layer_path: pathlib.Path | None
    managed_requirements_paths: list[pathlib.Path]


class ArtifactDetails(NamedTuple):
    """Details of the Layer or Lambda function artifact."""

    codeuri: str
    full_path: str
    name: str
