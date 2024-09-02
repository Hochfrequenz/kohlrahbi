## What's Changed
* add gh action for cliff
* add cliff config
* refactor(dependencies): Move MAUS dependencies to kohlrahbi, replace attrs with pydantic, remove marshmallow
* Bump pydantic-core from 2.23.0 to 2.23.1
* fix(test): 🚛 rename test file to fix tests
* fix: parsing of segment ids

## What's Changed in v1.5.0
* Bump marshmallow from 3.21.3 to 3.22.0
* Bump pydantic-core from 2.22.0 to 2.23.0
* Bump numpy from 2.0.1 to 2.1.0
* Bump pydantic-core from 2.21.0 to 2.22.0
* Bump tomlkit from 0.13.1 to 0.13.2
* Bump tomlkit from 0.13.0 to 0.13.1
* Bump lxml from 5.2.2 to 5.3.0
* Bump more-itertools from 10.3.0 to 10.4.0
* Bump ytanikin/PRConventionalCommits from 1.1.0 to 1.2.0
* ci(gh action): Add check for conventional commit in PR title
* Bump attrs from 24.1.0 to 24.2.0
* Bump pydantic-core from 2.20.1 to 2.21.0
* ci[dependency management] Use Optional Dependencies In Pyproject.toml and Update GH Actions
* Bump black from 24.4.2 to 24.8.0
* Bump attrs from 23.2.0 to 24.1.0
* Bump coverage from 7.6.0 to 7.6.1
* Update Dependencies and Add Syrupy
* Bump efoli from 1.0.0 to 1.1.0
* Bump maus from 0.5.4 to 0.6.0

**Full Changelog**: https://github.com///compare/v1.4.4...v1.5.0

## What's Changed in v1.4.4
* Set maus 0.5.4 as min version

**Full Changelog**: https://github.com///compare/v1.4.3...v1.4.4

## What's Changed in v1.4.3
* Bump maus from 0.5.3 to 0.5.4

**Full Changelog**: https://github.com///compare/v1.4.2...v1.4.3

## What's Changed in v1.4.2
* chore: improve readability  of dump function
* Bump mypy from 1.11.0 to 1.11.1

**Full Changelog**: https://github.com///compare/v1.4.1...v1.4.2

## What's Changed in v1.4.1
* fix: add forgotton "xlsx" sub-directory to path

**Full Changelog**: https://github.com///compare/v1.4.0...v1.4.1

## What's Changed in v1.4.0
* Avoid unnecessary write operations: Dont' dump if JSON output didn't changed
* Bump pydantic from 2.7.1 to 2.8.2
* Bump tomlkit from 0.12.5 to 0.13.0
* Bump numpy from 2.0.0 to 2.0.1

**Full Changelog**: https://github.com///compare/v1.3.0...v1.4.0

## What's Changed in v1.3.0
* ignore capitalization in filenames when filtering for the latest file
* Bump pytest from 8.3.1 to 8.3.2
* Bump pylint from 3.2.5 to 3.2.6
* Bump mypy from 1.10.1 to 1.11.0
* Bump pytest from 8.2.2 to 8.3.1
* Bump maus from 0.5.2 to 0.5.3
* Bump coverage from 7.5.4 to 7.6.0
* Bump types-requests from 2.32.0.20240622 to 2.32.0.20240712

**Full Changelog**: https://github.com///compare/v1.2.0...v1.3.0

## What's Changed in v1.2.0
* ignore ahb tables where no pruefi is provided
* Remove double entries in flatahb output
* remove irrelevant lines in flatahb output
* add conditions to flatahbtable output
* Bump mypy from 1.10.0 to 1.10.1
* Bump types-requests from 2.32.0.20240602 to 2.32.0.20240622
* Bump twine from 5.1.0 to 5.1.1
* Bump zipp from 3.18.1 to 3.19.1 in /dev_requirements in the pip group across 1 directory
* Bump pylint from 3.2.3 to 3.2.5
* Bump coverage from 7.5.3 to 7.5.4
* Bump openpyxl from 3.1.4 to 3.1.5
* Bump typing-extensions from 4.11.0 to 4.12.2
* Bump packaging from 24.0 to 24.1
* Bump numpy from 1.26.4 to 2.0.0
* Remove section_name From Flatahb If segment_code Is Empty, modified test
* Bump certifi from 2024.2.2 to 2024.7.4 in /dev_requirements in the pip group across 1 directory
* Bump urllib3 from 2.2.1 to 2.2.2 in /dev_requirements in the pip group across 1 directory
* Bump openpyxl from 3.1.3 to 3.1.4
* Bump more-itertools from 10.2.0 to 10.3.0
* Bump pylint from 3.2.2 to 3.2.3
* Bump marshmallow from 3.21.2 to 3.21.3
* Bump pytest from 8.2.1 to 8.2.2
* Bump pandas-stubs from 2.2.2.240514 to 2.2.2.240603
* Bump types-requests from 2.32.0.20240523 to 2.32.0.20240602
* Add link to fundamend
* Bump openpyxl from 3.1.2 to 3.1.3
* Bump requests from 2.31.0 to 2.32.0 in /dev_requirements in the pip group across 1 directory
* Bump coverage from 7.5.2 to 7.5.3
* Bump coverage from 7.5.1 to 7.5.2
* Bump types-requests from 2.32.0.20240521 to 2.32.0.20240523

**Full Changelog**: https://github.com///compare/v1.1.3...v1.2.0

## What's Changed in v1.1.3
* filter for most recent file
* Bump pylint from 3.2.1 to 3.2.2
* Bump annotated-types from 0.6.0 to 0.7.0
* Bump types-requests from 2.31.0.20240406 to 2.32.0.20240521

**Full Changelog**: https://github.com///compare/v1.1.2...v1.1.3

## What's Changed in v1.1.2
* Use default_factories
* Try manual garbage collection to avoid memory leaks
* Fix Type Hints of `file_type`; It's a tuple of, not a single export type

**Full Changelog**: https://github.com///compare/v1.1.1...v1.1.2

## What's Changed in v1.1.1
* Fix regression: Treat empty string `''` as `None` data element ID

**Full Changelog**: https://github.com///compare/v1.1.0...v1.1.1

## What's Changed in v1.1.0
* Extract 5 digit Segment ID from (some) ≥FV2410 AHBs
* Bump pylint from 3.2.0 to 3.2.1
* Bump pytest from 8.2.0 to 8.2.1
* chore: drop `pip-compile step` from dev env setup; Add `pip-compile-multi` env
* 🧹 Switch to `mypy --strict`
* Bump pylint from 3.1.1 to 3.2.0 + fix minor linting issues
* Bump python-docx from 1.1.0 to 1.1.2
* Bump twine from 5.0.0 to 5.1.0
* Bump maus from 0.4.2 to 0.5.0
* Bump pandas-stubs from 2.2.1.240316 to 2.2.2.240514

**Full Changelog**: https://github.com///compare/v1.0.0...v1.1.0

## What's Changed in v1.0.0
* extract conditions and packages
* Bump lxml from 5.2.1 to 5.2.2
* Bump pylint from 3.1.0 to 3.1.1
* Bump freezegun from 1.5.0 to 1.5.1
* Bump tomlkit from 0.12.4 to 0.12.5
* Bump pydantic from 2.7.0 to 2.7.1
* Bump coverage from 7.5.0 to 7.5.1
* Bump marshmallow from 3.21.1 to 3.21.2
* Bump pytest from 8.1.1 to 8.2.0
* Bump black from 24.4.1 to 24.4.2
* Bump black from 24.4.0 to 24.4.1
* Bump mypy from 1.9.0 to 1.10.0
* Bump freezegun from 1.4.0 to 1.5.0
* Bump coverage from 7.4.4 to 7.5.0
* ⬆️ Update dependencies
* Add Version Flag
* handle line endings in csv files
* Bump black from 24.3.0 to 24.4.0
* Bump idna from 3.6 to 3.7 in /dev_requirements
* Bump lxml from 5.1.1 to 5.2.1
* 🔥 delete collect pruefis
* Rework
* Bump types-requests from 2.31.0.20240403 to 2.31.0.20240406
* Bump types-requests from 2.31.0.20240402 to 2.31.0.20240403
* Bump types-requests from 2.31.0.20240311 to 2.31.0.20240402
* Bump build from 1.1.1 to 1.2.1

**Full Changelog**: https://github.com///compare/v0.4.1...v1.0.0

## What's Changed in v0.4.1
* Fix toml path
* Fix dev-environment

**Full Changelog**: https://github.com///compare/v0.4.0...v0.4.1

## What's Changed in v0.4.0
* Scrape all known pruefis for each format version
* 🎨 Use kebab case for flags
* 🩹Upgrade `requirements-packaging.txt` - resolve `InvalidDistribution` issue
* Bump pandas-stubs from 2.2.0.240218 to 2.2.1.240316
* Bump black from 24.2.0 to 24.3.0
* chore: ⬆ Upgrade `packaging` dependencies
* Bump coverage from 7.4.3 to 7.4.4
* docs: Mention migmose
* Bump mypy from 1.8.0 to 1.9.0
* Bump pytest from 8.1.0 to 8.1.1
* Bump types-requests from 2.31.0.20240218 to 2.31.0.20240311
* Bump pytest from 8.0.2 to 8.1.0
* Bump build from 1.0.3 to 1.1.1
* Bump tomlkit from 0.12.3 to 0.12.4
* Bump pytest from 8.0.1 to 8.0.2
* Bump pandas from 2.2.0 to 2.2.1
* Bump pylint from 3.0.3 to 3.1.0
* Bump coverage from 7.4.2 to 7.4.3
* Bump the pip group across 1 directories with 1 update
* Bump coverage from 7.4.1 to 7.4.2
* Bump pandas-stubs from 2.1.4.231227 to 2.2.0.240218
* Bump pytest from 8.0.0 to 8.0.1
* Bump types-requests from 2.31.0.20240125 to 2.31.0.20240218
* Bump xlsxwriter from 3.1.9 to 3.2.0
* Bump black from 24.1.1 to 24.2.0
* Bump twine from 4.0.2 to 5.0.0
* 📝 Add kohlrahbi image to README
* Bump pytz from 2023.4 to 2024.1
* Bump maus from 0.4.1 to 0.4.2
* Bump isort from 5.12.0 to 5.13.2
* Bump pytest from 7.4.4 to 8.0.0
* Bump colorlog from 6.8.0 to 6.8.2
* Bump pytz from 2023.3.post1 to 2023.4
* Bump coverage from 7.4.0 to 7.4.1
* ci: 📍 pin formatting dependencies and ⬆ bump black to 24.1.1 and isort to 5.13.0
* Bump types-requests from 2.31.0.20240106 to 2.31.0.20240125
* Bump maus from 0.4.0 to 0.4.1
* Bump pandas from 2.1.4 to 2.2.0

**Full Changelog**: https://github.com///compare/v0.3.1...v0.4.0

## What's Changed in v0.3.1
* fix: 📍 Pin packaging requirements; Fix file path in publish workflow

**Full Changelog**: https://github.com///compare/v0.3.0...v0.3.1

## What's Changed in v0.3.0
* Memorize which File contains which Pruefi Tables

**Full Changelog**: https://github.com///compare/v0.2.1...v0.3.0

## What's Changed in v0.2.1
* Bump types-requests from 2.31.0.20231231 to 2.31.0.20240106
* Use release-environment-based PyPI Publishing
* Bump attrs from 23.1.0 to 23.2.0
* Bump pytest from 7.4.3 to 7.4.4
* Bump types-requests from 2.31.0.10 to 2.31.0.20231231
* Bump coverage from 7.3.4 to 7.4.0
* Bump pandas-stubs from 2.1.4.231218 to 2.1.4.231227
* Remove outdated 11... pruefis
* Support Python 3.12 (blocked by lxml)
* Bump mypy from 1.5.1 to 1.8.0
* Bump types-requests from 2.31.0.6 to 2.31.0.10
* Bump pytest from 7.4.2 to 7.4.3
* Bump pandas-stubs from 2.0.1.230501 to 2.1.4.231218
* Bump coverage from 7.3.3 to 7.3.4
* Bump pylint from 3.0.1 to 3.0.3

**Full Changelog**: https://github.com///compare/v0.2.0...v0.2.1

## What's Changed in v0.2.0
* Pin CI dependencies
* 🔥 Remove if case which stops iteration
* Add New Feature Flavour To Scrape Änderungshistorien
* Bump pandas from 2.1.3 to 2.1.4
* Bump actions/setup-python from 4 to 5
* Bump colorlog from 6.7.0 to 6.8.0
* Read name and direction from AHB table headers
* Bump tomlkit from 0.12.2 to 0.12.3
* Bump pandas from 2.1.2 to 2.1.3
* Bump tomlkit from 0.12.1 to 0.12.2
* Bump python-docx from 1.0.1 to 1.1.0
* Add workflow to auto-approve and -merge dependabot PRs
* Extract AHB conditions.json
* Bump pandas from 2.1.1 to 2.1.2
* 🩹Fixed typo and adapted path in test for windows
* Bump xlsxwriter from 3.1.8 to 3.1.9
* 🩹fixed typo for conditions in classmethod 'from_ahb_table' in class 'UnfoldedAhb'
* Bump xlsxwriter from 3.1.7 to 3.1.8
* Bump python-docx from 1.0.0 to 1.0.1
* Bump python-docx from 0.8.11 to 1.0.0
* Bump maus from 0.3.43 to 0.4.0
* Bump xlsxwriter from 3.1.6 to 3.1.7
* Bump xlsxwriter from 3.1.5 to 3.1.6
* Bump xlsxwriter from 3.1.4 to 3.1.5
* Bump pandas from 2.1.0 to 2.1.1
* Bump xlsxwriter from 3.1.3 to 3.1.4
* Bump xlsxwriter from 3.1.2 to 3.1.3
* Bump pytz from 2023.3 to 2023.3.post1
* Bump actions/checkout from 3 to 4
* Bump pandas from 2.0.3 to 2.1.0
* Bump click from 8.1.6 to 8.1.7

**Full Changelog**: https://github.com///compare/v0.1.1...v0.2.0

## What's Changed in v0.1.1
* Bump maus from 0.3.41 to 0.3.43

**Full Changelog**: https://github.com///compare/v0.1.0...v0.1.1

## What's Changed in v0.1.0
* Set maus v0.3.41 as min version
* Bump maus from 0.3.39 to 0.3.41

**Full Changelog**: https://github.com///compare/v0.0.9...v0.1.0

## What's Changed in v0.0.9
* Add some more `del` statements
* Bump tomlkit from 0.11.8 to 0.12.1
* doc: Add link to `machine-readable_anwendungshandbuecher`
* docs: fixed code block to render reference correctly

**Full Changelog**: https://github.com///compare/v0.0.8...v0.0.9

## What's Changed in v0.0.8
* ✨Support wild cards as CLI pruefi args
* Readability: Use dict comprehension instead of looping over group by

**Full Changelog**: https://github.com///compare/v0.0.7...v0.0.8

## What's Changed in v0.0.7
* 🐛: Re-instantiate `ahb_file_finder` for every pruefi

**Full Changelog**: https://github.com///compare/v0.0.6...v0.0.7

## What's Changed in v0.0.6
* Extend list of supported pruefis (mainly FV2310 UTILMD 44***, 55***)
* 🔉 Reduce Log Level of "Found a table with the following pruefis..."; ⚡Access `item.style` half as often
* FlatAHB Dump: Don't use new GUID for otherwise unchanged lines
* 🐛 Don't drop adjacent lines with only Value Pool Entries when Unfolding AHB
* 🐛 Don't decorate test class with `@attrs`; Fix error hidden behind failed test class instantiation: `reset_index` should modify the instance
* Bump click from 8.1.5 to 8.1.6

**Full Changelog**: https://github.com///compare/v0.0.5...v0.0.6

## What's Changed in v0.0.5
* Don't try to find deprecated 11... Prüfis in >= 2023-10-01 Files
* `del` variables after use; Maybe this reduces the memory footprint?
* Bump click from 8.1.3 to 8.1.5
* 🥅 Add pokemon catcher around single pruefi scraping
* Read every docx file only once
* 🩹 Fix typo
* prefer `list` over `List`
* Update license in pyproject
* 📄 Add LICENSE
* Bump pandas from 2.0.2 to 2.0.3
* Bump pandas from 2.0.1 to 2.0.2
* Bump xlsxwriter from 3.1.1 to 3.1.2
* Bump xlsxwriter from 3.1.0 to 3.1.1
* Bump maus from 0.3.18 to 0.3.39
* Bump maus from 0.3.13 to 0.3.18
* Bump attrs from 22.2.0 to 23.1.0
* Bump tomlkit from 0.11.7 to 0.11.8
* Bump pandas from 2.0.0 to 2.0.1
* Bump xlsxwriter from 3.0.9 to 3.1.0
* Bump maus from 0.3.11 to 0.3.13

**Full Changelog**: https://github.com///compare/v0.0.4...v0.0.5

## What's Changed in v0.0.4
* 🧹Ensure stable formatting of FlatAHBs
* Bump maus from 0.3.10 to 0.3.11
* Remove set functions in get function
* 📝Fix `edi_energy_mirror` path in README MWE
* 🔊 Print/Log more info in click script
* Bump pandas from 1.5.3 to 2.0.0
* Bump maus from 0.3.2 to 0.3.10
* Bump tomlkit from 0.11.6 to 0.11.7
* Bump pytz from 2023.2 to 2023.3
* Bump pytz from 2022.7.1 to 2023.2
* Bump xlsxwriter from 3.0.8 to 3.0.9
* Bump openpyxl from 3.1.1 to 3.1.2
* Add new flag --assume-yes / -y
* 🎨 Improve the output folder order
* 🩹 Fix output path issue

**Full Changelog**: https://github.com///compare/v0.0.3...v0.0.4

## What's Changed in v0.0.3
* 🔈 Add log message if no docx file was found
* 🔄 After maus upgrade, all known prüfis work

**Full Changelog**: https://github.com///compare/v0.0.2...v0.0.3

## What's Changed in v0.0.2
* ⬆️Update maus in pyproject.toml
* Fix README: The CLI arg is `pruefis`, not `pruefi`
* Set maus >= v0.3.2 as min version dependency
* Bump maus from 0.3.1 to 0.3.2

**Full Changelog**: https://github.com///compare/v0.0.1...v0.0.2

## What's Changed in v0.0.1
* 🖊Fix typos in README: "Prüfide**n**tifikator"
* 🏷Add PyPI Status Badge to README
* 📝 Add explanation how to use kohlrahbi
* 💚 Update gh action publish workflow

**Full Changelog**: https://github.com///compare/v0.0.0...v0.0.1

## What's Changed in v0.0.0
* 📦🐍  Use hatch and pyproject.toml for packaging
* 🩹 Fix prüfis which have a following landscape table
* 🖤👷‍♂️Switch to native Black action
* Bump pytz from 2022.7 to 2022.7.1
* Rework of the whole workflow
* Bump maus from 0.2.6 to 0.3.1
* Bump pandas from 1.5.2 to 1.5.3
* Bump xlsxwriter from 3.0.5 to 3.0.7
* Bump maus from 0.2.5 to 0.2.6
* Bump xlsxwriter from 3.0.4 to 3.0.5
* Bump maus from 0.2.3 to 0.2.5
* Bump xlsxwriter from 3.0.3 to 3.0.4
* ⬆🐍Upgrade CI Actions to 3.11 (and demonstrate that kohlrahbi is generally 3.11 compatible)
* ⬆ pandas `1.5.2` and numpy `1.24.0`
* Bump maus from 0.2.2 to 0.2.3
* Bump attrs from 22.1.0 to 22.2.0
* Bump maus from 0.1.24 to 0.2.2
* ⬆Upgrade to lxml 4.9.2
* 🚛 Rename `ahbexctractor`➡`kohlrahbi`
* Bump maus from 0.1.23 to 0.1.24
* ✨ Write output files into edifact_format(_version) specific directories
* ✨ Add function to remove duplicate AHB paths
* Bump actions/setup-python from 2 to 4
* Bump actions/checkout from 2 to 3
* 🤖Update Github Actions using Dependabot
* Bump pandas from 1.5.0 to 1.5.1
* ✔ Add Unittest for `get_all_paragraphs_and_tables`
* 🧹more elegant mapping
* ✔ Add Unit Test for `beautify_bedingungen` + Fix incorrect Type Hints
* 📦 Prepare for Publishing as Package
* Unittest 3.9 and 3.10; Black, Test&Coverage, Linting only on 3.10
* Add `py.typed` Files and Type Check Unittests
* 🚚 Introduce `src` based layout
* Bump pandas from 1.4.3 to 1.5.0
* 🔊 Remove `print(...)` from `ahbextractor`(`.helper`) package
* Fix MyPy Errors
* 🎨 Introduce Elixir class
* Introduce MyPy Checks
* Allow Batch Processing
* Bump numpy from 1.21.5 to 1.22.0
* Bump openpyxl from 3.0.9 to 3.0.10
* Bump pandas from 1.3.5 to 1.4.3
* Update ahbextractor/helper/write_functions.py
* Update ahbextractor/helper/write_functions.py
* Update ahbextractor/helper/write_functions.py
* Update ahbextractor/helper/write_functions.py
* Update unittests/test_check_row_type.py
* Update ahbextractor/helper/write_functions.py
* Update ahbextractor/helper/write_functions.py
* Bump xlsxwriter from 3.0.2 to 3.0.3
* Bump lxml from 4.6.5 to 4.9.1
* Request Dependabot Reviews from 🐍Review Team
* Bump openpyxl from 3.0.7 to 3.0.9
* Bump pandas from 1.2.4 to 1.3.5
* Bump xlsxwriter from 1.4.3 to 3.0.2
* Bump lxml from 4.6.3 to 4.6.5
* Install Dependabot
* 💡 Remove unnecessary text
* 💡 Precise error message
* 👩‍💻 Improve saving feedback
* 💡 Add comment to explain list(df.columns)[:5]
* 🎨 Improve function name to export *single* pruefidentifikator
* 🔥 Remove deprecated code
* 💡 Improve docstring of define_row_type
* 💡 Improve docstring of RowType enum
* 💡 Add color name in comment
* 📝 Add examples for RowTypes in docstring
* 📝 Improve some docstrings
* 👩‍💻 Improve user feedback in error case
* 📝 Improve docstring of main function
* 📝 Try to improve understanding for activating virtual environment
* 📝 Improve README
* 📝 Make purpose of the app clearer
* 📝Add some lines for how to install and execute the ahbscraper
* Fix module not found error in tests
* 🚨🔧 Add "df" too good-names
* 🚨 Fix linter warnings
* 🚨 Disable wrong linter warnings
* 📝 Add module docstrings
* 🔧 Add ahb_extractor to pylint
* 🩹 Remove additional whitespace
* 🙈 Ignore 7z files
* 📝 Add docstrings to write_functions.py
* 📝 Add docstrings to app.py
* 📝 Add docstrings to read_functions.py
* 📝 Add docstrings to functions in export_functions.py
* 📝Add docstrings to functions in check_row_type.py
* 🎨 Remove unused parameter from export_pruefidentifikator
* 🎨 Separate export functions
* 🐛 Fix issue with multiline dataelement in empty row
* ✅ Update tests to new module structure
* ♻ Great restructuring
* 🚚 Add folder AHB_Extractor
* 📝 Add some explaining lines to the README
* ✅ Add test for multi entry dataelement
* 🎨 Remove hard coded pruefi tabstop posistions
* ✅🎨 Create an extra function to prepare docx table row for testing
* ✅ Add tests for write_dataelement_to_dataframe
* ✅ Add tests for write_segmentgruppe and write_segment
* ✅🎨 Move some class variables into function to avoid conflicts
* ✅ Add test for write_segment_name _to_dataframe
* 🎨 Rename TestClass and param ids
* 🐛 Fixed issue with multiline Segmentnamen got cut after first line
* ✅ Add tests for parsing edifact struktur and bedingungen cells
* 🎨 Remove unnecessary pass command
* 🎨 Comment out else case which is probably not reachable
* ✅ Improve test structure for better understanding
* 🐛 Fix issue with repeating text in the output cells
* ✅ Add tests for write functions
* ♻ Restructure all write functions
* 🐛 Fix bugs found by unittests
* ✅🎨 Restructure test for check_row_type
* ✅ Add EMTPY row type to tests
* ✅ Add tests for row defintions
* 🎨 Remove text_in_row_as_list parameter from is_row_segmentname function
* 🎨 Remove parameter text_in_row_as_list from is_row_header call
* ➕ Add XlsxWriter to dependencies
* 🎨 Replace text_in_row_as_list with edifact_struktur_cell
* 🎨 Remove unused table parameter in is_row_segementname
* 🔥 Remove template files
* 🎨 Remove table parameter in is_row_segmentname
* 🟨 Try some different JSON structures
* 🎨 Save all PID in one file
* 🩹 Remove writer.save() to avoid warning caused by double closed file
* 🎨 Improve formate of excel files
* 🔥 Remove comment with depricated idea
* 🎨 Replace hard coded left indent position with variable
* 🐛 Fix bug of missing multiline expression
* 🙈 Add json files to gitignore
* 🔥 remove commented out code lines
* 🎨 Add output folder and subfolder for each export file format
* 💤 Disable lines to save all prüfidentifikatoren in one xlsx file
* 🎨 Add typehints for return values
* 🎨💡 Add typehint and docstring to function get_tabstop_positions
* 🎨 Use xlsxwriter to improve excel sheet layout
* ✨ Add beautify Bedingungen function
* 🔥 Remove commented out lines
* 🎉 First successful run through whole document \^.^/
* 🎨 Remove dataframe_row argument from write_segment_name_to_dataframe
* 🎨💡 Improve structure and add comments for if cases
* 🎨 Add dynamic tabstop positions as argument
* 🔥 Delete deprecated code
* 🙈 Add xlsx and csv files to gitignore
* 🎨 Create new function to read tables
* ✨ Get Prüfis from Header and tabstop positons from third row
* ✨ Iterate through all paragraphs and tables
* 🎨 Define one function for writing row into dataframe
* 🎨 Use CamelCase for enum class
* 🔥 Remove unused line
* 🎨 Change start of tables list to loop through all tables
* 🔥 Remove unused lines
* 🎨 Rename parser function for middle column cells
* 🎨 Add type hint for create_list_of_column_indices
* ✨ Add case for EMPTY cell
* 🎨Add additional attribute middle_cell to write SEGMENT and DATENELEMENT
* 🐛 Small bug fixes for the list row_cell_texts_as_list
* ♻ Put write functions into separate file
* 🔧 Add black profile to isort config
* 🔥 Remove unused functions
* ♻ Put check row type functions into separate file
* 🔥 Remove unused import of numpy
* ✨ Parse multi line codelists into separate dataframe rows
* 🔥 remove old and unstructured code
* 🚧 WIP
* ♻️ Big code refactoring part 01
* 🚧 Add three column tables
* 🎨 Rename path for documents
* 🙈 Add document folders to gitignore
* ➕ Add dependencies
* 🚧 WIP
* Initial commit

**Full Changelog**: https://github.com///compare/working...v0.0.0

<!-- generated by git-cliff -->
