#!/bin/sh
# Проверка всех параметров командной строки вместе, справки
# и неизвестного параметра
cd "$(dirname "$0")/.." || exit 1
. ./scripts/env.sh
echo "=== --vfs and --script together ==="
sh ./run.sh --vfs build/vfs/deep.zip --script examples/exit_code.txt
echo "exit code: $?"
echo "=== --help ==="
sh ./run.sh --help
echo "exit code: $?"
echo "=== unknown parameter ==="
sh ./run.sh --colour red < /dev/null
echo "exit code: $?"
