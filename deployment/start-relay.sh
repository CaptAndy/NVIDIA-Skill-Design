#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
image='sha256:9b2b3cb4d201e48efac830e8b1fd4d5f057be394def6f11cce50f3691d2f8e6a'
target="$(docker inspect screen-assistance-vlm --format '{{(index .NetworkSettings.Networks "screen-assistance-isolated-v3").IPAddress}}')"
test -n "$target"
if docker container inspect screen-assistance-relay >/dev/null 2>&1; then
  docker inspect screen-assistance-relay | python3 -c 'import json,sys; c=json.load(sys.stdin)[0]; assert c["State"]["Running"]; assert c["Image"]==sys.argv[2]; assert c["Config"]["Labels"].get("org.screen-assistance.owner")=="security-v3"; assert c["Config"]["Cmd"]==["/relay.py","--target",sys.argv[1]]; assert c["HostConfig"]["NetworkMode"]=="host"; assert c["HostConfig"]["ReadonlyRootfs"]; assert c["HostConfig"]["CapDrop"]==["ALL"]; print("Matching relay is running")' "$target" "$image"
  exit 0
fi
docker run -d --name screen-assistance-relay --network host --user "$(id -u):$(id -g)" \
  --cap-drop ALL --security-opt no-new-privileges --read-only --pids-limit 64 \
  --label org.screen-assistance.owner=security-v3 \
  -v "$script_dir/loopback_relay.py:/relay.py:ro" --entrypoint python3 "$image" /relay.py --target "$target"
