"""Генерация тестовых VFS-архивов в каталог build/vfs.

Архивы не хранятся в репозитории (это артефакты сборки), а создаются
этим скриптом: python tools/make_vfs.py [каталог]

* minimal.zip — минимальная VFS: один файл;
* multi.zip   — несколько файлов, в том числе двоичный;
* deep.zip    — не менее 3 уровней вложенности файлов и каталогов;
* broken.zip  — файл, не являющийся ZIP-архивом (для проверки ошибок).
"""

import os
import stat
import sys
import zipfile

DATE = (2026, 9, 14, 12, 0, 0)
ATTR_SHIFT = 16
PNG_HEADER = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
BINARY_DATA = PNG_HEADER + bytes(range(256))

MINIMAL = {
    "hello.txt": (0o644, "Hello from the minimal VFS!\n"),
}

MULTI = {
    "readme.txt": (0o644, "VFS with several files.\n"),
    "access.log": (0o640, "GET /\nGET /\nGET /about\nget /about\n"
                          "GET /about\nPOST /login\nGET /\n"),
    "colors.txt": (0o644, "red\nred\ngreen\nblue\nblue\nblue\n"),
    "logo.png": (0o644, BINARY_DATA),
    "build.sh": (0o755, "#!/bin/sh\necho build\n"),
}

DEEP = {
    "home/": (0o755, None),
    "home/student/notes.txt": (0o600, "Level 3 file\n"),
    "home/student/.profile": (0o644, "export EDITOR=nano\n"),
    "home/student/projects/": (0o755, None),
    "projects/app/src/main.py": (0o644, "print('hello')\n"),
    "projects/app/src/utils/helpers.py": (0o644, "def f():\n    pass\n"),
    "projects/app/docs/guide.md": (0o644, "# Guide\n"),
    "projects/app/run.sh": (0o755, "#!/bin/sh\npython3 src/main.py\n"),
    "projects/app/assets/icon.bin": (0o644, BINARY_DATA),
    "var/log/syslog": (0o640, "boot\nboot\nstart\nstart\nstart\nstop\n"),
    "var/log/access.log": (0o640, "GET /\nget /\nGET /\nPOST /login\n"
                                  "post /login\nGET /about\n"),
    "etc/motd": (0o644, "Welcome to the deep VFS\n"),
}


def write_archive(path, entries):
    """Записать ZIP-архив с заданными элементами и правами доступа."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, (mode, data) in entries.items():
            info = zipfile.ZipInfo(name, DATE)
            kind = stat.S_IFDIR if name.endswith("/") else stat.S_IFREG
            info.external_attr = (kind | mode) << ATTR_SHIFT
            if isinstance(data, str):
                data = data.encode("utf-8")
            archive.writestr(info, data or b"")


def main(target):
    """Создать все тестовые архивы в каталоге ``target``."""
    os.makedirs(target, exist_ok=True)
    for name, entries in (("minimal", MINIMAL), ("multi", MULTI),
                          ("deep", DEEP)):
        path = os.path.join(target, f"{name}.zip")
        write_archive(path, entries)
        print(f"created {path}")
    broken = os.path.join(target, "broken.zip")
    with open(broken, "w", encoding="utf-8") as file:
        file.write("this is not a ZIP archive\n")
    print(f"created {broken}")


if __name__ == "__main__":
    main((sys.argv[1:] or [os.path.join("build", "vfs")])[0])
