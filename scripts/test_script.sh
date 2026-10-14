#!/bin/sh
# Проверка параметра --script: успешный скрипт, exit из скрипта,
# отсутствующий файл скрипта
cd "$(dirname "$0")/.." || exit 1
echo "=== --script with comments and errors ==="
sh ./run.sh --script examples/stage2.txt < /dev/null
echo "exit code: $?"
echo "=== --script with exit 3 ==="
sh ./run.sh --script examples/exit_code.txt < /dev/null
echo "exit code: $?"
echo "=== --script: file does not exist ==="
sh ./run.sh --script examples/missing.txt < /dev/null
echo "exit code: $?"
