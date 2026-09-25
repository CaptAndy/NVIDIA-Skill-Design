#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="${SCREEN_ASSISTANCE_RUNTIME:-$HOME/screen-assistance-runtime}"
image_id='sha256:9b2b3cb4d201e48efac830e8b1fd4d5f057be394def6f11cce50f3691d2f8e6a'
image_ref='vllm/vllm-openai@sha256:09532aaa219c2cb459dba6690d4aef3feafefff6299460fb3f0097ff5ddaf4d1'
test "$(uname -m)" = aarch64 || { echo 'This lock targets ARM64 Spark'; exit 1; }
python3 "$script_dir/manifest.py" verify "$project_dir/models/Step3-VL-10B" "$script_dir/model-lock.json"
python3 "$script_dir/prepare_tokenizer.py" "$project_dir/models/Step3-VL-10B" "$project_dir/runtime-config/tokenizer_config.json"
if ! docker image inspect "$image_id" >/dev/null 2>&1; then
  docker pull --platform linux/arm64 "$image_ref"
  test "$(docker image inspect "$image_ref" --format '{{.Id}}')" = "$image_id"
fi
config_hash="$(cat "$script_dir/start-spark.sh" "$project_dir/runtime-config/tokenizer_config.json" | sha256sum | cut -d ' ' -f 1)"
if docker container inspect screen-assistance-vlm >/dev/null 2>&1; then
  existing="$(docker inspect screen-assistance-vlm --format '{{index .Config.Labels "org.screen-assistance.config"}}')"
  test "$existing" = "$config_hash" || { echo 'Existing project container uses different configuration; inspect and replace explicitly, preserving rollback.'; exit 2; }
  test "$(docker inspect screen-assistance-vlm --format '{{.State.Status}}')" = running || { echo 'Matching container is stopped; start it explicitly.'; exit 3; }
  curl --fail --silent --max-time 5 http://127.0.0.1:18000/health >/dev/null
  echo 'Matching service is healthy'; exit 0
fi
mkdir -p "$project_dir/runtime-cache"
network='screen-assistance-isolated-v3'
if ! docker network inspect "$network" >/dev/null 2>&1; then
  docker network create --internal --label org.screen-assistance.owner=security-v3 "$network"
fi
test "$(docker network inspect "$network" --format '{{.Internal}}')" = true
test "$(docker network inspect "$network" --format '{{index .Labels "org.screen-assistance.owner"}}')" = security-v3
docker run -d --name screen-assistance-vlm --gpus all --shm-size 4g \
  --network "$network" --dns 127.0.0.1 \
  --user "$(id -u):$(id -g)" --cap-drop ALL --security-opt no-new-privileges \
  --read-only --tmpfs /tmp:rw,nosuid,size=4g --pids-limit 1024 \
  --label "org.screen-assistance.config=$config_hash" \
  -p 127.0.0.1:18000:8000 \
  -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
  -e HOME=/tmp -e XDG_CACHE_HOME=/cache -e HF_HOME=/cache/huggingface \
  -e USER=screen-assistance -e LOGNAME=screen-assistance -e TORCHINDUCTOR_CACHE_DIR=/cache/inductor \
  -e TORCH_HOME=/cache/torch -e TRITON_CACHE_DIR=/cache/triton \
  -v "$project_dir/models/Step3-VL-10B:/model:ro" \
  -v "$project_dir/runtime-config/tokenizer_config.json:/model/tokenizer_config.json:ro" \
  -v "$project_dir/runtime-cache:/cache" \
  --entrypoint vllm "$image_id" \
  serve /model --served-model-name screen-assistance-vlm \
  --host 0.0.0.0 --port 8000 --trust-remote-code --dtype bfloat16 \
  --max-model-len 8192 --max-num-seqs 1 --gpu-memory-utilization 0.45 \
  --enforce-eager --reasoning-parser deepseek_r1
echo 'Started; run check-spark.sh after model initialization.'
