#!/usr/bin/env bash
# MLflow UI on the machine's local DB (~/.mlflow/mlflow.db), in the background.
# Usage: mlflow_ui.sh [start|stop|status|restart] [--port N] [--lab N]
set -u
repo="$(cd "$(dirname "$0")/../../../.." && pwd)"
home="$HOME/.mlflow"
pidfile="$home/ui.pid"
logfile="$home/ui.log"
port=5050   # 5000 is taken by AirPlay Receiver on macOS
lab=""

cmd="${1:-start}"
[ $# -gt 0 ] && shift
while [ $# -gt 0 ]; do
  case "$1" in
    --port) port="$2"; shift 2 ;;
    --lab) lab="lab-${2#lab-}"; shift 2 ;;
    *) echo "Unknown argument: $1"; exit 2 ;;
  esac
done

running() { [ -f "$pidfile" ] && kill -0 "$(cut -d' ' -f1 "$pidfile")" 2>/dev/null; }

stop() {
  if running; then
    kill "$(cut -d' ' -f1 "$pidfile")" && echo "Stopped (pid $(cut -d' ' -f1 "$pidfile"))"
  else
    echo "Not running"
  fi
  rm -f "$pidfile"
}

start() {
  if running; then
    echo "Already running: http://127.0.0.1:$(cut -d' ' -f2 "$pidfile")"
    return 0
  fi
  mkdir -p "$home"
  # mlflow comes from a lab's uv env: given lab, else the newest lab-N with a .venv
  if [ -z "$lab" ]; then
    lab=$(cd "$repo" && ls -d lab-*/.venv 2>/dev/null | sort -V | tail -1 | cut -d/ -f1)
  fi
  if [ -z "$lab" ] || [ ! -d "$repo/$lab" ]; then
    echo "No lab with an env: run 'uv sync' in lab-N first"; exit 1
  fi
  if lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $port is busy: use --port N"; exit 1
  fi
  cd "$repo/$lab" || exit 1
  nohup uv run mlflow ui --backend-store-uri "sqlite:///$home/mlflow.db" \
    --host 127.0.0.1 --port "$port" >"$logfile" 2>&1 &
  echo "$! $port" >"$pidfile"
  for _ in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:$port/health" >/dev/null 2>&1; then
      echo "Started ($lab env): http://127.0.0.1:$port"
      return 0
    fi
    sleep 1
  done
  echo "Did not come up in 30 s, see $logfile"; tail -5 "$logfile"; rm -f "$pidfile"; exit 1
}

case "$cmd" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status)
    if running; then echo "Running: http://127.0.0.1:$(cut -d' ' -f2 "$pidfile")"; else echo "Not running"; fi ;;
  *) echo "Usage: mlflow_ui.sh [start|stop|status|restart] [--port N] [--lab N]"; exit 2 ;;
esac
