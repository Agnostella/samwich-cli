# SAMWICH CLI

*A sandwich :sandwich: for `sam build`*

SAMWICH CLI is a tool that simplifies working with AWS Serverless Application Model (SAM) deployments, particularly focusing on dependency management and build processes for **Python** Lambda functions and layers.

**Note: This project is in early development and may not be fully functional.**

<!-- ts -->

## Table of Contents

- [Inspiration](#inspiration)
- [Installation](#installation)
- [Requirements](#requirements)
- [Usage](#usage)
  - [Example (with layers)](#example-with-layers)
  - [Example (without layers)](#example-without-layers)
  - [Basic Usage](#basic-usage)
  - [Options](#options)
  - [How It Works](#how-it-works)
  - [Environment Variables](#environment-variables)
- [License](#license)
- [Contributing](#contributing)
  - [Development](#development)
  - [Code Quality](#code-quality)
  <!-- te -->

## Inspiration

Many python projects do not use requirements.txt files, but instead use `pyproject.toml` with `poetry` or `uv`. This tool is designed to help those projects by automatically generating a `requirements.txt` file from the `pyproject.toml` file, and then copying it to the appropriate locations for AWS Lambda functions and layers.

Also, using absolute python imports from the project root is not currently possible with AWS SAM (see https://github.com/aws/aws-sam-cli/issues/6593). This tool helps to maintain a consistent folder structure for your functions and layers, so the lambda functions can be individually packaged with the same folder structure as they are developed.

## Installation

```bash
pipx install samwich-cli
```

## Requirements

- Python 3.9 or higher
- Git (recommended for workspace detection)

## Features

The SAMWICH CLI:

1. Copies your `requirements.txt` file to the appropriate locations for Lambda functions and layers.
2. Executes `sam build` to build your AWS resources.
3. Updates the folder structure of your functions and layers to maintain consistency.

## Example (with layers)

### Project Structure

```
my-project/
├── layer/
│   └── lib/
│       └── utils.py
├── functions/
│   ├── sender/
│   │   └── app.py
│   └── receiver/
│       └── app.py
├── pyproject.toml
└── uv.lock
```

### SAM Template

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: My SAM Application

Resources:
  SenderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: functions.sender.app.lambda_handler
      Runtime: python3.12
      CodeUri: functions/sender/
      Layers:
        - !Ref MyLayer

  ReceiverFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: functions.receiver.app.lambda_handler
      Runtime: python3.12
      CodeUri: functions/receiver/
      Layers:
        - !Ref MyLayer

  MyLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: MyLayer
      ContentUri: layer/
      CompatibleRuntimes:
        - python3.12
      Metadata:
        BuildMethod: python3.12
```

### Resulting Structure

```
.aws-sam/
├── build/
│   ├── SenderFunction/
│   │   └── functions/
│   |       └── sender/
│   |           └── app.py
│   ├── ReceiverFunction/
│   │   └── functions/
│   |       └── receiver/
|   |           └── app.py
│   └── MyLayer/
│       └── python/
│           ├── requirements.txt
│           ├── < project dependencies >
│           └── layer/
│               └── lib/
│                   └── utils.py
```

## Example (without layers)

### Project Structure

```
my-project/
├── functions/
│ ├── sender/
│ │ └── app.py
│ └── receiver/
│ └── app.py
├── pyproject.toml
└── uv.lock
```

### SAM Template

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: My SAM Application
Resources:
  SenderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: functions.sender.app.lambda_handler
      Runtime: python3.12
      CodeUri: functions/sender/

  ReceiverFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: functions.receiver.app.lambda_handler
      Runtime: python3.12
      CodeUri: functions/receiver/
```

### Resulting Structure

```
.aws-sam/
├── build/
│   ├── SenderFunction/
│   │   ├── requirements.txt
│   │   ├── < project dependencies >
│   │   └── functions/
│   |       └── sender/
│   |           └── app.py
│   └── ReceiverFunction/
│       ├── requirements.txt
|       ├── < project dependencies >
|       └── functions/
│           └── receiver/
│               └── app.py
```

### Basic Usage

```bash
uv export \
  --locked \
  --output-file requirements.txt

samwich-cli --requirements-path requirements.txt --template-file template.yaml
```

### Options

- `--requirements-path`: Path to your Python requirements.txt file. Defaults to `requirements.txt` in the current directory.
- `--template-file`: Path to your AWS SAM template file. Defaults to `template.yaml` in the current directory.
- `--debug`: Enable debug logging

## How It Works

SAMWICH CLI performs the following actions:

1. Analyzes your SAM template to identify Lambda functions and layers
2. Copies your requirements.txt file to the appropriate locations
3. Executes `sam build` to build your AWS resources
4. Updates the folder structure of your functions and layers to maintain consistency

## Environment Variables

- `SAMWICH_WORKSPACE`: Override the default workspace root (defaults to git repository root)
- `SAMWICH_TEMP`: Override the default temporary directory.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development

1. Clone the repository
2. Install development dependencies with your package manager of choice
3. Install pre-commit hooks: `pre-commit install`

### Code Quality

This project uses pre-commit hooks for code quality, including:

- Ruff for linting and formatting
- pycln for removing unused imports
- Various pre-commit hooks for file consistency
