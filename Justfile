set shell := ["bash", "-uc"]
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

python_compatible := if `python --version` =~ '3\.(9|1\d)\.\d+$' { "true" } else { error("Python 3.9 or higher is required") }

alias h := help

help:
    @just --list

# Install the required dependencies for the project and set up the pre-commit hooks
setup:
    python -m pip install --upgrade pip pipx
    python -m pipx install uv pre-commit
    pre-commit install --install-hooks
    uv sync

# Update uv dependencies and pre-commit hooks and run all pre-commit hooks on all files
update: && pre-commit
    uv lock --upgrade
    pre-commit autoupdate

pre-commit:
    pre-commit run --all-files

pytest:
    uv run pytest tests

lint: pre-commit pytest
