"""API caller that executes tool definitions against real endpoints."""

from dataclasses import dataclass, field

import httpx

from api_client.models import ToolDefinition


@dataclass
class APIRequest:
    method: str
    url: str
    query_params: dict = field(default_factory=dict)
    json_body: dict | None = None
    headers: dict = field(default_factory=dict)


@dataclass
class APIResponse:
    status_code: int
    body: object
    headers: dict = field(default_factory=dict)


class APICaller:
    def __init__(self, default_headers: dict | None = None) -> None:
        self.default_headers = default_headers or {}

    def build_request(self, tool: ToolDefinition, arguments: dict) -> APIRequest:
        url = tool.path
        query_params = {}
        body_params = {}

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

    async def call(self, tool: ToolDefinition, arguments: dict) -> APIResponse:
        request = self.build_request(tool, arguments)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=request.url,
                params=request.query_params,
                json=request.json_body,
                headers=request.headers,
            )
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            body = response.json()
        else:
            body = response.text
        return APIResponse(
            status_code=response.status_code,
            body=body,
            headers=dict(response.headers),
        )
