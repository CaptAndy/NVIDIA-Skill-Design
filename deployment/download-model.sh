#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="${SCREEN_ASSISTANCE_RUNTIME:-$HOME/screen-assistance-runtime}"
image_id='sha256:9b2b3cb4d201e48efac830e8b1fd4d5f057be394def6f11cce50f3691d2f8e6a'
image_ref='vllm/vllm-openai@sha256:09532aaa219c2cb459dba6690d4aef3feafefff6299460fb3f0097ff5ddaf4d1'
if python3 "$script_dir/manifest.py" verify "$project_dir/models/Step3-VL-10B" "$script_dir/model-lock.json"; then exit 0; fi
if test -d "$project_dir/models/Step3-VL-10B"; then echo 'Existing model does not match lock; preserve it and choose a new SCREEN_ASSISTANCE_RUNTIME directory.'; exit 2; fi
if ! docker image inspect "$image_id" >/dev/null 2>&1; then
 docker pull --platform linux/arm64 "$image_ref"
 test "$(docker image inspect "$image_ref" --format '{{.Id}}')" = "$image_id"
fi
mkdir -p "$project_dir/models" "$project_dir/download-cache"
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
 -v "$project_dir/download-cache:/models" --entrypoint python3 "$image_id" \
 -c 'from modelscope.hub.snapshot_download import snapshot_download; snapshot_download("stepfun-ai/Step3-VL-10B",revision="master",local_dir="/models/Step3-VL-10B",max_workers=2)'
# Upstream master is mutable. Only the exact locked bytes are accepted.
python3 "$script_dir/prepare_model.py" "$project_dir/download-cache/Step3-VL-10B" "$project_dir/models/Step3-VL-10B" "$script_dir/model-lock.json"
python3 "$script_dir/manifest.py" verify "$project_dir/models/Step3-VL-10B" "$script_dir/model-lock.json"
