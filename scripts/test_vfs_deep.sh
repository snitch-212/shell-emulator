#!/bin/sh
# VFS с 3+ уровнями вложенности: загрузка, сохранение командой
# vfs-save и повторная загрузка сохранённого архива
cd "$(dirname "$0")/.." || exit 1
. ./scripts/env.sh
sh ./run.sh --vfs build/vfs/deep.zip <<'COMMANDS'
vfs-info
vfs-save build/deep-copy.zip
exit
COMMANDS
echo "exit code: $?"
echo "=== reload saved copy ==="
sh ./run.sh --vfs build/deep-copy.zip <<'COMMANDS'
vfs-info /projects
exit
COMMANDS
echo "exit code: $?"
