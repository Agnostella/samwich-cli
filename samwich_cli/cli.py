import logging
import pathlib
import subprocess
from typing import Final

from samcli.commands._utils import constants

from samwich_cli import model, utils

logger = logging.getLogger(__name__)

SAM_BUILD_DIR: Final[pathlib.Path] = pathlib.Path.cwd() / constants.DEFAULT_BUILD_DIR


def _prepare_requirements(
    ctx: model.Context,
    layers: list[model.ArtifactDetails],
    functions: list[model.ArtifactDetails],
) -> pathlib.Path | None:
    layer_path = None
    if len(layers) == 1:
        layer_path = pathlib.Path(layers[0].codeuri)
        utils.copy_requirements(ctx, layer_path)
    elif len(layers) == 0:
        for fn in functions:
            utils.copy_requirements(ctx, pathlib.Path(fn.codeuri))
    else:
        logger.warning("More than one layer found, skipping poetry export")

    return layer_path


def _sam_build(ctx: model.Context) -> None:
    """Run the SAM build command."""
    logger.debug("Running SAM build")
    subprocess.check_call(["sam", "build", "--template-file", str(ctx.template_file)])


def _update_layer_structure(
    ctx: model.Context,
    layers: list[model.ArtifactDetails],
    layer_path: pathlib.Path | None,
) -> None:
    """Update the layer folder structure."""
    if layer_path and list(_.name for _ in layer_path.glob("*")) != [
        "requirements.txt"
    ]:
        logger.info("Updating layer folder structure")
        relative_path = utils.determine_relative_lambda_path(ctx, str(layer_path))
        logger.debug(
            "Relative path for layer %s: %s",
            layer_path,
            relative_path,
        )
        utils.copy_contents(ctx, SAM_BUILD_DIR / layers[0].name, relative_path)


def _update_function_structure(
    ctx: model.Context, functions: list[model.ArtifactDetails]
) -> None:
    """Update the function folder structure."""
    for fn in functions:
        logger.info("Updating folder structure for function %s", fn.name)
        relative_path = utils.determine_relative_lambda_path(
            ctx, artifact_dir=fn.codeuri
        )
        logger.debug(
            "Relative path for function %s: %s",
            fn.name,
            relative_path,
        )
        utils.copy_contents(ctx, SAM_BUILD_DIR / fn.name, relative_path)


def main():
    """Main function to run the CLI."""
    args = utils.parse_args()
    utils.configure_logging(args.debug)
    ctx = utils.create_context(args)

    logger.debug("Context: %s", ctx._asdict())

    build_resources = utils.get_build_resources(ctx)
    layers = build_resources["layers"]
    functions = build_resources["functions"]

    layer_path = _prepare_requirements(ctx, layers, functions)

    _sam_build(ctx)

    _update_layer_structure(ctx, layers, layer_path)

    # Process functions
    _update_function_structure(ctx, functions)
