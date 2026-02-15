VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: venv
venv:
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt -r requirements-dev.txt

.PHONY: lint
lint:
	$(VENV)/bin/ruff check scripts

.PHONY: bandit
bandit:
	$(VENV)/bin/bandit -q -r scripts

.PHONY: test
test:
	$(VENV)/bin/pytest -q

.PHONY: compile
compile:
	$(PY) -c "import pathlib, py_compile; [py_compile.compile(str(p), doraise=True) for p in pathlib.Path('scripts').rglob('*.py')]; print('py_compile: OK')"

.PHONY: check
check: lint bandit compile test
