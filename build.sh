workdir=$(pwd)
TEMP_DIR=$(test -d "${TEMP_DIR}" && echo "${TEMP_DIR}" || mktemp -d)
WORKSPACE_ROOT=$(test -d "${GITHUB_WORKSPACE}" && echo "${GITHUB_WORKSPACE}" || git rev-parse --show-toplevel)
BUILD_DIR="${TEMP_DIR}/build"

pip install aws-sam-cli==1.136.0
poetry self add "poetry-plugin-export@^1.0.0"

pushd "${WORKSPACE_ROOT}"
poetry export \
    --only main \
    --without-urls \
    --format requirements.txt \
    --output "${TEMP_DIR}/requirements.txt" || exit 1
popd

function copy_requirements() {
    target_dir=$1
    mkdir -p "$target_dir"
    cp "${TEMP_DIR}/requirements.txt" "$target_dir/requirements.txt"
}

function determine_relative_lambda_path() {
    lambda_dir=$1

    # Get the relative path from the workspace directory to the lambda directory
    relative_path=$(realpath --relative-to="${WORKSPACE_ROOT}" "$lambda_dir")

    echo "$relative_path"
}

function copy_contents() {
    relative_path=$1

    scratch_dir="${TEMP_DIR}/scratch"
    mkdir "${scratch_dir}"
    cp -r --parents "${relative_path}" "${scratch_dir}"

    rm -rf "${relative_path}"

    mkdir -p "${relative_path}"

    ls -A "${scratch_dir}" | xargs -I {} echo "${scratch_dir}"/{} | xargs -I {} cp -r {} "${relative_path}"
    rm -rf "${scratch_dir}"
}

build_resources=$(python -c '
import json

from samcli.commands._utils import constants
from samcli.commands._utils import options
from samcli.commands.build import build_context
with build_context.BuildContext(
    template_file=options.get_or_default_template_file_name(None, None, options._TEMPLATE_OPTION_DEFAULT_VALUE, include_build=False),
    resource_identifier=None,
    base_dir=None,
    build_dir=constants.DEFAULT_BUILD_DIR,
    cache_dir=constants.DEFAULT_CACHE_DIR,
    cached=False,
    parallel=None,
    mode=None
) as ctx:
    resources = ctx.get_resources_to_build()
print(json.dumps({"layers": " ".join(f.codeuri for f in resources.layers), "functions": " ".join(f.codeuri for f in resources.functions)}))
')

layers=($(echo "$build_resources" | jq -r '.layers'))
fns=($(echo "$build_resources" | jq -r '.functions'))

cd "${WORKSPACE_ROOT}"
for fn in "${fns[@]}"; do
    # Get the relative path from the workspace directory to the lambda directory
    relative_path=$(determine_relative_lambda_path "$fn")

    # Copy the contents of the lambda directory to the build directory
    copy_contents "$relative_path"
done

# If length of layers is one, output poetry to that directory
if [[ ${#layers[@]} -eq 1 ]]; then
    if [[ -d "${layers[0]}" ]]; then
        relative_path=$(determine_relative_lambda_path "${layers[0]}")
        copy_contents "$relative_path"
    else
        mkdir -p "${layers[0]}"
    fi
    copy_requirements "${layers[0]}"
elif [[ ${#layers[@]} -eq 0 ]]; then
    for fn in "${fns[@]}"; do
        copy_requirements "$fn"
    done
else
    echo "::warning:: More than one layer found, skipping poetry export"
fi

cd "${workdir}"

sam build
