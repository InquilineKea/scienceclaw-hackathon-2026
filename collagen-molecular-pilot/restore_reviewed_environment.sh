#!/usr/bin/env bash
# Restore the reviewed environment on the newly authorized H100. No installers.
set -euo pipefail
cd -- "$(dirname -- "$0")"
DOCKER=(docker)
if ! docker info >/dev/null 2>&1; then
  sudo -n docker info >/dev/null
  DOCKER=(sudo -n docker)
fi
sha256sum -c reviewed-environment.sha256
printf '4842c52ad210d6e1f84d6cf1ffa70fae25a7e0d755ed55cf223f43913f587db7  MACE-OFF23_medium.model\n' | sha256sum -c -
image='python@sha256:78c6833ca878fd221957db5d580f7f2e9e31265b38656e97368caf23f12e24c8'
"${DOCKER[@]}" pull "$image"
"${DOCKER[@]}" volume create oxt-alchemi-venv
"${DOCKER[@]}" volume create oxt-cache
# Dedicated new volumes on the newly-created instance, not the original L4.
"${DOCKER[@]}" run --rm --pull never --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 64 --memory 2g --cpus 2 \
  --mount "type=bind,src=$(pwd)/reviewed-environment.tar.gz,dst=/input/environment.tar.gz,readonly" \
  --mount type=volume,src=oxt-alchemi-venv,dst=/restore \
  "$image" /bin/tar -xzf /input/environment.tar.gz -C /restore --no-same-owner --no-same-permissions
"${DOCKER[@]}" run --rm --pull never --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 64 --memory 256m --cpus 1 \
  --mount "type=bind,src=$(pwd)/MACE-OFF23_medium.model,dst=/input/model,readonly" \
  --mount type=volume,src=oxt-cache,dst=/models \
  "$image" /bin/sh -c 'mkdir -p /models/mace && cp /input/model /models/mace/MACE-OFF23_medium.model'
"${DOCKER[@]}" image inspect "$image" --format '{{.Id}} {{json .RepoDigests}}'
