import pathlib

import click

from samwich_cli import controller, model


@click.command()
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
    "-t",
    "--template-file",
    default="template.yaml",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path
    ),
    help="Path to the AWS SAM template file.",
)
@click.option(
    "--sam-args",
    default="",
    help="Arbitrary SAM arguments to pass directly to the sam build command",
)
@click.option(
    "-q",
    "--debug",
    is_flag=True,
    help="Enable debug output.",
)
def main(
    requirements: pathlib.Path,
    template_file: pathlib.Path,
    debug: bool,
    sam_args: str,
) -> None:
    """SAMWICH CLI to prepare the build environment for AWS Lambda functions and layers."""
    controller.run(
        model.Context.build(
            requirements=requirements,
            template_file=template_file,
            sam_args=sam_args,
            debug=debug,
        )
    )
