#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 "$script_dir/verify-security.py"
docker inspect screen-assistance-vlm | python3 -c 'import sys,json; c=json.load(sys.stdin)[0]; assert c["State"]["Running"],"not running"; p=c["HostConfig"]["PortBindings"]; assert p=={"8000/tcp":[{"HostIp":"127.0.0.1","HostPort":"18000"}]},"unexpected binding"; print("running; loopback only")'
curl --fail --silent --max-time 5 http://127.0.0.1:18000/health >/dev/null
curl --fail --silent --max-time 5 http://127.0.0.1:18000/v1/models | python3 -c 'import json,sys; a=json.load(sys.stdin); assert any(x["id"]=="screen-assistance-vlm" for x in a["data"]); print("health and model identity OK")'
