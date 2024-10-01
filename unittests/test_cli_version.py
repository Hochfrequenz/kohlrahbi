import click.testing

from kohlrahbi import cli


def test_version_flag():
    """
    Test the version flag.
    """
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output
