#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/config/vrx-2019.env"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. OrbStack provides the Docker-compatible engine on macOS." >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "The Docker engine is not reachable. Start OrbStack, then retry." >&2
  exit 1
fi

compose=(docker compose --env-file "${ENV_FILE}" -f "${ROOT_DIR}/compose.yaml")
mkdir -p "${ROOT_DIR}/artifacts"
"${compose[@]}" config --quiet

case "${1:-up}" in
  --build-only)
    "${compose[@]}" build --pull simulator
    ;;
  --down)
    "${compose[@]}" down
    ;;
  up)
    "${compose[@]}" build --pull simulator
    "${compose[@]}" up --detach --wait simulator
    "${compose[@]}" ps
    ;;
  *)
    echo "Usage: $0 [up|--build-only|--down]" >&2
    exit 2
    ;;
esac
