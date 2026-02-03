#!/usr/bin/env bash
# docker-sandbox.sh — Dexter Refinery Isolation Wrapper v0.2
# Usage: ./docker-sandbox.sh [run|stop|logs|shell]

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONTAINER_NAME="dexter-refinery"
CONFIG_PATH="/workspace/config/heartbeat.yaml"

case "${1:-run}" in
  run)
    echo "[dexter] Starting Docker sandbox: $CONTAINER_NAME"
    
    # v0.2 Explicit Pattern:
    # - Volume mount ensures beads/THEORY.md survive restarts
    # - supervisor.py inside handles crash recovery with backoff
    # - Injection guard runs OUTSIDE sandbox (pre-filter)
    
    docker sandbox run --name "$CONTAINER_NAME" \
      --mount type=bind,source="$SCRIPT_DIR",target=/workspace \
      --restart unless-stopped \
      python /workspace/core/loop.py --config "$CONFIG_PATH"
    
    echo "[dexter] Sandbox started. Logs: ./docker-sandbox.sh logs"
    ;;
    
  stop)
    echo "[dexter] Stopping Docker sandbox: $CONTAINER_NAME"
    docker stop "$CONTAINER_NAME" 2>/dev/null || echo "[dexter] Container not running."
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    echo "[dexter] Sandbox stopped."
    ;;
    
  logs)
    echo "[dexter] Tailing logs for: $CONTAINER_NAME"
    docker logs -f "$CONTAINER_NAME"
    ;;
    
  shell)
    echo "[dexter] Opening shell in: $CONTAINER_NAME"
    docker exec -it "$CONTAINER_NAME" /bin/bash
    ;;
    
  status)
    echo "[dexter] Checking status of: $CONTAINER_NAME"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ;;
    
  *)
    echo "Dexter Docker Sandbox Wrapper v0.2"
    echo ""
    echo "Usage: $0 {run|stop|logs|shell|status}"
    echo ""
    echo "Commands:"
    echo "  run     Start the Dexter refinery in Docker sandbox"
    echo "  stop    Stop and remove the sandbox container"
    echo "  logs    Tail container logs"
    echo "  shell   Open interactive shell in container"
    echo "  status  Show container status"
    echo ""
    echo "Supervisor pattern:"
    echo "  - supervisor.py watches loop.py inside sandbox"
    echo "  - On crash: restart with backoff (1s, 2s, 4s, max 60s)"
    echo "  - Health check: heartbeat ping every 60s"
    echo "  - Volume mount preserves beads/THEORY.md across restarts"
    exit 1
    ;;
esac
