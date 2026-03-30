#!/bin/bash

set -euo pipefail

TARGET_BRANCH="main"
AUTO_PUSH=0

while [ $# -gt 0 ]; do
    case "$1" in
        --push)
            AUTO_PUSH=1
            ;;
        --branch)
            shift
            TARGET_BRANCH="${1:-main}"
            ;;
        -h|--help)
            cat <<'EOF'
用法：
  bash scripts/sync_upstream.sh
  bash scripts/sync_upstream.sh --push
  bash scripts/sync_upstream.sh --branch main --push

作用：
  1. 拉取 upstream 最新代码
  2. 将 upstream/<branch> 快进合并到本地 <branch>
  3. 可选推送到 origin/<branch>

前提：
  - 当前仓库已配置 upstream 指向源仓库
  - 工作区干净
EOF
            exit 0
            ;;
        *)
            echo "未知参数：$1" >&2
            exit 1
            ;;
    esac
    shift
done

if [ -n "$(git status --porcelain)" ]; then
    echo "工作区有未提交改动，请先提交或暂存。" >&2
    exit 1
fi

if ! git remote get-url upstream >/dev/null 2>&1; then
    echo "未配置 upstream 远程。" >&2
    exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
    echo "未配置 origin 远程。" >&2
    exit 1
fi

current_branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || echo "DETACHED")
if [ "$current_branch" = "DETACHED" ]; then
    echo "当前处于 detached HEAD，无法自动同步。" >&2
    exit 1
fi

if [ "$current_branch" != "$TARGET_BRANCH" ]; then
    echo "当前分支是 $current_branch，正在切换到 $TARGET_BRANCH"
    git checkout "$TARGET_BRANCH"
fi

echo "拉取 upstream/$TARGET_BRANCH ..."
git fetch upstream --prune

echo "尝试快进合并 upstream/$TARGET_BRANCH -> $TARGET_BRANCH ..."
git merge --ff-only "upstream/$TARGET_BRANCH"

echo "本地 $TARGET_BRANCH 已与 upstream/$TARGET_BRANCH 同步。"

if [ "$AUTO_PUSH" -eq 1 ]; then
    echo "推送到 origin/$TARGET_BRANCH ..."
    git push origin "$TARGET_BRANCH"
    echo "已推送到 origin/$TARGET_BRANCH。"
fi
