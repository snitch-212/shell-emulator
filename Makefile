# Основные цели: make run, make test, make lint
PYTHON ?= python3
export PYTHONPATH := src

.PHONY: run test lint clean

run:
	$(PYTHON) -m shell_emulator $(ARGS)

test:
	$(PYTHON) -m unittest discover -s tests -t . -v

lint:
	$(PYTHON) tools/check_style.py src tests tools

clean:
	rm -rf build
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
