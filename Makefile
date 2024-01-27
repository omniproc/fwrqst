.DEFAULT_GOAL := help

# ── Cross-platform detection ──────────────────────────────────────────
VENV_CFG = .venv/pyvenv.cfg

ifeq ($(OS),Windows_NT)
    SHELL       = cmd.exe
    .SHELLFLAGS = /c
    VENV_BIN    = .venv\Scripts
    PYTHON      = $(VENV_BIN)\python
    PIP         = $(VENV_BIN)\pip
else
    VENV_BIN    = .venv/bin
    PYTHON      = $(VENV_BIN)/python
    PIP         = $(VENV_BIN)/pip
endif

# ── Auto-create virtualenv when missing ───────────────────────────────
$(VENV_CFG):
	python -m venv .venv

# ── Targets ───────────────────────────────────────────────────────────
.PHONY: help venv activate install format lint typecheck security test build check clean

ifeq ($(OS),Windows_NT)
help: ## Show available targets
	@powershell -NoProfile -Command "Get-Content $(MAKEFILE_LIST) | Select-String '^[a-zA-Z_-]+:.*?## ' | ForEach-Object { $$_ -match '^([a-zA-Z_-]+):.*?## (.*)$$' | Out-Null; '{0,-15} {1}' -f $$Matches[1], $$Matches[2] }"
else
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
endif

venv: $(VENV_CFG) ## Create virtual environment

activate: $(VENV_CFG) ## Print venv activation instructions
ifeq ($(OS),Windows_NT)
	@echo. & rem
	@echo   make cannot activate a virtualenv in your current shell
	@echo   because each recipe line runs in its own subprocess.
	@echo. & rem
	@echo   Run this command directly in PowerShell:
	@echo. & rem
	@echo     .\.venv\Scripts\Activate.ps1
	@echo. & rem
	@echo   All other make targets use the virtualenv automatically.
	@echo. & rem
else
	@echo ""
	@echo "  make cannot activate a virtualenv in your current shell"
	@echo "  because each recipe line runs in its own subprocess."
	@echo ""
	@echo "  Run this command directly:"
	@echo ""
	@echo "    source .venv/bin/activate"
	@echo ""
	@echo "  All other make targets use the virtualenv automatically."
	@echo ""
endif

install: $(VENV_CFG) ## Install all dependencies and git hooks
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[all]" build
	git config core.hooksPath .githooks

format: $(VENV_CFG) ## Auto-format code with black
	$(PYTHON) -m black .

lint: $(VENV_CFG) ## Lint code with flake8
	$(PYTHON) -m flake8 .

typecheck: $(VENV_CFG) ## Type-check code with mypy
	$(PYTHON) -m mypy src/

security: $(VENV_CFG) ## Security scan with bandit
	$(PYTHON) -m bandit -c pyproject.toml -r .

test: $(VENV_CFG) ## Run unit tests with coverage
	$(PYTHON) -m pytest

build: $(VENV_CFG) ## Build sdist and wheel
	$(PYTHON) -m build

check: lint typecheck security test ## Run all checks (lint, typecheck, security, test)

ifeq ($(OS),Windows_NT)
clean: ## Remove generated files
	@powershell -NoProfile -Command "Remove-Item -Recurse -Force .venv, dist, build, .mypy_cache, .pytest_cache -ErrorAction SilentlyContinue"
else
clean:
	rm -rf .venv dist build .mypy_cache .pytest_cache
endif
