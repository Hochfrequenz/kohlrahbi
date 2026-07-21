from typer.testing import CliRunner

from kohlrahbi import app

runner = CliRunner()


def test_version_flag() -> None:
    """
    Test the version flag.
    """
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output
