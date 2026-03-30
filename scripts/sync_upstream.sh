#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PARENT_SCRIPT="$PROJECT_ROOT/../sync_upstream_repos.sh"

if [ ! -f "$PARENT_SCRIPT" ]; then
    echo "未找到上级目录脚本：$PARENT_SCRIPT" >&2
    echo "请从上级目录统一维护 sync_upstream_repos.sh。" >&2
    exit 1
fi

exec bash "$PARENT_SCRIPT" "$PROJECT_ROOT" "$@"
