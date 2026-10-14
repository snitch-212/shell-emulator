# Подключается скриптами проверки (. ./scripts/env.sh): создаёт тестовые VFS
for PYTHON in python3 python; do
    "$PYTHON" -c "" > /dev/null 2>&1 && break
done
"$PYTHON" tools/make_vfs.py build/vfs > /dev/null
