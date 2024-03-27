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


@click.command()
@click.option(
    "--format_version",
    type=click.Choice([e.value for e in EdifactFormatVersion], case_sensitive=False),
    help="Format version of the AHB documents.",
)
def update_pruefis(format_version):
    """
    This CLI tool updates the all_known_pruefis.toml file with Prüfidentifikatoren from AHB documents in the specified format version folder.
    """
    all_pruefis: dict[str, str] = {}

    # pre-flight checks for the input and output paths
    edi_energy_mirror_repo_root_path = Path(__file__).parent.parent.parent.parent.parent / "edi_energy_mirror"
    path_to_ahb_documents = edi_energy_mirror_repo_root_path / Path(f"edi_energy_de/{format_version}")

    assert path_to_ahb_documents.exists(), f"The specified path {path_to_ahb_documents} does not exist."

    output_filename = f"{format_version}_all_known_pruefis.toml"
    output_file_path = Path(__file__).parent.parent / "format_versions" / output_filename

    assert output_file_path.parent.exists(), f"The specified path {output_file_path.parent} does not exist."

    # alright, we are ready for lift-off
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

    toml_data = {
        "meta_data": {"updated_on": date.today()},
        "pruefidentifikatoren": all_pruefis,
    }

    with open(output_file_path, "w", encoding="utf-8") as f:
        tomlkit.dump(toml_data, f)
        logger.info("🎉 Successfully updated %s and saved it at %s.", output_filename, output_file_path)


if __name__ == "__main__":
    update_pruefis()
