# Examples and Advanced Usage

## CLI Examples

Install `just` (`pipx install rust-just`) and refer to the [Justfile](./Justfile).

## Example (with layers)

This example excludes the src path segment from the build using the --source-dir option.

### Project Structure

```
my-project/
├── src/
│   ├── lib/
│   │    └── utils.py
│   ├── sender/
│   │   └── app.py
│   └── receiver/
│       └── app.py
├── pyproject.toml
├── template.yaml
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
      Handler: sender.app.lambda_handler
      Runtime: python3.12
      CodeUri: src/sender/
      Layers:
        - !Ref MyLayer

  ReceiverFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: receiver.app.lambda_handler
      Runtime: python3.12
      CodeUri: src/receiver/
      Layers:
        - !Ref MyLayer

  MyLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: MyLayer
      ContentUri: lib/
      CompatibleRuntimes:
        - python3.12
      Metadata:
        BuildMethod: python3.12
```

### SAMWICH CLI

```bash
uv export \
  --locked \
  --output-file requirements.txt
samwich-cli --source-dir src --sam-args "--cached"
```

### Resulting Structure

```
.aws-sam/
├── build/
│   ├── SenderFunction/
│   │   └── sender/
│   |       └── app.py
│   ├── ReceiverFunction/
│   │   └── receiver/
|   |       └── app.py
│   └── MyLayer/
│       └── python/
│           ├── requirements.txt
│           ├── < project dependencies >
│           └── lib/
│               └── utils.py
```

## Example (without layers)

### Project Structure

```
my-project/
├── src/
│   ├── sender/
│   │   └── app.py
│   └── receiver/
│       └── app.py
├── pyproject.toml
├── template.yaml
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
      Handler: src.sender.app.lambda_handler
      Runtime: python3.12
      CodeUri: src/sender/

  ReceiverFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src.receiver.app.lambda_handler
      Runtime: python3.12
      CodeUri: src/receiver/
```

### Resulting Structure

```
.aws-sam/
├── build/
│   ├── SenderFunction/
│   │   ├── requirements.txt
│   │   ├── < project dependencies >
│   │   └── src/
│   |       └── sender/
│   |           └── app.py
│   └── ReceiverFunction/
│       ├── requirements.txt
|       ├── < project dependencies >
|       └── src/
│           └── receiver/
│               └── app.py
```
