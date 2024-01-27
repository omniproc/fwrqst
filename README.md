# fwrqst

![snapshot workflow](https://github.com/omniproc/fwrqst/actions/workflows/snapshot.yml/badge.svg)

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

## Environment

Get an isolated build environment

```bash
pip install virtualenv
python -m virtualenv .venv
source .venv/bin/activate
pip install -e .[dev,cli,test]
```

When done, run basic project specific checks with project defaults defined in `pyproject.toml`.

```bash
black .
bandit -c pyproject.toml -r .
flake8 .
```

And run unit tests with defaults defined in `pyproject.toml`.

```bash
pytest .
```

## Building

`pip wheel --no-deps --wheel-dir dist .`. Follow the build steps from the CI pipelines for more details.

# Tufin API documentation

An OpenAPI-ish doc of the most current version can be found [here](https://forum.tufin.com/support/kc/rest-api/R23-2/securechangeworkflow/apidoc/#!/Tickets).
This code was tested against SecureChange version **23.1 PHF1.2.0**. Unfortunately there is no SemVer-like API-Version available in the Tufin API nor a mock-server available to make this more reliable 😿.
