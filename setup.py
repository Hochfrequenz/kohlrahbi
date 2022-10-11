from setuptools import find_packages, setup

setup(
    name="ahbextractor",
    version="0.0.0",
    author="Kevin Krechan",
    author_email="kevin.krechan@hochfrequenz.de",
    description="Tool to generate machine readable files from AHB documents.",
    packages=find_packages(),
    install_requires=["openpyxl", "pandas", "python-docx", "XlsxWriter"],
    package_data={"*": ["py.typed"]},
)
