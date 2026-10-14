#!/bin/sh
# VFS из нескольких файлов, включая двоичный (хранится в base64)
cd "$(dirname "$0")/.." || exit 1
. ./scripts/env.sh
sh ./run.sh --vfs build/vfs/multi.zip <<'COMMANDS'
vfs-info
exit
COMMANDS
echo "exit code: $?"
