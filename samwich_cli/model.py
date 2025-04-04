import pathlib
from typing import NamedTuple


class Context(NamedTuple):
    """Context for the SAMWICH CLI."""

    workspace_root: pathlib.Path
    requirements_path: pathlib.Path
    template_file: pathlib.Path
    temp_dir: pathlib.Path


class ArtifactDetails(NamedTuple):
    """Details of the Layer or Lambda function artifact."""

    codeuri: str
    name: str
