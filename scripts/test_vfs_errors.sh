#!/bin/sh
# Ошибки загрузки VFS и VFS по умолчанию
cd "$(dirname "$0")/.." || exit 1
. ./scripts/env.sh
echo "=== file not found ==="
sh ./run.sh --vfs build/vfs/missing.zip < /dev/null
echo "exit code: $?"
echo "=== not a ZIP archive ==="
sh ./run.sh --vfs build/vfs/broken.zip < /dev/null
echo "exit code: $?"
echo "=== directory instead of archive ==="
sh ./run.sh --vfs build/vfs < /dev/null
echo "exit code: $?"
echo "=== no --vfs: default VFS in memory ==="
sh ./run.sh <<'COMMANDS'
vfs-info
exit
COMMANDS
echo "exit code: $?"
