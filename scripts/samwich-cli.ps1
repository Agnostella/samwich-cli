# Set up environment
$env:PYTHONPATH = (Get-Location).Path
$script_dir = $PSScriptRoot
$script_path = Join-Path -Path $script_dir -ChildPath "entrypoint.py"

# Run the Python script with all arguments
python $script_path $args
