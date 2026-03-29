# fwrqst

![Build](https://github.com/omniproc/fwrqst/actions/workflows/snapshot.yml/badge.svg)
![Release](https://github.com/omniproc/fwrqst/actions/workflows/release.yml/badge.svg)
![Codecov](https://codecov.io/gh/omniproc/fwrqst/branch/main/graph/badge.svg)
![Python](https://img.shields.io/badge/python-~%3D3.14-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Conventional Commits](https://img.shields.io/badge/commits-conventional-fe5196?logo=conventionalcommits&logoColor=white)

A library abstracting the complexity of creating firewall configuration change requests against [tufin](https://www.tufin.com/de/tufin-orchestration-suite/securechange).

# Requests

## Validation

If you use an _IDE_ that supports `YAML` or `JSON` schema validations feel free to use the _JSON-schema_ for input validation and autocompletion.
You can get the current access request _JSON-schema_ for your version of _fwrqst_ using `fwrqst schema accessrequest`. Examples are provided in the [examples](/examples/) folder of this repo.

You can do so by using in-file declarations within your `YAML`, pointing it to the schema using a modeline like so: `# yaml-language-server: $schema=./examples/tickets.schema.json`.

Some _IDEs_ allow you to explicitly map file endings to schemas. For example in VSCode with the [YAML plugin](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml) installed, assuming your current VSCode workspace is set to this repository, add this to your VSCode `settings.json` and restart VSCode:

```json
{
  "yaml.schemas": {
    "${workspaceFolder}/examples/tickets.schema.json": [".tufin.yaml"]
  }
}
```

When you now create a new file ending `.tufin.yaml` VSCode will automatically use the specified schema. See the [examples folder](/examples/).

# CLI usage

Install with CLI extras: `pip install fwrqst[cli]`

## `securechange` — Tufin SecureChange API

Manage access request tickets against the Tufin SecureChange API.

```bash
# Create a ticket from a YAML file
fwrqst securechange -u admin -p secret create -i tickets.yaml

# Read an existing ticket
fwrqst securechange -u admin -p secret read -t TICKET_ID

# Cancel a pending ticket
fwrqst securechange -u admin -p secret cancel -t TICKET_ID
```

Connection parameters (`--username`, `--password`, `--domain`, `--port`, `--cafile`, `--workflow`) can also be set via environment variables or the `settings.toml` file. See [Settings](#settings).

## `schema` — JSON schema export

```bash
# Print the access request JSON schema to stdout
fwrqst schema accessrequest

# Write the schema to a file
fwrqst schema accessrequest -o tickets.schema.json
```

## `config` — Configuration management

```bash
# Show current settings
fwrqst config show

# Find the settings file location on disk
fwrqst config find

# Set a specific setting (persists to settings.toml)
fwrqst config set -k secure_change_port -v 8443

# Reset a setting to its default
fwrqst config set -k secure_change_port
```

# API usage

```python
from pathlib import Path
from datetime import date, timedelta

from fwrqst.io import load_tickets, dump_tickets
from fwrqst.models.ticket import (
    AccessRequestTicket,
    AccessRequest,
    IpEndpoint,
    DnsEndpoint,
    TcpService,
)
from fwrqst.models.types import Priority, Action
from fwrqst.api.securechange import AccessRequestService

# Load tickets from YAML
tickets = load_tickets(Path("examples/tickets.yaml"))

# Create a ticket programmatically
ticket = AccessRequestTicket(
    subject="Temporary HTTPS Access",
    workflow="Standard",
    priority=Priority.NORMAL,
    expiration=date.today() + timedelta(days=30),
    access_requests=[
        AccessRequest(
            source_domain="Default",
            sources=[IpEndpoint(address="192.168.1.100", cidr=32)],
            destination_domain="Default",
            destinations=[DnsEndpoint(fqdn="example.com")],
            services=[TcpService(port=443)],
            action=Action.ACCEPT,
            comment="Allow HTTPS to SaaS provider",
        ),
    ],
)

# Save to YAML
dump_tickets(Path("my_ticket.yaml"), [ticket])

# Submit to Tufin SecureChange
service = AccessRequestService(
    username="admin",
    password="secret",
    domain="tufin.example.com",
)
ticket_id = service.create_ticket(ticket)
```

# Settings

This project makes use of Dynaconf under the hood to provide a convenient configuration interface. You can view the currently applied defaults using `fwrqst config show`. Any parameter you provide when using the CLI or API will overwrite the default value.

## Defaults

It's possible to change the defaults in a persistent manner. There are two ways to do so:

1. Locate the `settings.toml` using `fwrqst config find` and make changes to the file.
2. Use `fwrqst config set` to configure individual settings of the `settings.toml` file.

If you need a blank `settings.toml` with all the available settings and their default values simply run `fwrqst config set` with a valid key but without any value, e.g. `fwrqst config set -k secure_change_port`. This will reset the `secure_change_port` setting to its default and persist the current application settings to the location returned by `fwrqst config find`.

Want something more 12-factor like? You can configure all application settings simply using environment variables. Simply prefix any setting you want to change with `FWRQST_`, e.g. `export FWRQST_SECURE_CHANGE_PORT=80`

## Precedence

1. Parameters passed to the CLI or methods/functions
2. Settings defined using OS environment variables
3. Settings defined within the `settings.toml` file
4. Default settings

Few things to note here:

- Not all arguments available for a given command may be available as CLI arguments. Some might only be accessible via environment variables or the `settings.toml` file.
- Settings of the `settings.toml` file can be set by directly editing the file or by using the `config` subcommand of the CLI.

# Development

## Prerequisites

- Python 3.14+
- `make` (optional but recommended — on Windows: `winget install GnuWin32.Make` or use Git Bash / WSL)

## Quick start

```bash
# Install all dependencies and git hooks (auto-creates the venv)
make install
```

All make targets automatically create the virtual environment if it does not exist yet.

## Available Make targets

| Target           | Description                                      |
| ---------------- | ------------------------------------------------ |
| `make help`      | Show all available targets                       |
| `make venv`      | Create a `.venv` virtual environment             |
| `make activate`  | Print venv activation instructions               |
| `make install`   | Install all dependencies and git hooks           |
| `make format`    | Auto-format code with black                      |
| `make lint`      | Lint code with flake8                            |
| `make typecheck` | Type-check code with mypy                        |
| `make security`  | Security scan with bandit                        |
| `make test`      | Run unit tests with coverage                     |
| `make build`     | Build sdist and wheel                            |
| `make check`     | Run all checks (lint, typecheck, security, test) |
| `make clean`     | Remove generated files                           |

## Manual setup (without Make)

```bash
python -m venv .venv

# Activate the venv
# Linux / macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -e ".[all]" build

# Install git hooks
git config core.hooksPath .githooks
```

## Running checks locally

```bash
black .                       # Format
flake8 .                      # Lint
mypy src/                     # Type check
bandit -c pyproject.toml -r . # Security
pytest                        # Tests
```

## VS Code

The workspace includes debug launch configurations (`.vscode/launch.json`):

| Configuration           | Description                         |
| ----------------------- | ----------------------------------- |
| **Debug**               | Run `debug/debug.py`                |
| **Debug: Current File** | Run the currently open file         |
| **Debug: CLI (fwrqst)** | Debug the CLI entry point           |
| **Debug: Pytest**       | Debug tests with breakpoint support |
| **Debug: Mypy**         | Debug mypy type checking            |

Recommended extensions are listed in `.vscode/extensions.json` and will be suggested on first open.

## Commit convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/). Git hooks enforce the format automatically. Allowed prefixes: `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `ci`, `chore`, `build`, `style`.

Examples:

```
feat: add bulk ticket creation
fix: handle empty YAML input gracefully
docs: update CLI usage examples
```

[release-please](https://github.com/googleapis/release-please) uses these commits to auto-generate the changelog and determine version bumps.

## Building

```bash
make build
# or: python -m build
```

# Tufin API documentation

An OpenAPI-ish doc of the most current version can be found [here](https://forum.tufin.com/support/kc/rest-api/R23-2/securechangeworkflow/apidoc/#!/Tickets).
This code was tested against SecureChange version **23.1 PHF1.2.0**. Unfortunately there is no SemVer-like API-Version available in the Tufin API nor a mock-server available to make this more reliable 😿.
