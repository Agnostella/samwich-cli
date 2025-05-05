import os
import pathlib
import shutil
from click.testing import CliRunner

from samwich_cli.main import cli


def test_should_match_snapshot_given_lambda_and_layer_build(snapshot):
    # Given
    runner = CliRunner()
    example_app = pathlib.Path.cwd() / "docs" / "examples" / "lambda-and-layer"
    with runner.isolated_filesystem():
        for example in example_app.glob("*"):
            if example.is_file():
                shutil.copy(example, example.name)
            else:
                shutil.copytree(example, example.name)

        # When
        result = runner.invoke(
            cli,
            [
                "--template-file",
                "template.yaml",
                "--requirements",
                "requirements.txt",
                "--debug",
            ],
        )
        build_dir = pathlib.Path.cwd() / ".aws-sam"
        built_artifacts = set()
        for root, dirs, files in os.walk(build_dir):
            # Get relative path for this directory
            rel_path = os.path.relpath(root, build_dir)

            # Add all files from this directory
            for file in files:
                file_rel_path = (
                    os.path.join(rel_path, file) if rel_path != "." else file
                )
                built_artifacts.add(file_rel_path)

    # Then
    assert result.exception is None, result.exc_info
    assert result.exit_code == 0, result.output

    assert built_artifacts == snapshot
