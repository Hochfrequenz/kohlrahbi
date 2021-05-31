# Python Template Repository including Tox.ini, Unittests, Linting Actions and Coverage Measurements
<!--- you need to replace the `organization/repo_name` in the status badge URLs --->
![Unittests status badge](https://github.com/Hochfrequenz/python_template_repository/workflows/Unittests/badge.svg)
![Coverage status badge](https://github.com/Hochfrequenz/python_template_repository/workflows/Coverage/badge.svg)
![Linting status badge](https://github.com/Hochfrequenz/python_template_repository/workflows/Linting/badge.svg)
![Black status badge](https://github.com/Hochfrequenz/python_template_repository/workflows/Black/badge.svg)

This is a template repository. It doesn't contain any useful code but only a minimal working setup for a Python project including:

+ a basic **project structure** with
    + tox.ini
    + requirements.in
    + and a requirements.txt derived from it
    + an example class
    + an example unit test (using pytest)
+ ready to use **Github Actions** for
    + [pytest](https://pytest.org)
    + [code coverage measurement](https://coverage.readthedocs.io) (fails below 80% by default)
    + [pylint](https://pylint.org/) (only accepts 10/10 code rating by default)
    + [black](https://github.com/psf/black) code formatter check
      using [lgeiger/black-action](https://github.com/lgeiger/black-action)

By default it uses Python version 3.9.

## How to use this Repository on Your Machine

This introduction assumes that you have tox installed already (
see [installation instructions](https://tox.readthedocs.io/en/latest/install.html)) and that a `.toxbase` environment
has been created.

If this is the case, clone this repository and create the `dev` environment on your machine.

```bash
tox -e dev
```

### How to use with PyCharm

1. Create a new project using existing sources with your local working copy of this repository as root directory. Choose
   the path `your_repo/.tox/dev/` as path of the "previously configured interpreter".
2. Set the
   default [test runner of your project](https://www.jetbrains.com/help/pycharm/choosing-your-testing-framework.html) to
   pytest.
3. Set
   the [working directory of the unit tests](https://www.jetbrains.com/help/pycharm/creating-run-debug-configuration-for-tests.html)
   to the project root (instead of the unittest directory)

### How to use with VS Code

1. Open the folder with VS Code.
2. **Select the python interpreter** which is created by tox. Open the command pallett with `CTRL + P` and type `Python: Select Interpreter`. Select the interpreter which is placed in `.tox/dev/Scripts/python.exe` under Windows or `.tox/dev/bin/python` under Linux and macOS.
3. **Setup pytest and pylint**. Therefore we open the file `.vscode/settings.json` which should be automatically generated during the interpreter setup. Insert the following lines into the settings:
```json
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestEnabled": true,
    "pythonTestExplorer.testFramework": "pytest",
    "python.testing.pytestArgs": [
        "unittests"
    ],
    "python.linting.pylintEnabled": true
```
4. Enjoy 🤗

## Contribute
You are very welcome to contribute to this template repository by opening a pull request against the main branch.
