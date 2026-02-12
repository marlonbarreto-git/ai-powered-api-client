"""API caller that executes tool definitions against real endpoints."""

from dataclasses import dataclass, field
from typing import Any

import httpx

from api_client.models import ToolDefinition

CONTENT_TYPE_HEADER = "content-type"
JSON_CONTENT_INDICATOR = "json"


@dataclass
class APIRequest:
    """Structured representation of an outbound HTTP request."""

    method: str
    url: str
    query_params: dict[str, Any] = field(default_factory=dict)
    json_body: dict[str, Any] | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class APIResponse:
    """Structured representation of an HTTP response."""

    status_code: int
    body: Any
    headers: dict[str, str] = field(default_factory=dict)


class APICaller:
    """Executes API calls built from ToolDefinition objects."""

    def __init__(self, default_headers: dict[str, str] | None = None) -> None:
        self.default_headers: dict[str, str] = default_headers or {}

    def build_request(self, tool: ToolDefinition, arguments: dict[str, Any]) -> APIRequest:
        """Build an APIRequest by mapping arguments to path, query, and body params.

        Args:
            tool: The tool definition describing the endpoint.
            arguments: Mapping of parameter names to their values.

        Returns:
            A fully populated APIRequest ready for execution.
        """
        url = tool.path
        query_params: dict[str, Any] = {}
        body_params: dict[str, Any] = {}

        for param in tool.parameters:
            if param.name not in arguments:
                continue
            value = arguments[param.name]
            if param.location == "path":
                url = url.replace(f"{{{param.name}}}", str(value))
            elif param.location == "query":
                query_params[param.name] = value
            elif param.location == "body":
                body_params[param.name] = value

        if tool.base_url:
            url = tool.base_url + url

        return APIRequest(
            method=tool.method,
            url=url,
            query_params=query_params,
            json_body=body_params if body_params else None,
            headers=dict(self.default_headers),
        )

    async def call(self, tool: ToolDefinition, arguments: dict[str, Any]) -> APIResponse:
        """Execute an HTTP request for the given tool and return the response.

        Args:
            tool: The tool definition describing the endpoint.
            arguments: Mapping of parameter names to their values.

        Returns:
            An APIResponse with status code, parsed body, and headers.
        """
        request = self.build_request(tool, arguments)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=request.url,
                params=request.query_params,
                json=request.json_body,
                headers=request.headers,
            )
        content_type = response.headers.get(CONTENT_TYPE_HEADER, "")
        if JSON_CONTENT_INDICATOR in content_type:
            body: Any = response.json()
        else:
            body = response.text
        return APIResponse(
            status_code=response.status_code,
            body=body,
            headers=dict(response.headers),
        )
