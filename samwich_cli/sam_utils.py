import pathlib
import subprocess
from typing import Final

from samcli.commands._utils import constants
from samcli.commands.build import build_context
from samcli.lib.providers import provider

from samwich_cli import model

SAM_BUILD_DIR: Final[pathlib.Path] = pathlib.Path.cwd() / constants.DEFAULT_BUILD_DIR


def sam_build(template_file: pathlib.Path) -> None:
    """Run the SAM build command."""
    subprocess.check_call(["sam", "build", "--template-file", str(template_file)])


def get_build_resources(
    template_file: pathlib.Path,
) -> dict[str, list[model.ArtifactDetails]]:
    """Get the functions and layers from SAM build context."""
    with build_context.BuildContext(
        template_file=str(template_file),
        resource_identifier=None,
        base_dir=None,
        build_dir=str(SAM_BUILD_DIR),
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
            model.ArtifactDetails(codeuri=r.codeuri, name=r.name)
            for r in resources.layers
            if r.codeuri and r.name and _is_python_resource(r)
        ],
        "functions": [
            model.ArtifactDetails(codeuri=r.codeuri, name=r.name)
            for r in resources.functions
            if r.codeuri and r.name and _is_python_resource(r)
        ],
    }
