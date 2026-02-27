VENV ?= .venv

# Prefer venv binaries when available; otherwise fall back to user/system-installed tools.
PY := $(shell [ -x "$(VENV)/bin/python" ] && echo "$(VENV)/bin/python" || echo "python3")
PIP := $(shell [ -x "$(VENV)/bin/pip" ] && echo "$(VENV)/bin/pip" || echo "python3 -m pip")
RUFF := $(shell [ -x "$(VENV)/bin/ruff" ] && echo "$(VENV)/bin/ruff" || echo "ruff")
BANDIT := $(shell [ -x "$(VENV)/bin/bandit" ] && echo "$(VENV)/bin/bandit" || echo "bandit")
PYTEST := $(shell [ -x "$(VENV)/bin/pytest" ] && echo "$(VENV)/bin/pytest" || echo "pytest")

.PHONY: venv
venv:
	@python3 -m venv $(VENV) || ( \
		echo "ERROR: venv creation failed. On Ubuntu/Debian, install: sudo apt install python3.12-venv" >&2; \
		exit 1 \
	)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt -r requirements-dev.txt

.PHONY: lint
lint:
	$(RUFF) check scripts

.PHONY: bandit
bandit:
	$(BANDIT) -q -r scripts -s B101,B104,B105,B110,B112,B310,B314,B405,B324,B404,B603,B605,B607

.PHONY: test
test:
	PYTHONPATH=. $(PYTEST) -q

.PHONY: compile
compile:
	$(PY) -c "import pathlib, py_compile; [py_compile.compile(str(p), doraise=True) for p in pathlib.Path('scripts').rglob('*.py')]; print('py_compile: OK')"

.PHONY: check
check: lint bandit compile test
