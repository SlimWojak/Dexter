#!/usr/bin/env bash
# docker-sandbox.sh — Dexter Refinery Isolation Wrapper v0.2
# Usage: ./docker-sandbox.sh [run|stop|logs|shell|status]
#
# Fallback: standard docker run with isolation flags.
# docker sandbox run (Docker Desktop AI agent feature) uses a different API
# that doesn't support --mount/--restart; using docker run instead.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CONTAINER_NAME="dexter-refinery"
IMAGE="python:3.11-slim"
CONFIG_PATH="/workspace/config/heartbeat.yaml"

case "${1:-run}" in
  run)
    echo "[dexter] Starting container: $CONTAINER_NAME"

    # Stop existing if running
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

    # Install deps then run supervisor which manages loop.py
    docker run -d \
      --name "$CONTAINER_NAME" \
      --restart unless-stopped \
      --network none \
      -v "$SCRIPT_DIR:/workspace:rw" \
      -w /workspace \
      "$IMAGE" \
      bash -c "pip install --quiet -r /workspace/requirements.txt && python -u /workspace/core/supervisor.py --config $CONFIG_PATH"

    echo "[dexter] Container started. Logs: ./docker-sandbox.sh logs"
    ;;

  stop)
    echo "[dexter] Stopping container: $CONTAINER_NAME"
    docker stop "$CONTAINER_NAME" 2>/dev/null || echo "[dexter] Container not running."
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    echo "[dexter] Stopped."
    ;;

  logs)
    docker logs -f "$CONTAINER_NAME"
    ;;

  shell)
    docker exec -it "$CONTAINER_NAME" /bin/bash
    ;;

  status)
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ;;

  *)
    echo "Dexter Docker Sandbox Wrapper v0.2"
    echo ""
    echo "Usage: $0 {run|stop|logs|shell|status}"
    echo ""
    echo "Commands:"
    echo "  run     Start the Dexter refinery in isolated container"
    echo "  stop    Stop and remove the container"
    echo "  logs    Tail container logs"
    echo "  shell   Open interactive shell in container"
    echo "  status  Show container status"
    exit 1
    ;;
esac
