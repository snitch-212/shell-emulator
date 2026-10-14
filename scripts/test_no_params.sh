#!/bin/sh
# Запуск эмулятора без параметров (ввод пуст — сразу EOF)
cd "$(dirname "$0")/.." || exit 1
echo "=== no parameters ==="
sh ./run.sh < /dev/null
echo "exit code: $?"
