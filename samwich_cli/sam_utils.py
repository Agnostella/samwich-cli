from __future__ import annotations

import sys

import click
from samcli.cli.main import cli
from samcli.commands._utils import constants
from samcli.commands.build import build_context
from samcli.lib.providers import provider

from samwich_cli import model


def sam_build(sam_args: tuple[str, ...], debug: bool) -> None:
    """Run the SAM build command."""

    original_args = sys.argv.copy()

    args = ["sam", "build", *sam_args]
    if debug:
        click.echo()
        click.echo()
    click.secho("Begin SAM build", fg="magenta")
    click.secho("=" * 25, fg="magenta")
    click.echo()
    click.echo(f"+ {' '.join(args)}")
    click.echo()
    try:
        sys.argv = args
        cli(prog_name="sam")
    except SystemExit as e:
        if e.code != 0:
            sys.exit(e.code)
    finally:
        sys.argv = original_args
        click.echo()
        click.secho("=" * 25, fg="magenta")
        click.secho("End SAM build", fg="magenta")
        click.echo()
        click.echo()


def get_build_resources(
    ctx: model.Context,
) -> dict[str, list[model.ArtifactDetails]]:
    """Get the functions and layers from SAM build context."""
    with build_context.BuildContext(
        template_file=str(ctx.template_file),
        resource_identifier=None,
        base_dir=None,
        build_dir=str(ctx.sam_build_dir),
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
            model.ArtifactDetails(codeuri=r.codeuri, full_path=r.full_path, name=r.name)
            for r in resources.layers
            if isinstance(r.codeuri, str) and _is_python_resource(r)
        ],
        "functions": [
            model.ArtifactDetails(codeuri=r.codeuri, full_path=r.full_path, name=r.name)
            for r in resources.functions
            if isinstance(r.codeuri, str) and _is_python_resource(r)
        ],
    }
