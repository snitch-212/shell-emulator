# Эмулятор командной оболочки UNIX

Практическая работа №1 по дисциплине «Конфигурационное управление»,
вариант 25.

## 1. Общее описание

Консольное приложение (CLI), имитирующее работу командной строки
UNIX-подобной ОС. Эмулятор работает с виртуальной файловой системой
(VFS), которая загружается из ZIP-архива и полностью хранится в
памяти.

* Язык реализации — Python 3.10+, только стандартная библиотека.
* Приглашение строится по реальным данным ОС:
  `имя_пользователя@имя_хоста:текущий_каталог$`.
* Поддерживаются интерактивный режим (REPL) и стартовые скрипты.

Работа выполнена в 5 этапов, каждый этап — отдельный коммит:

| Этап | Содержание |
|------|------------|
| 1. REPL | приглашение, парсер с переменными окружения, заглушки `ls`/`cd`, `exit`, ошибки |
| 2. Конфигурация | параметры `--vfs`, `--script`, отладочный вывод, стартовый скрипт |
| 3. VFS | загрузка ZIP в память, base64, `vfs-save`, VFS по умолчанию |
| 4. Основные команды | `ls`, `cd`, `pwd`, `uniq`, `date` |
| 5. Дополнительные команды | `chmod` (изменения только в памяти) |

## 2. Функции и настройки

### 2.1. Параметры командной строки

| Параметр | Описание |
|----------|----------|
| `--vfs PATH` | путь к ZIP-архиву с VFS; если не указан — VFS по умолчанию |
| `--script PATH` | путь к стартовому скрипту |
| `-h`, `--help` | справка по параметрам |

При запуске выводится отладочная информация обо всех параметрах:

```text
[debug] emulator parameters:
[debug]   --vfs     = build/vfs/deep.zip
[debug]   --script  = (not set)
```

### 2.2. Парсер командной строки

| Синтаксис | Поведение |
|-----------|-----------|
| `a b   c` | слова разделяются пробелами |
| `$HOME`, `${USER}` | раскрытие переменной окружения реальной ОС |
| `'текст $HOME'` | одинарные кавычки — без подстановок |
| `"текст $HOME"` | двойные кавычки — с подстановками |
| `\x` | экранирование символа |
| `# ...` | комментарий до конца строки |

Неизвестная переменная заменяется пустой строкой, как в bash.

### 2.3. Стартовый скрипт

* Текстовый файл с командами эмулятора, по одной на строку.
* Комментарии — как в Python: строка или хвост строки после `#`.
* Каждая команда выводится вместе с приглашением, а затем её
  результат — так имитируется диалог с пользователем.
* Ошибка в строке выводится с номером строки
  (`script.txt: line 6: cd: too many arguments`), выполнение
  продолжается.
* Нечитаемый или отсутствующий файл скрипта — сообщение
  `shell: cannot read script ...` и код возврата 1.
* `exit` в скрипте завершает эмулятор, иначе после скрипта
  начинается интерактивный режим.

### 2.4. Виртуальная файловая система

* Источник — ZIP-архив. Он читается в память целиком и никогда не
  изменяется на диске; все команды меняют только данные в памяти.
* Текстовые файлы хранятся строками, двоичные — в кодировке base64.
* Права доступа и время изменения берутся из атрибутов ZIP и
  сохраняются обратно командой `vfs-save`.
* Без `--vfs` в памяти создаётся VFS по умолчанию:
  `/home/<пользователь>` (с файлами `readme.txt`, `fruits.txt`),
  `/etc/hostname`, `/tmp`.
* Ошибки загрузки (файл не найден, не ZIP-архив, каталог вместо
  файла) выводятся как `shell: cannot load VFS '...': ...`, код 1.
* Пути: абсолютные и относительные, `.`, `..`, `~`.
* Права владельца проверяются: `cd` требует `x` каталога, `ls` —
  `r` каталога, `uniq` — `r` файла, проход через каталог — `x`.

### 2.5. Команды

| Команда | Описание |
|---------|----------|
| `ls [-l] [-a] [путь ...]` | содержимое каталогов; `-l` — подробно, `-a` — со скрытыми |
| `cd [путь \| ~ \| -]` | смена каталога; без аргумента и `~` — домашний, `-` — предыдущий |
| `pwd` | абсолютный путь текущего каталога |
| `uniq [-c] [-d] [-u] [-i] файл` | удаление соседних повторов строк (опции — ниже) |
| `date [-u] [-I] [+ФОРМАТ]` | дата и время ОС; `-u` — UTC, `-I` — ISO 8601, `+ФОРМАТ` — формат strftime |
| `chmod [-R] [-v] РЕЖИМ путь ...` | изменение прав доступа (режимы — ниже) |
| `vfs-save путь` | сохранить состояние VFS в ZIP-архив на диске |
| `vfs-info [путь]` | служебная: источник VFS и дерево каталогов |
| `exit [код]` | завершение работы с кодом возврата |

Опции `uniq`: `-c` — число повторов перед строкой, `-d` — только
повторяющиеся строки, `-u` — только неповторяющиеся, `-i` — без учёта
регистра.

Режимы `chmod`: восьмеричный (`755`, `0640`) или символьный —
выражения `[ugoa]*[-+=][rwx]*` через запятую: `u+x`, `go-w`, `a=r`,
`u=rwx,g=rx,o=`, `+x`. Опция `-R` — рекурсивно для всего поддерева,
`-v` — сообщать о каждом изменении.

### 2.6. Обработка ошибок

| Ситуация | Пример сообщения | Код |
|----------|------------------|-----|
| неизвестная команда | `foo: command not found` | 127 |
| неверная опция | `ls: invalid option -- 'z'` | 1 |
| лишние аргументы | `cd: too many arguments` | 1 |
| нет операнда | `uniq: missing operand: file` | 1 |
| путь не существует | `cd: /nope: No such file or directory` | 1 |
| не каталог / каталог | `cd: /etc/motd: Not a directory` | 1 |
| нет прав | `cd: /projects: Permission denied` | 1 |
| неверный режим chmod | `chmod: invalid mode: 'abc'` | 1 |
| незакрытая кавычка | `shell: syntax error: unterminated quote (")` | 1 |
| ошибка загрузки VFS | `shell: cannot load VFS 'x.zip': invalid format` | 1 |

## 3. Сборка и запуск тестов

Сборка не требуется, нужен Python 3.10 или новее.

```sh
./run.sh [--vfs PATH] [--script PATH]       # Linux / macOS
run.bat  [--vfs PATH] [--script PATH]       # Windows
make run ARGS="--vfs build/vfs/deep.zip"    # через Makefile
```

Тестовые VFS-архивы (в репозиторий не входят, так как это артефакты
сборки) создаются в каталоге `build/vfs`:

```sh
make vfs                  # или: python3 tools/make_vfs.py
```

| Архив | Содержимое |
|-------|------------|
| `minimal.zip` | минимальная VFS — один файл |
| `multi.zip` | несколько файлов, в том числе двоичный |
| `deep.zip` | не менее 3 уровней вложенности файлов и каталогов |
| `broken.zip` | не ZIP-архив — для проверки ошибок |

Модульные тесты и проверка оформления кода:

```sh
make test                 # или: python3 -m unittest discover -s tests -t .
make lint                 # или: python3 tools/check_style.py
```

`tools/check_style.py` проверяет код по перечню нарушений из
сборника: длину строк (≤ 80) и файлов, длину функций (≤ 40 строк),
число аргументов (≤ 7), наличие docstring, цикломатическую сложность
(≤ 10), магические числа в сравнениях и имена по PEP 8.

### Скрипты ОС для проверки эмулятора

Каталог `scripts/`, для каждого скрипта есть версии `.sh` и `.bat`:

| Скрипт | Что проверяет |
|--------|---------------|
| `test_no_params` | запуск без параметров |
| `test_script` | `--script`: комментарии, ошибки, `exit`, нет файла |
| `test_all_params` | `--vfs` и `--script` вместе, `--help`, неверный параметр |
| `test_vfs_minimal` | минимальная VFS |
| `test_vfs_multi` | VFS из нескольких файлов, двоичный файл |
| `test_vfs_deep` | VFS с 3+ уровнями, `vfs-save` и повторная загрузка |
| `test_vfs_errors` | ошибки загрузки VFS, VFS по умолчанию |

### Стартовые скрипты эмулятора

Каталог `examples/`:

| Скрипт | Что проверяет |
|--------|---------------|
| `stage2.txt` | комментарии, вывод команд, ошибки в скрипте |
| `stage3.txt` | команды этапов 1–3, работа с VFS, `vfs-save`, ошибки |
| `stage4.txt` | все режимы `ls`, `cd`, `pwd`, `uniq`, `date` и ошибки |
| `stage5.txt` | все режимы `chmod`, влияние прав на команды, ошибки |
| `exit_code.txt` | завершение эмулятора командой `exit 3` |

```sh
make vfs
./run.sh --vfs build/vfs/deep.zip --script examples/stage5.txt
```

## 4. Примеры использования

```text
$ ./run.sh --vfs build/vfs/deep.zip
[debug] emulator parameters:
[debug]   --vfs     = build/vfs/deep.zip
[debug]   --script  = (not set)
student@laptop:/$ ls
etc  home  projects  var
student@laptop:/$ cd projects/app/src
student@laptop:/projects/app/src$ ls -la
drwxr-xr-x  4 student student 4096 Sep 14 12:00 .
drwxr-xr-x  6 student student 4096 Sep 14 12:00 ..
-rw-r--r--  1 student student   15 Sep 14 12:00 main.py
drwxr-xr-x  3 student student 4096 Sep 14 12:00 utils
student@laptop:/projects/app/src$ cd ../../..
student@laptop:/$ uniq -c /var/log/syslog
      2 boot
      3 start
      1 stop
student@laptop:/$ date +%d.%m.%Y
14.10.2026
student@laptop:/$ chmod -v go-r /etc/motd
mode of '/etc/motd' changed from 0644 (rw-r--r--) to 0600 (rw-------)
student@laptop:/$ chmod -x /projects
student@laptop:/$ cd /projects
cd: /projects: Permission denied
student@laptop:/$ ls $HOME
ls: cannot access '/home/student': No such file or directory
student@laptop:/$ foo
foo: command not found
student@laptop:/$ vfs-save build/changed.zip
VFS saved to build/changed.zip
student@laptop:/$ exit 0
```

Запуск со стартовым скриптом:

```text
$ ./run.sh --script examples/exit_code.txt
[debug] emulator parameters:
[debug]   --vfs     = (not set)
[debug]   --script  = examples/exit_code.txt
# Скрипт завершает эмулятор с кодом 3
student@laptop:~$ ls
fruits.txt  projects  readme.txt
student@laptop:~$ exit 3
$ echo $?
3
```

## 5. Структура репозитория

```text
src/shell_emulator/
  __main__.py         запуск: python -m shell_emulator
  cli.py              параметры командной строки, отладочный вывод
  shell.py            приглашение, выполнение команд, REPL, скрипты
  parser.py           разбор строки: кавычки, экранирование, $VAR
  vfs.py              VFS в памяти, загрузка и сохранение ZIP, права
  errors.py           исключения ShellError и ExitRequest
  commands/
    __init__.py       реестр команд
    basic.py          exit
    fs.py             ls, cd, pwd
    text.py           uniq
    system.py         date
    perms.py          chmod
    vfs_commands.py   vfs-save, vfs-info
    options.py        разбор однобуквенных опций
tests/                модульные тесты (unittest)
examples/             стартовые скрипты эмулятора
scripts/              скрипты ОС (.sh, .bat) для проверки эмулятора
tools/check_style.py  проверка кода по правилам оформления
tools/make_vfs.py     генерация тестовых VFS-архивов
run.sh, run.bat       скрипты запуска
Makefile              цели run, test, lint, vfs, clean
```
