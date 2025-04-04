import os
import pathlib
import subprocess
import tempfile
from typing import Final

import click

from samwich_cli import file_utils, model, sam_utils


def run(requirements: pathlib.Path, template_file: pathlib.Path, debug: bool) -> None:
    """Run the SAMWICH CLI."""
    ctx = _create_context(requirements, template_file, debug)

    if debug:
        click.echo(f"Context: {ctx._asdict()}")

    build_resources = sam_utils.get_build_resources(ctx.template_file)
    layers = build_resources["layers"]
    functions = build_resources["functions"]

    dependencies_state = _prepare_requirements(ctx, layers, functions)

    if ctx.debug:
        click.echo()
        click.echo()
    click.secho("Begin SAM build", fg="magenta")
    click.secho("=" * 25, fg="magenta")
    click.echo()
    sam_utils.sam_build(ctx.template_file)
    click.echo()
    click.secho("=" * 25, fg="magenta")
    click.secho("End SAM build", fg="magenta")
    click.echo()
    click.echo()

    _update_layer_structure(ctx, layers, dependencies_state.layer_path)
    _update_function_structure(ctx, functions)

    for req_path in dependencies_state.managed_requirements_paths:
        if ctx.debug:
            click.echo(
                f"Removing {os.path.relpath(start=ctx.workspace_root, path=req_path)}"
            )
        req_path.unlink(missing_ok=True)


def _create_context(
    requirements: pathlib.Path, template_file: pathlib.Path, debug: bool
) -> model.Context:
    """Create a context object from the command line arguments."""
    repo_root: Final[str] = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()
    workspace_root = pathlib.Path(
        os.environ.get("SAMWICH_WORKSPACE", repo_root)
    ).resolve()
    return model.Context(
        workspace_root=workspace_root,
        requirements=requirements.resolve(),
        template_file=template_file.resolve(),
        temp_dir=pathlib.Path(
            os.environ.get("SAMWICH_TEMP", tempfile.mkdtemp())
        ).resolve(),
        debug=debug,
    )


def _prepare_requirements(
    ctx: model.Context,
    layers: list[model.ArtifactDetails],
    functions: list[model.ArtifactDetails],
) -> model.DependenciesState:
    """
    Prepare the requirements for the build.

    Args:
        ctx: The context for the build.
        layers: The layers to be built.
        functions: The functions to be built.

    Returns:
        DependenciesState: The dependencies state containing the layer path and managed requirements paths.
    """
    layer_path = None

    copy_candidate_dirs = []
    if len(layers) == 1:
        layer_path = pathlib.Path(layers[0].codeuri)
        copy_candidate_dirs = [layer_path]
    elif len(layers) == 0:
        copy_candidate_dirs = [pathlib.Path(fn.codeuri) for fn in functions]
    else:
        copy_candidate_dirs = []
        click.secho(
            "More than one layer found, skipping requirements copy. This may be supported in the future.",
            fg="yellow",
        )

    managed_reqs_paths = []
    for candidate in copy_candidate_dirs:
        copied_req_path = file_utils.copy_requirements(ctx, candidate)
        if copied_req_path is None:
            continue

        if ctx.debug:
            click.echo(
                f"Copied requirements.txt to {str(os.path.relpath(start=ctx.workspace_root, path=copied_req_path))}"
            )
        managed_reqs_paths.append(copied_req_path)

    return model.DependenciesState(
        layer_path=layer_path, managed_requirements_paths=managed_reqs_paths
    )


def _update_layer_structure(
    ctx: model.Context,
    layers: list[model.ArtifactDetails],
    layer_path: pathlib.Path | None,
) -> None:
    """Update the layer folder structure."""
    if layer_path and list(_.name for _ in layer_path.glob("*")) != [
        "requirements.txt"
    ]:
        click.echo(
            "Updating layer folder structure: "
            + click.style(layer_path.name, fg="magenta")
        )
        relative_path = file_utils.determine_relative_lambda_path(ctx, str(layer_path))
        if ctx.debug:
            click.echo(f"Relative path for layer {layer_path}: {relative_path}")
        file_utils.copy_contents(
            ctx, sam_utils.SAM_BUILD_DIR / layers[0].name, relative_path
        )


def _update_function_structure(
    ctx: model.Context, functions: list[model.ArtifactDetails]
) -> None:
    """Update the function folder structure."""
    for fn in functions:
        click.echo(
            "Updating lambda folder structure: " + click.style(fn.name, fg="magenta")
        )
        relative_path = file_utils.determine_relative_lambda_path(
            ctx, artifact_dir=fn.codeuri
        )
        if ctx.debug:
            click.echo(
                f"{file_utils.INDENT}Relative path: {os.path.relpath(start=ctx.workspace_root, path=relative_path)}"
            )
        file_utils.copy_contents(ctx, sam_utils.SAM_BUILD_DIR / fn.name, relative_path)
        click.echo("")
