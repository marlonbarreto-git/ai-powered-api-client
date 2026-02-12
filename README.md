# AI-Powered API Client

[![CI](https://github.com/marlonbarreto-git/ai-powered-api-client/actions/workflows/ci.yml/badge.svg)](https://github.com/marlonbarreto-git/ai-powered-api-client/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Client that reads OpenAPI specs and generates LLM tool definitions, turning any API into a conversational interface.

## Overview

AI-Powered API Client parses OpenAPI specifications and converts each endpoint into a structured tool definition that LLMs can invoke. It handles path, query, and body parameters, generates OpenAI-compatible function calling schemas, and executes the actual HTTP requests via an async caller. This bridges the gap between natural language and any REST API.

## Architecture

```
OpenAPI Spec (JSON)
        |
        v
+------------------+
|  OpenAPIParser   |
| (extract paths,  |
|  params, bodies) |
+------------------+
        |
        v
+------------------+      +------------------+
| ToolDefinition[] |----->|  to_openai_tools  |
| (name, method,   |      | (function calling |
|  path, params)   |      |  schema export)   |
+------------------+      +------------------+
        |
        v
+------------------+
|    APICaller     |
| (build request,  |
|  async httpx)    |
+------------------+
        |
        v
   APIResponse
```

## Features

- OpenAPI spec parsing with path, query, and body parameter extraction
- Request body schema support (JSON properties)
- OpenAI function calling schema generation
- Async HTTP execution via httpx
- Path parameter interpolation
- Automatic content-type detection (JSON/text)
- Configurable default headers

## Tech Stack

- Python 3.11+
- Pydantic (data validation)
- httpx (async HTTP client)

## Quick Start

```bash
git clone https://github.com/marlonbarreto-git/ai-powered-api-client.git
cd ai-powered-api-client
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Project Structure

```
src/api_client/
  __init__.py
  models.py     # ParameterDef and ToolDefinition dataclasses
  parser.py     # OpenAPIParser with schema export
  caller.py     # APICaller with async HTTP execution
tests/
  test_parser.py
  test_caller.py
```

## Testing

```bash
pytest -v --cov=src/api_client
```

31 tests covering OpenAPI parsing, parameter extraction, request building, and schema generation.

## License

MIT