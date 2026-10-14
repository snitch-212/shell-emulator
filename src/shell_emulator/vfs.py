"""Виртуальная файловая система (VFS), полностью хранящаяся в памяти.

Источник VFS — ZIP-архив. Архив читается в память целиком и на диске
не изменяется; сохранить состояние можно только явно (vfs-save).
Текстовые файлы хранятся как строки, двоичные — в кодировке base64.
"""

import base64
import io
import stat
import time
import zipfile
import zlib

from .errors import ShellError

DEFAULT_DIR_MODE = 0o755
DEFAULT_FILE_MODE = 0o644
PERMISSION_MASK = 0o777
ZIP_ATTR_SHIFT = 16
MSDOS_DIR_FLAG = 0x10
MIN_ZIP_YEAR = 1980
ZIP_DATE_FIELDS = 6
TIME_TUPLE_TAIL = (0, 0, -1)
READ = 0o400
WRITE = 0o200
EXECUTE = 0o100


class VfsError(ShellError):
    """Ошибка загрузки или сохранения VFS."""


class VfsNode:
    """Общая часть файла и каталога: имя, права, время изменения."""

    is_dir = False

    def __init__(self, name, mode, mtime=None):
        """Создать узел с именем, правами доступа и временем."""
        self.name = name
        self.mode = mode & PERMISSION_MASK
        self.mtime = time.time() if mtime is None else mtime
        self.parent = None

    def path(self):
        """Вернуть абсолютный путь узла внутри VFS."""
        parts = []
        node = self
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))


class VfsFile(VfsNode):
    """Файл VFS; двоичное содержимое хранится в base64."""

    def __init__(self, name, data=b"", mode=DEFAULT_FILE_MODE, mtime=None):
        """Создать файл с содержимым ``data`` (bytes)."""
        super().__init__(name, mode, mtime)
        self.content = ""
        self.binary = False
        self.set_bytes(data)

    def set_bytes(self, data):
        """Сохранить содержимое: текст как есть, двоичное — в base64."""
        try:
            self.content = data.decode("utf-8")
            self.binary = False
        except UnicodeDecodeError:
            self.content = base64.b64encode(data).decode("ascii")
            self.binary = True

    def to_bytes(self):
        """Вернуть исходное содержимое файла в виде bytes."""
        if self.binary:
            return base64.b64decode(self.content)
        return self.content.encode("utf-8")

    def size(self):
        """Вернуть размер файла в байтах."""
        return len(self.to_bytes())


class VfsDir(VfsNode):
    """Каталог VFS, содержащий словарь дочерних узлов."""

    is_dir = True

    def __init__(self, name, mode=DEFAULT_DIR_MODE, mtime=None):
        """Создать пустой каталог."""
        super().__init__(name, mode, mtime)
        self.children = {}

    def add(self, node):
        """Добавить дочерний узел и вернуть его."""
        node.parent = self
        self.children[node.name] = node
        return node


class Vfs:
    """Дерево VFS, текущий и домашний каталоги."""

    def __init__(self, root=None, source=None, home="/"):
        """Создать VFS; ``source`` — путь к архиву или None."""
        self.root = root or VfsDir("")
        self.source = source
        self.home = home
        self.previous = None
        try:
            self.cwd = self.resolve(home)
        except ShellError:
            self.home = "/"
            self.cwd = self.root

    def resolve(self, path):
        """Найти узел по абсолютному или относительному пути.

        :raises ShellError: если путь не существует
        """
        if path == "~" or path.startswith("~/"):
            path = self.home + path[1:]
        node = self.root if path.startswith("/") else self.cwd
        for part in path.split("/"):
            node = _step(node, part, path)
        return node

    def walk(self, node=None):
        """Обойти дерево в глубину, выдавая все узлы."""
        node = node or self.root
        yield node
        if node.is_dir:
            for child in sorted(node.children.values(),
                                key=lambda item: item.name):
                yield from self.walk(child)


def check_access(node, permission, path):
    """Проверить право владельца (READ, WRITE, EXECUTE) на узел.

    :raises ShellError: если право отсутствует
    """
    if not node.mode & permission:
        raise ShellError(f"{path}: Permission denied")


def _step(node, part, path):
    """Сделать один шаг по пути от узла ``node``."""
    if part in ("", "."):
        return node
    if not node.is_dir:
        raise ShellError(f"{path}: Not a directory")
    if part == "..":
        return node.parent or node
    check_access(node, EXECUTE, path)
    child = node.children.get(part)
    if child is None:
        raise ShellError(f"{path}: No such file or directory")
    return child


def make_dirs(root, parts, mtime=None):
    """Создать (при необходимости) цепочку каталогов и вернуть последний.

    :raises VfsError: если на пути встретился файл
    """
    node = root
    for part in parts:
        child = node.children.get(part)
        if child is None:
            child = node.add(VfsDir(part, mtime=mtime))
        elif not child.is_dir:
            raise VfsError(f"'{part}' is both a file and a directory")
        node = child
    return node


def load_zip(path, home="/"):
    """Загрузить VFS из ZIP-архива, не изменяя его на диске.

    :raises VfsError: файл не найден, не читается или не ZIP-архив
    """
    try:
        with open(path, "rb") as file:
            data = file.read()
        root = _read_archive(data)
    except OSError as exc:
        raise VfsError(f"cannot load VFS '{path}': {exc.strerror}") \
            from None
    except (zipfile.BadZipFile, VfsError, EOFError, zlib.error,
            RuntimeError, NotImplementedError) as exc:
        raise VfsError(f"cannot load VFS '{path}': invalid format "
                       f"({exc})") from None
    return Vfs(root, source=path, home=home)


def _read_archive(data):
    """Построить дерево VFS из содержимого ZIP-архива (bytes)."""
    root = VfsDir("")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            _add_entry(root, info, archive.read(info))
    return root


def _add_entry(root, info, data):
    """Добавить в дерево один элемент ZIP-архива."""
    parts = [p for p in info.filename.split("/") if p not in ("", ".")]
    if ".." in parts:
        raise VfsError(f"unsafe path in archive: {info.filename}")
    if not parts:
        return
    mode = (info.external_attr >> ZIP_ATTR_SHIFT) & PERMISSION_MASK
    mtime = time.mktime(info.date_time + TIME_TUPLE_TAIL)
    if info.is_dir():
        node = make_dirs(root, parts, mtime)
        node.mode = mode or DEFAULT_DIR_MODE
        node.mtime = mtime
        return
    parent = make_dirs(root, parts[:-1], mtime)
    if parts[-1] in parent.children:
        raise VfsError(f"duplicate entry: {info.filename}")
    parent.add(VfsFile(parts[-1], data, mode or DEFAULT_FILE_MODE, mtime))


def save_zip(vfs, path):
    """Сохранить VFS в ZIP-архив на диске (исходный формат).

    :raises VfsError: если файл нельзя записать
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for node in vfs.walk():
            if node is not vfs.root:
                _write_entry(archive, node)
    try:
        with open(path, "wb") as file:
            file.write(buffer.getvalue())
    except OSError as exc:
        raise VfsError(f"cannot save VFS to '{path}': {exc.strerror}") \
            from None


def _write_entry(archive, node):
    """Записать один узел VFS в ZIP-архив, сохранив права и время."""
    name = node.path().lstrip("/")
    date_time = time.localtime(node.mtime)[:ZIP_DATE_FIELDS]
    if date_time[0] < MIN_ZIP_YEAR:
        date_time = (MIN_ZIP_YEAR, 1, 1, 0, 0, 0)
    if node.is_dir:
        info = zipfile.ZipInfo(name + "/", date_time)
        info.external_attr = ((stat.S_IFDIR | node.mode)
                              << ZIP_ATTR_SHIFT) | MSDOS_DIR_FLAG
        archive.writestr(info, b"")
        return
    info = zipfile.ZipInfo(name, date_time)
    info.external_attr = (stat.S_IFREG | node.mode) << ZIP_ATTR_SHIFT
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, node.to_bytes())


def default_vfs(user):
    """Создать VFS по умолчанию (если путь к архиву не указан)."""
    root = VfsDir("")
    home = make_dirs(root, ["home", user])
    home.add(VfsFile("readme.txt", "Добро пожаловать в эмулятор!\n"
                     "VFS по умолчанию создана в памяти.\n".encode()))
    home.add(VfsFile("fruits.txt",
                     b"apple\napple\nbanana\nApple\napple\ncherry\n"))
    make_dirs(root, ["home", user, "projects"])
    etc = make_dirs(root, ["etc"])
    etc.add(VfsFile("hostname", b"emulator\n"))
    make_dirs(root, ["tmp"])
    return Vfs(root, source=None, home=f"/home/{user}")
