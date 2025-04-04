import pathlib

import click

from samwich_cli import controller


@click.command()
@click.option(
    "--requirements",
    default="requirements.txt",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, path_type=pathlib.Path
    ),
    help="Path to the requirements.txt file for the project.",
)
@click.option(
    "--template-file",
    default="template.yaml",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path
    ),
    help="Path to the AWS SAM template file.",
)
@click.option("--debug", is_flag=True, help="Enable debug output.")
def main(requirements, template_file, debug):
    """SAMWICH CLI to prepare the build environment for AWS Lambda functions and layers."""
    controller.run(requirements, template_file, debug)
