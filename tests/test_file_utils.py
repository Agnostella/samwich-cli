import pathlib

from samwich_cli import file_utils


class TestCopyRequirements:
    def test_given_non_existent_path(self, context_factory) -> None:
        """Test that copy_requirements does not copy if no requirements are found."""
        ctx = context_factory()

        result = file_utils.copy_requirements(ctx, pathlib.Path.cwd())

        assert result is None

    def test_given_same_file(self, context_factory) -> None:
        """Test that copy_requirements does not copy if the source and destination are the same."""
        ctx = context_factory()

        ctx.requirements.touch()

        result = file_utils.copy_requirements(ctx, ctx.workspace_root)

        assert result is None

    def test_given_copy_performed(self, context_factory) -> None:
        """Test that copy_requirements copies the requirements file to the target directory."""
        ctx = context_factory()

        ctx.requirements.touch()

        result = file_utils.copy_requirements(ctx, ctx.temp_dir)

        assert result is not None
        assert result == ctx.temp_dir / "requirements.txt"
        assert result.exists()
        assert result.is_file()
        assert result.stat().st_size == 0
