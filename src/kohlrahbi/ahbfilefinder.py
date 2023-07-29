"""
This module contains the AhbFileFinder class.
"""
from itertools import groupby
from pathlib import Path

import attrs
from maus.edifact import EdifactFormat, get_format_of_pruefidentifikator

from kohlrahbi.logger import logger


@attrs.define(auto_attribs=True, kw_only=True)
class AhbFileFinder:
    """
    This class is responsible for finding the AHB files in the input directory.
    """

    paths_to_docx_files: list[Path]

    @classmethod
    def from_input_path(cls, input_path: Path) -> "AhbFileFinder":
        """
        Create an AhbFileFinder object from the input path.
        """

        ahb_file_paths: list[Path] = [
            path for path in input_path.iterdir() if path.is_file() if path.suffix == ".docx" if "AHB" in path.name
        ]
        if not any(ahb_file_paths):  # this is suspicious at least
            logger.warning("The directory '%s' does not contain any AHB docx files.", input_path.absolute())
        return cls(paths_to_docx_files=ahb_file_paths)

    @staticmethod
    def get_first_part_of_ahb_docx_file_name(path_to_ahb_document: Path) -> str:
        """
        Return the first part of the AHB docx file name.
        The first part contains the information about the EDIFACT formats.
        """

        return path_to_ahb_document.name.split("-")[0]

    def filter_for_latest_ahb_docx_files(self) -> None:
        """
        Filter the list of AHB docx paths for the latest AHB docx files.
        The latest files contain `LesefassungmitFehlerkorrekturen` in their file names.
        This method is _not_ pure. It changes the state of the object.
        """
        result: list[Path] = []

        groups: dict[str, list[Path]] = {  # the key is the first part of the file name, the values are matching files
            group_key: list(group)
            for group_key, group in groupby(
                sorted(self.paths_to_docx_files, key=AhbFileFinder.get_first_part_of_ahb_docx_file_name),
                key=AhbFileFinder.get_first_part_of_ahb_docx_file_name,
            )
        }
        # groups may now look like this:
        # pylint:disable=line-too-long
        # {'APERAKCONTRLAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/APERAKCONTRLAHB-informatorischeLesefassung2.3m_99991231_20231001.docx')], 'COMDISAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/COMDISAHB-informatorischeLesefassung1.0dKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/COMDISAHB-informatorischeLesefassung1.0d_99991231_20231001.docx')], 'HerkunftsnachweisregisterAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/HerkunftsnachweisregisterAHB-informatorischeLesefassung2.3cKonsolidierteLesefassungmitFehlerkorrekturenStand19.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/HerkunftsnachweisregisterAHB-informatorischeLesefassung2.3c_99991231_20231001.docx')], 'IFTSTAAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/IFTSTAAHB-informatorischeLesefassung2.0eKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/IFTSTAAHB-informatorischeLesefassung2.0e_99991231_20231001.docx')], 'INVOICREMADVAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/INVOICREMADVAHB-informatorischeLesefassung2.5bKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/INVOICREMADVAHB-informatorischeLesefassung2.5b_99991231_20231001.docx')], 'MSCONSAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/MSCONSAHB-informatorischeLesefassung3.1c_99991231_20231001.docx')], 'ORDERSORDRSPAHBMaBiS': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/ORDERSORDRSPAHBMaBiS-informatorischeLesefassung2.2c_99991231_20231001.docx')], 'PARTINAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/PARTINAHB-informatorischeLesefassung1.0c_99991231_20231001.docx')], 'PRICATAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/PRICATAHB-informatorischeLesefassung2.0c_99991231_20231001.docx')], 'REQOTEQUOTESORDERSORDRSPORDCHGAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/REQOTEQUOTESORDERSORDRSPORDCHGAHB-informatorischeLesefassung2.2KonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/REQOTEQUOTESORDERSORDRSPORDCHGAHB-informatorischeLesefassung2.2_99991231_20231001.docx')], 'UTILMDAHBGas': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBGas-informatorischeLesefassung1.0aKonsolidierteLesefassungmitFehlerkorrekturenStand29.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBGas-informatorischeLesefassung1.0a_99991231_20231001.docx')], 'UTILMDAHBMaBiS': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBMaBiS-informatorischeLesefassung4.1_99991231_20231001.docx')], 'UTILMDAHBStrom': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBStrom-informatorischeLesefassung1.1KonsolidierteLesefassungmitFehlerkorrekturenStand29.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBStrom-informatorischeLesefassung1.1_99991231_20231001.docx')], 'UTILTSAHBBerechnungsformel': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILTSAHBBerechnungsformel-informatorischeLesefassung1.0e_99991231_20231001.docx')], 'UTILTSAHBDefinitionen': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILTSAHBDefinitionen-informatorischeLesefassung1.1_99991231_20231001.docx')]}
        for group_items in groups.values():
            if len(group_items) == 1:
                result.append(group_items[0])
            else:
                for path in group_items:
                    error_corrected_version_is_present = (
                        "KonsolidierteLesefassungmitFehlerkorrekturen" in path.name
                        or "AußerordentlicheVeröffentlichung" in path.name
                    )
                    if error_corrected_version_is_present:
                        result.append(path)
                    else:
                        logger.debug("Ignoring file %s", path.name)
        self.paths_to_docx_files = result

    def filter_docx_files_for_edifact_format(self, edifact_format: EdifactFormat) -> None:
        """
        Returns a list of docx files which contain the given edifact format.
        This method is not pure. It changes the state of the object.
        """

        self.paths_to_docx_files = [path for path in self.paths_to_docx_files if str(edifact_format) in path.name]

    def get_docx_files_which_may_contain_searched_pruefi(self, searched_pruefi: str) -> list[Path]:
        """
        This functions takes a pruefidentifikator and returns a list of docx files which can contain the searched pruefi
        Unfortunately, it is not clear in which docx the pruefidentifikator you are looking for is located.
        A 11042 belongs to the UTILMD format. However, there are seven docx files that describe the UTILMD format.
        A further reduction of the number of files is not possible with the pruefidentifikator only.
        This method is _not_ pure. It changes the state of the object.
        """

        edifact_format = get_format_of_pruefidentifikator(searched_pruefi)
        if edifact_format is None:
            logger.exception("❌ There is no known format for the prüfi '%s'.", searched_pruefi)
            raise ValueError(f"There is no known format for the prüfi '{searched_pruefi}'.")

        self.filter_for_latest_ahb_docx_files()
        self.filter_docx_files_for_edifact_format(edifact_format=edifact_format)
        if (
            edifact_format == EdifactFormat.UTILMD
            and searched_pruefi.startswith("11")
            and all("202310" in path.name for path in self.paths_to_docx_files)
        ):
            logger.info(
                # pylint:disable=line-too-long
                "You searched for a UTILMD prüfi %s starting with the soon deprecated prefix '11' but all relevant files %s are valid from 2023-10 onwards. They won't contain any match.",
                searched_pruefi,
                ", ".join([path.name for path in self.paths_to_docx_files]),
            )
            return []
        return self.paths_to_docx_files
