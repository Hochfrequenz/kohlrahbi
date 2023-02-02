"""
This file makes the package itself executable.
You can run it with:

    python -m kohlrahbi

"""
import argparse
import sys
from pathlib import Path
from typing import List

from kohlrahbi import harvester
from kohlrahbi.helper.read_functions import remove_duplicates_from_ahb_list

if __name__ == "__main__":
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        sys.exit("Python >=3.11 is required to run this script")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path", "-p", help="relative path to either a directory that contains docx files or a single docx file"
    )
    docx_file_paths: List[Path]
    args = parser.parse_args()
    path_to_either_file_or_dir: Path
    if not args.path:
        print("No path was given (via the --path cli argument): Use CWD instead")
        path_to_either_file_or_dir = Path.cwd()
    else:
        path_to_either_file_or_dir = Path(args.path)
    if path_to_either_file_or_dir.is_dir():
        docx_file_paths = [x for x in path_to_either_file_or_dir.glob("**/*.docx")]  # all docx recursively
        if len(docx_file_paths) == 0:
            sys.exit(f"No files found in {path_to_either_file_or_dir}")
    elif not path_to_either_file_or_dir.exists():
        sys.exit(f"The path {path_to_either_file_or_dir} was not found")
    elif not path_to_either_file_or_dir.is_dir():
        sys.exit(f"The path {path_to_either_file_or_dir} is not a directory")
    elif not path_to_either_file_or_dir.suffix == ".docx":
        sys.exit(f"The path {path_to_either_file_or_dir} is does not end with '.docx'")
    else:
        docx_file_paths = [path_to_either_file_or_dir]
    docx_file_paths = [x for x in docx_file_paths if "ahb" in str(x).lower()]  # filter out migs, codelisten foo, etc
    remove_duplicates_from_ahb_list(docx_file_paths)
    docx_file_paths = [
        x for x in docx_file_paths if ("aperak" not in str(x).lower() and "contrl" not in str(x).lower())
    ]  # sorry for that
    print(f"Start processing {len(docx_file_paths)} files...")
    harvester.main(file_paths=docx_file_paths)
