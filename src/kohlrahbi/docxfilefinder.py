"""
This module contains the DocxFileFinder class.
"""
from itertools import groupby
from pathlib import Path

import attrs
from maus.edifact import EdifactFormat, get_format_of_pruefidentifikator

from kohlrahbi.logger import logger


@attrs.define(auto_attribs=True, kw_only=True)
class DocxFileFinder:
    """
    This class is responsible for finding the docx files in the input directory.
    It can find MIG and AHB docx files.
    """

    paths_to_docx_files: list[Path]

    @classmethod
    def from_input_path(cls, input_path: Path) -> "DocxFileFinder":
        """
        Create an DocxFileFinder object from the input path.
        """

        ahb_file_paths: list[Path] = [path for path in input_path.iterdir() if path.is_file() if path.suffix == ".docx"]
        if not any(ahb_file_paths):  # this is suspicious at least
            logger.warning("The directory '%s' does not contain any docx files.", input_path.absolute())
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
        self.paths_to_docx_files = self.filter_ahb_docx_files(self.paths_to_docx_files)
        grouped_files = self.group_files_by_name_prefix(self.paths_to_docx_files)
        self.paths_to_docx_files = self.filter_latest_version(grouped_files)

    @staticmethod
    def filter_ahb_docx_files(paths_to_docx_files: list[Path]) -> list[Path]:
        """
        This function filters the docx files which contain the string "AHB" in their file name.
        """
        return [path for path in paths_to_docx_files if "AHB" in path.name]

    @staticmethod
    def filter_for_docx_files_with_change_history(paths_to_docx_files: list[Path]) -> list[Path]:
        """
        This function filters the docx files which contain a change history.
        At this time it seems that all docx files have a change history.
        But this may change in the future, so search for some keywords in the file name.
        """
        return [
            path
            for path in paths_to_docx_files
            if "AHB" in path.name
            or "MIG" in path.name
            or "AllgemeineFestlegungen" in path.name
            or "Codeliste" in path.name
            or "Entscheidungsbaum" in path.name
        ]

    # pylint: disable=line-too-long
    @staticmethod
    def group_files_by_name_prefix(paths_to_docx_files: list[Path]) -> dict[str, list[Path]]:
        """
        This function groups the docx files by their name prefix.
        Groups may now look like this:
        {'APERAKCONTRLAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/APERAKCONTRLAHB-informatorischeLesefassung2.3m_99991231_20231001.docx')],
         'COMDISAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/COMDISAHB-informatorischeLesefassung1.0dKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/COMDISAHB-informatorischeLesefassung1.0d_99991231_20231001.docx')],
         'HerkunftsnachweisregisterAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/HerkunftsnachweisregisterAHB-informatorischeLesefassung2.3cKonsolidierteLesefassungmitFehlerkorrekturenStand19.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/HerkunftsnachweisregisterAHB-informatorischeLesefassung2.3c_99991231_20231001.docx')],
         'IFTSTAAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/IFTSTAAHB-informatorischeLesefassung2.0eKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/IFTSTAAHB-informatorischeLesefassung2.0e_99991231_20231001.docx')],
         'INVOICREMADVAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/INVOICREMADVAHB-informatorischeLesefassung2.5bKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/INVOICREMADVAHB-informatorischeLesefassung2.5b_99991231_20231001.docx')],
         'MSCONSAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/MSCONSAHB-informatorischeLesefassung3.1c_99991231_20231001.docx')],
         'ORDERSORDRSPAHBMaBiS': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/ORDERSORDRSPAHBMaBiS-informatorischeLesefassung2.2c_99991231_20231001.docx')],
         'PARTINAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/PARTINAHB-informatorischeLesefassung1.0c_99991231_20231001.docx')],
         'PRICATAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/PRICATAHB-informatorischeLesefassung2.0c_99991231_20231001.docx')],
         'REQOTEQUOTESORDERSORDRSPORDCHGAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/REQOTEQUOTESORDERSORDRSPORDCHGAHB-informatorischeLesefassung2.2KonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/REQOTEQUOTESORDERSORDRSPORDCHGAHB-informatorischeLesefassung2.2_99991231_20231001.docx')],
         'UTILMDAHBGas': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBGas-informatorischeLesefassung1.0aKonsolidierteLesefassungmitFehlerkorrekturenStand29.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBGas-informatorischeLesefassung1.0a_99991231_20231001.docx')],
         'UTILMDAHBMaBiS': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBMaBiS-informatorischeLesefassung4.1_99991231_20231001.docx')],
         'UTILMDAHBStrom': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBStrom-informatorischeLesefassung1.1KonsolidierteLesefassungmitFehlerkorrekturenStand29.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBStrom-informatorischeLesefassung1.1_99991231_20231001.docx')],
         'UTILTSAHBBerechnungsformel': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILTSAHBBerechnungsformel-informatorischeLesefassung1.0e_99991231_20231001.docx')], 'UTILTSAHBDefinitionen': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILTSAHBDefinitionen-informatorischeLesefassung1.1_99991231_20231001.docx')]}
        """
        return {
            group_key: list(group)
            for group_key, group in groupby(
                sorted(paths_to_docx_files, key=DocxFileFinder.get_first_part_of_ahb_docx_file_name),
                key=DocxFileFinder.get_first_part_of_ahb_docx_file_name,
            )
        }

    @staticmethod
    def filter_latest_version(groups: dict[str, list[Path]]) -> list[Path]:
        """
        This function filters the latest version of the AHB or MIG docx files.
        """
        result = []
        for group_items in groups.values():
            if len(group_items) == 1:
                result.append(group_items[0])
            else:
                for path in group_items:
                    if (
                        "KonsolidierteLesefassungmitFehlerkorrekturen" in path.name
                        or "AußerordentlicheVeröffentlichung" in path.name
                    ):
                        result.append(path)
                    else:
                        logger.debug("Ignoring file %s", path.name)
        return result

    def filter_for_latest_mig_and_ahb_docx_files(self) -> None:
        """
        Filter the list of MIG docx paths for the latest MIG docx files.
        """
        self.paths_to_docx_files = self.filter_for_docx_files_with_change_history(self.paths_to_docx_files)
        grouped_files = self.group_files_by_name_prefix(self.paths_to_docx_files)
        self.paths_to_docx_files = self.filter_latest_version(grouped_files)

    def filter_docx_files_for_edifact_format(self, edifact_format: EdifactFormat) -> None:
        """
        Returns a list of docx files which contain the given edifact format.
        This method is not pure. It changes the state of the object.
        """

        self.paths_to_docx_files = [path for path in self.paths_to_docx_files if str(edifact_format) in path.name]

    def remove_temporary_files(self):
        """
        This method removes all temporary files from paths_to_docx_files.
        Temporary files lead to the exception `BadZipFile: File is not a zip file`.
        It appears if a docx file is opened by Word.
        """

        self.paths_to_docx_files = [path for path in self.paths_to_docx_files if not path.name.startswith("~")]

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

    def get_all_docx_files_which_contain_change_histories(self) -> list[Path]:
        """
        This function returns a list of docx fils which probably contain a change history.
        Only format documents like UTILMD, MSCONS etc. contain a change history.
        """

        self.filter_for_latest_mig_and_ahb_docx_files()
        self.remove_temporary_files()

        return self.paths_to_docx_files
