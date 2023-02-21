# KohlrAHBi
![Unittests status badge](https://github.com/Hochfrequenz/AHBExtractor/workflows/Unittests/badge.svg)
![Coverage status badge](https://github.com/Hochfrequenz/AHBExtractor/workflows/Coverage/badge.svg)
![Linting status badge](https://github.com/Hochfrequenz/AHBExtractor/workflows/Linting/badge.svg)
![Black status badge](https://github.com/Hochfrequenz/AHBExtractor/workflows/Black/badge.svg)


This tool helps to generate machine-readable files from AHB documents.


## Installation
Kohlrahbi is a Python based tool.
Therefor you have to make sure, that Python is running on your machine.

We recommend to use virtual environments to keep your system clean.

Create a new virtual environment with
```bash
python -m venv .venv
```

The activation of the virtual environment depends on your used OS.

**Windows**
```
.venv\Scripts\activate
```
**MacOS/Linux**
```
source .venv/bin/activate
```
Finally, install the package with

```bash
pip install kohlrahbi
```

## Usage

There are two ways to use kohlrahbi.
You can extract all prüfidetifikatoren listed in [all_known_pruefis.toml](src/kohlrahbi/all_known_pruefis.toml) or you can extract a specific prüfidetifikator.
### Get all Prüfidetifikatoren
If you want to extract all prüfidetifikatoren, you can run the following command.

```bash
kohlrahbi --input_path ../edi_energy_mirror/ --output_path ./output/
```

This will extract all prüfidetifikatoren listed in [all_known_pruefis.toml](src/kohlrahbi/all_known_pruefis.toml) and save them in the provided output path.


### Get a specific Prüfidetifikator

If you want to extract a specific prüfidetifikator, you can run the following command.

```bash
kohlrahbi --input_path ../edi_energy_mirror/ --output_path ./output/ --pruefi 11039
```

You can also provide multiple prüfidetifikatoren.

```bash
kohlrahbi --input_path ../edi_energy_mirror/ --output_path ./output/ --pruefi 11039 --pruefi 11040 --pruefi 11041
```

## Workflow

```mermaid
flowchart TB
    S[Start] --> RD[Read docx]
    RD --> RPT[Read all paragraphs <br> and tables]
    RPT --> I[Start iterating]
    I --> NI[Read next item]
    %% check for text paragraph %%
    NI --> CTP{Text Paragraph?}
    CTP -- Yes --> NI
    CTP -- No --> CCST{Is item just<br>Chapter or Section Title?}
    CCST -- Yes --> CTAenderunghistorie{Is Chapter Title<br>'Änderungshistorie'?}
    CTAenderunghistorie -- Yes --> EXPORT[Export Extract]
    CCST -- No --> CT{Is item a table<br>with prüfis?}
    CT -- Yes --> Extract[Create Extract]
```



## Development

### Setup

To setup the development environment, you have to install the dev dependencies.

```bash
tox -e dev
```

### Run all tests and linters

To run the tests, you can use tox.

```bash
tox
```
