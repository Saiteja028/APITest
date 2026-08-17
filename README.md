# Enterprise API Automation Framework

A layered, enterprise-grade API test automation framework built on **Python** and
**[Playwright](https://playwright.dev/python/)** (`APIRequestContext`) with
**pytest** as the runner.

It ships with a working example suite that runs out of the box against
[JSONPlaceholder](https://jsonplaceholder.typicode.com), so you can validate the
setup immediately and then point it at your own APIs.

## Why this design

The framework is layered so each concern is isolated and independently testable:

```
tests/              # what to verify (business intent)
  └── services/     # service objects: how to talk to each endpoint (like page objects)
        └── framework/client/   # HTTP client wrapping Playwright's APIRequestContext
              └── config/        # environment-aware settings (YAML + env vars)
```

Supporting pillars: pluggable **auth**, structured **logging**, JSON **schema
validation**, and **data-driven** test inputs.

## Project layout

```
.
├── config/
│   ├── settings.py            # merges YAML env config with environment variables
│   └── environments/          # dev.yaml / qa.yaml / prod.yaml
├── framework/
│   ├── client/                # ApiClient + ApiResponse (fluent assertions)
│   ├── core/                  # logger + BaseService
│   ├── auth/                  # bearer / basic / api_key strategies
│   └── utils/                 # data loader + JSON schema validator
├── services/                  # UsersService, PostsService (service objects)
├── schemas/                   # JSON schema contracts
├── data/                      # test data files
├── tests/api/                 # example test suites
├── conftest.py                # session/function pytest fixtures
├── pytest.ini                 # runner config, markers, HTML report
└── requirements.txt
```

## Setup

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright's browser/runtime deps (needed even for API testing)
playwright install

# 4. (optional) create your local env file
copy .env.example .env
```

## Running tests

```powershell
# Run everything (HTML report written to reports/report.html)
pytest

# Smoke suite only
pytest -m smoke

# A single service
pytest -m users

# Run in parallel across CPUs
pytest -n auto

# Auto-retry flaky tests up to twice
pytest --reruns 2

# Target a different environment
$env:TEST_ENV = "qa"; pytest
```

## Configuration

Configuration resolves in this order (later wins):

1. `config/environments/<TEST_ENV>.yaml`
2. Environment variables / `.env` (see `.env.example`)

Select the environment with `TEST_ENV` (`dev` by default). Secrets such as
tokens should come from environment variables, never committed YAML.

### Authentication

Set the strategy in the env YAML (or via env vars):

| strategy | required values                       | sends                                   |
|----------|---------------------------------------|-----------------------------------------|
| `none`   | –                                     | nothing                                 |
| `bearer` | `API_TOKEN`                           | `Authorization: Bearer <token>`         |
| `basic`  | `API_USERNAME`, `API_PASSWORD`        | `Authorization: Basic <base64>`         |
| `api_key`| `API_KEY` (+ `api_key_header` in YAML)| `<header>: <key>`                       |

## Extending the framework

**Add a new service** – create `services/<name>_service.py`:

```python
from framework.core.base_service import BaseService

class OrdersService(BaseService):
    service_key = "orders"          # must exist under services: in the env YAML

    def get_order(self, order_id):
        return self.get(str(order_id))
```

Register its base path under `services:` in each `config/environments/*.yaml`,
then expose a fixture in `conftest.py`.

**Add a schema contract** – drop a `*.json` schema in `schemas/` and call
`validate_schema(response_json, "my_schema.json")` in a test.

## Reports & logs

- HTML report: `reports/report.html` (generated on every run)
- Rotating logs: `logs/api-framework.log`
