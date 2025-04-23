from __future__ import annotations

import pathlib

import click

from samwich_cli import controller, model

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "auto_envvar_prefix": "SAMWICH",
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option()
@click.option(
    "-t",
    "--template-file",
    default="template.yaml",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path
    ),
    help="Path to the AWS SAM template file.",
)
@click.option(
    "-r",
    "--requirements",
    default="requirements.txt",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, path_type=pathlib.Path
    ),
    help="Path to the requirements.txt file for the project.",
)
@click.option(
    "--workspace-root",
    default=None,
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path
    ),
    help="Path to the workspace root directory. The default is discovered using git or the current working directory.",
)
@click.option(
    "--source-dir",
    default=None,
    type=click.Path(
        exists=False, file_okay=False, dir_okay=True, path_type=pathlib.Path
    ),
    help="Path to the source directory for the code. When restructuring, only the child paths of this directory will be included.",
)
@click.option(
    "--sam-args",
    default="",
    help="Arbitrary SAM arguments to pass directly to the sam build command",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug output.",
)
def cli(
    debug: bool,
    requirements: pathlib.Path | None,
    sam_args: str,
    source_dir: pathlib.Path | None,
    template_file: pathlib.Path,
    workspace_root: pathlib.Path | None,
) -> None:
    """SAMWICH CLI to prepare the build environment for AWS Lambda functions and layers."""
    controller.run(
        model.Context.build(
            debug=debug,
            requirements=requirements,
            sam_args=sam_args,
            source_dir=source_dir,
            template_file=template_file,
            workspace_root=workspace_root,
        )
    )
