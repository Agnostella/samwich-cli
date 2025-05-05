import pathlib
import pytest


@pytest.fixture()
def context_factory(tmp_path):
    """Fixture to create a context object for testing."""

    def _create_context(
        sam_args: tuple = tuple([]), source_dir="src", debug: bool = True
    ):
        from samwich_cli import model

        workspace_root = tmp_path / "workspace"
        temp_dir = tmp_path / "temp"

        workspace_root.mkdir(parents=True, exist_ok=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        return model.Context(
            workspace_root=workspace_root,
            requirements=workspace_root / "requirements.txt",
            template_file=workspace_root / "template.yaml",
            temp_dir=temp_dir,
            sam_args=sam_args,
            source_dir=workspace_root / source_dir,
            sam_build_dir=pathlib.Path.cwd() / "build",
            debug=debug,
        )

    return _create_context
