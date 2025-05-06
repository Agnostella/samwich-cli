# SAMWICH CLI

_A sandwich :sandwich: for `sam build`_

SAMWICH CLI is a tool that simplifies working with AWS Serverless Application Model (SAM) deployments, particularly focusing on dependency management and build processes for **Python** Lambda functions and layers.

<!-- ts -->

## Table of Contents

- [Inspiration](#inspiration)
- [Installation](#installation)
- [Requirements](#requirements)
- [Features](#features)
- [Basic Usage](#basic-usage)
- [Examples and Advanced Usage](#examples-and-advanced-usage)
- [License](#license)
- [Contributing](#contributing)
- [Development](#development)
- [Code Quality](#code-quality)

<!-- te -->

## Inspiration

Many python projects do not use requirements.txt files, but instead use `pyproject.toml` with `poetry` or `uv`. This tool is designed to help those projects by copying the generated requirements.txt to the appropriate locations for AWS Lambda functions and layers.

Also, using absolute python imports from the project root is not currently possible with AWS SAM (see https://github.com/aws/aws-sam-cli/issues/6593). This tool helps to maintain a consistent folder structure for your functions and layers, so the lambda functions can be individually packaged with the same folder structure as they are developed.

## Installation

```bash
pipx install samwich-cli
```

## Requirements

- Python 3.9 or higher

## Features

The SAMWICH CLI:

1. Copies your `requirements.txt` file to the appropriate locations for Lambda functions and layers.
2. Executes `sam build` to build your AWS resources.
3. Updates the folder structure of your functions and layers to maintain consistency.

## Basic Usage

```bash
samwich-cli --requirements requirements.txt --template-file template.yaml
```

### Options

- `--template-file`: Path to yours AWS SAM template file. Defaults to `template.yaml` in the current directory.
- `--requirements`: Path to your Python requirements.txt file. Defaults to `requirements.txt` in the current directory.
- `--workspace-root`: Path to the workspace root.
- `--source-dir`: Path to the source directory for the code. When restructuring, only the child paths of this directory will be included.
- `--sam-args`: Additional arguments to pass to `sam build`. For example, `--sam-args "--debug --use-container"`.
- `--debug`: Enable debug logging

### Environment Variables

All options can also be set using environment variables. The environment variable names are the same as the option names, but prefixed with `SAMWICH`, in uppercase, and with underscores instead of dashes. For example, `--template-file` can be set using the `SAMWICH_TEMPLATE_FILE` environment variable.

## Examples and Advanced Usage

Open the [docs](docs/) folder for examples and detailed usage.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development

Refer to the [Justfile](./Justfile) for development tasks. It is recommended to `pipx install rust-just` to run the tasks but you can also copy the commands from the Justfile and run them manually.

### Code Quality

This project uses `pre-commit` hooks for code quality, including:

- `ruff` for linting and formatting
- `pycln` for removing unused imports
- Various `pre-commit` hooks for file consistency
