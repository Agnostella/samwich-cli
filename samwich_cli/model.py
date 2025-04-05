import os
import pathlib
import platform
import shlex
import tempfile
from typing import Final, NamedTuple

import click

IS_WINDOWS: Final[bool] = platform.system().lower() == "windows"


class Context(NamedTuple):
    """Context for the SAMWICH CLI."""

    workspace_root: pathlib.Path
    requirements: pathlib.Path
    template_file: pathlib.Path
    temp_dir: pathlib.Path
    sam_args: tuple[str, ...]
    source_dir: pathlib.Path
    debug: bool

    @staticmethod
    def build(
        requirements: pathlib.Path,
        template_file: pathlib.Path,
        debug: bool,
        sam_args: str,
        source_dir: pathlib.Path,
    ) -> "Context":
        """Create a context object from the command line arguments."""
        workspace_env = os.environ.get("SAMWICH_WORKSPACE")
        temp_path = os.environ.get("SAMWICH_TEMP", tempfile.mkdtemp())

        workspace_root = (
            pathlib.Path(workspace_env).resolve()
            if workspace_env
            else pathlib.Path.cwd()
        )
        template_file = template_file.resolve()

        if source_dir.is_absolute() or not source_dir.resolve().is_relative_to(
            workspace_root
        ):
            raise click.BadOptionUsage(
                option_name="source_dir",
                message=f"source_dir must be relative and a child of the workspace root: {workspace_root}",
            )

        return Context(
            workspace_root=workspace_root,
            requirements=requirements.resolve(),
            template_file=template_file,
            temp_dir=pathlib.Path(temp_path).resolve(),
            sam_args=Context._parse_sam_args(sam_args, template_file),
            source_dir=workspace_root / source_dir,
            debug=debug,
        )

    @staticmethod
    def _parse_sam_args(sam_args: str, template_file: pathlib.Path) -> tuple[str, ...]:
        sam_args_temp = ["--template-file", str(template_file)]
        if sam_args:
            # Stripping the single quote that can be parsed from several shells
            sam_args_temp.extend(shlex.split(sam_args.strip("'"), posix=not IS_WINDOWS))
        return tuple(sam_args_temp)


class DependenciesState(NamedTuple):
    """State of the dependencies."""

    layer_path: "pathlib.Path | None"
    managed_requirements_paths: list[pathlib.Path]


class ArtifactDetails(NamedTuple):
    """Details of the Layer or Lambda function artifact."""

    codeuri: str
    name: str
