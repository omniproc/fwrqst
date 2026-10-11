.DEFAULT_GOAL := help

# ── Cross-platform detection ──────────────────────────────────────────
# uv manages the virtualenv (.venv) and resolves the correct interpreter on
# every platform, so only the shell differs between Windows and POSIX.
ifeq ($(OS),Windows_NT)
    SHELL       = cmd.exe
    .SHELLFLAGS = /c
endif

# ── Targets ───────────────────────────────────────────────────────────
.PHONY: help venv activate install lock format lint typecheck security test build check clean

ifeq ($(OS),Windows_NT)
help: ## Show available targets
	@powershell -NoProfile -Command "Get-Content $(MAKEFILE_LIST) | Select-String '^[a-zA-Z_-]+:.*?## ' | ForEach-Object { $$_ -match '^([a-zA-Z_-]+):.*?## (.*)$$' | Out-Null; '{0,-15} {1}' -f $$Matches[1], $$Matches[2] }"
else
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
endif

venv: ## Create virtual environment and sync all dependencies
	uv sync --all-extras

activate: ## Print venv activation instructions
ifeq ($(OS),Windows_NT)
	@echo. & rem
	@echo   make cannot activate a virtualenv in your current shell
	@echo   because each recipe line runs in its own subprocess.
	@echo. & rem
	@echo   Run this command directly in PowerShell:
	@echo. & rem
	@echo     .\.venv\Scripts\Activate.ps1
	@echo. & rem
	@echo   Activation is optional: "uv run <command>" always uses the venv.
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
	@echo "  Activation is optional: \"uv run <command>\" always uses the venv."
	@echo ""
endif

install: venv ## Install all dependencies and git hooks
	git config core.hooksPath .githooks

lock: ## Update uv.lock after changing dependencies in pyproject.toml
	uv lock

format: ## Auto-format code and sort imports with ruff
	uv run ruff check --select I --fix .
	uv run ruff format .

lint: ## Check formatting and lint code with ruff
	uv run ruff format --check .
	uv run ruff check .

typecheck: ## Type-check code with ty
	uv run ty check

security: ## Security scan with ruff (flake8-bandit rules)
	uv run ruff check --select S .

test: ## Run unit tests with coverage
	uv run pytest

build: ## Build sdist and wheel
	uv build

check: lint typecheck test ## Run all checks (lint incl. security, typecheck, test)

ifeq ($(OS),Windows_NT)
clean: ## Remove generated files
	@powershell -NoProfile -Command "Remove-Item -Recurse -Force .venv, dist, build, .ruff_cache, .pytest_cache -ErrorAction SilentlyContinue"
else
# In the dev container .venv is a volume mount point: it can only be emptied, not removed
clean:
	rm -rf dist build .ruff_cache .pytest_cache
	if mountpoint -q .venv 2>/dev/null; then find .venv -mindepth 1 -delete; else rm -rf .venv; fi
endif
