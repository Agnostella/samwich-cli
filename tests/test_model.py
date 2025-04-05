import pathlib

from samwich_cli import model


class TestContext:
    def test_parse_sam_args(self) -> None:
        """Test that the SAM arguments are parsed correctly."""
        template_file = pathlib.Path("template.yaml")
        sam_args = "--use-container --region us-east-1 --parallel"
        expected_args = (
            "--template-file",
            str(template_file),
            *sam_args.split(" "),
        )

        result = model.Context._parse_sam_args(sam_args, template_file)

        assert result == expected_args
