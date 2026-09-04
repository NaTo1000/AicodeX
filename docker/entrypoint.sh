#!/usr/bin/env bash
# AicodeX cross-platform run-system entrypoint.
#
# Detects the host OS (Android / Linux / Windows) and launches the app
# accordingly. Intended as the container entrypoint for the run system and as
# a convenience launcher on bare metal.
set -euo pipefail

APP_DIR="${AICODEX_HOME:-/app}"

detect_os() {
  case "$(uname -s 2>/dev/null || echo unknown)" in
    Linux*)
      if [ -n "${ANDROID_ROOT:-}" ] || [ -n "${TERMUX_VERSION:-}" ]; then
        echo "android"
      else
        echo "linux"
      fi
      ;;
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
      echo "windows"
      ;;
    Darwin*)
      echo "macos"
      ;;
    *)
      echo "unknown"
      ;;
  esac
}

main() {
  local os
  os="$(detect_os)"
  echo "AicodeX run system — detected OS: ${os}"

  case "${os}" in
    linux|android|macos)
      exec python "${APP_DIR}/src/main.py" "$@"
      ;;
    windows)
      # Under Git Bash / MSYS the `python` launcher works; fall back to py.
      if command -v python >/dev/null 2>&1; then
        exec python "${APP_DIR}/src/main.py" "$@"
      else
        exec py "${APP_DIR}/src/main.py" "$@"
      fi
      ;;
    *)
      echo "error: unsupported operating system: ${os}" >&2
      exit 1
      ;;
  esac
}

main "$@"
