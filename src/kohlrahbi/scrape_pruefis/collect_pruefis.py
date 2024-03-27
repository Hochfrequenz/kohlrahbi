from datetime import date
from pathlib import Path

import click
import docx  # type:ignore[import]
import tomlkit
from docx.table import Table  # type:ignore[import]
from maus.edifact import EdifactFormatVersion

from kohlrahbi.docxfilefinder import DocxFileFinder
from kohlrahbi.logger import logger
from kohlrahbi.read_functions import does_the_table_contain_pruefidentifikatoren, get_all_paragraphs_and_tables
from kohlrahbi.seed import Seed


def validate_path(ctx, param, value):
    """Ensure the path exists."""
    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"Path does not exist: {value}")
    return path


@click.command()
@click.option(
    "--format-version",
    multiple=True,
    default=[e.value for e in EdifactFormatVersion],  # Set default to all known format versions
    show_default="All",
    type=click.Choice([e.value for e in EdifactFormatVersion], case_sensitive=False),
    help="Format version(s) of the AHB documents. Default is all known format versions.",
)
@click.option(
    "--edi-energy-mirror-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    callback=validate_path,
    help="The root path to the edi_energy_mirror repository.",
    required=True,
)
def update_pruefis(format_version: list[EdifactFormatVersion], edi_energy_mirror_path: Path):
    """
    This CLI tool updates the all_known_pruefis.toml files with Prüfidentifikatoren from AHB documents.
    If no specific format version is provided, it processes all known format versions.
    """
    for version in format_version:  # Iterate over each provided format version
        all_pruefis: dict[str, str] = {}

        path_to_ahb_documents = edi_energy_mirror_path / Path(f"edi_energy_de/{version}")

        assert path_to_ahb_documents.exists(), f"The specified path {path_to_ahb_documents.absolute()} does not exist."

        output_filename = f"{version}_all_known_pruefis.toml"
        output_file_path = Path(__file__).parents[1] / "format_versions" / output_filename

        assert output_file_path.parent.exists(), f"The specified path {output_file_path.parent} does not exist."

        ahb_file_finder = DocxFileFinder.from_input_path(input_path=path_to_ahb_documents)

        ahb_file_finder.filter_for_latest_ahb_docx_files()

        for ahb_file_path in ahb_file_finder.paths_to_docx_files:
            doc = docx.Document(ahb_file_path)
            for item in get_all_paragraphs_and_tables(parent=doc):
                if isinstance(item, Table) and does_the_table_contain_pruefidentifikatoren(table=item):
                    if not item.row_cells(0)[-1].paragraphs[-1].text.startswith("Prüfidentifikator"):
                        continue
                    seed = Seed.from_table(docx_table=item)
                    logger.info("Found a table with the following pruefis: %s", seed.pruefidentifikatoren)
                    for pruefi in seed.pruefidentifikatoren:
                        all_pruefis.update({pruefi: ahb_file_path.name})

        all_pruefis = dict(sorted(all_pruefis.items()))
        if not any(all_pruefis):
            logger.warning("No Prüfidentifikatoren found in the AHB documents for format version %s.", version)
            all_pruefis = {
                "⚠️ No Prüfidentifikatoren found": f"No AHB documents found. Probably there are no AHB in the docx format in the provided path {path_to_ahb_documents}."
            }

        toml_data = {
            "meta_data": {"updated_on": date.today()},
            "pruefidentifikatoren": all_pruefis,
        }

        with open(output_file_path, "w", encoding="utf-8") as f:
            tomlkit.dump(toml_data, f)
            logger.info("🎉 Successfully updated %s and saved it at %s.", output_filename, output_file_path)


if __name__ == "__main__":
    update_pruefis()
