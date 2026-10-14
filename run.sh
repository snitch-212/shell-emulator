#!/bin/sh
# Запуск эмулятора: ./run.sh [параметры эмулятора]
DIR=$(cd "$(dirname "$0")" && pwd)
# Выбор интерпретатора: python3 (Linux, macOS) или python (Windows)
for PYTHON in python3 python; do
    "$PYTHON" -c "" > /dev/null 2>&1 && break
done
# Тестовые VFS-архивы создаются при первом запуске (с этапа 3)
if [ -f "$DIR/tools/make_vfs.py" ] && [ ! -f "$DIR/build/vfs/deep.zip" ]; then
    "$PYTHON" "$DIR/tools/make_vfs.py" "$DIR/build/vfs" > /dev/null
fi
PYTHONPATH="$DIR/src${PYTHONPATH:+:$PYTHONPATH}" exec "$PYTHON" -m shell_emulator "$@"
