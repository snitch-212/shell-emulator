#!/bin/sh
# Минимальная VFS: архив с одним файлом
cd "$(dirname "$0")/.." || exit 1
. ./scripts/env.sh
sh ./run.sh --vfs build/vfs/minimal.zip <<'COMMANDS'
vfs-info
exit
COMMANDS
echo "exit code: $?"
