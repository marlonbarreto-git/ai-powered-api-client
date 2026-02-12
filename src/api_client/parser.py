"""OpenAPI spec parser that generates tool definitions."""

from typing import Any

from api_client.models import ParameterDef, ToolDefinition

SUPPORTED_HTTP_METHODS = ("get", "post", "put", "patch", "delete")
DEFAULT_PARAM_TYPE = "string"
JSON_CONTENT_TYPE = "application/json"


class OpenAPIParser:
    """Parses an OpenAPI spec into ToolDefinition objects for LLM consumption."""

    def __init__(self, spec: dict[str, Any]) -> None:
        self.spec: dict[str, Any] = spec
        servers: list[dict[str, Any]] = spec.get("servers", [])
        self.base_url: str = servers[0]["url"] if servers else ""

    def parse(self) -> list[ToolDefinition]:
        """Parse all paths and operations into a list of ToolDefinitions.

        Returns:
            A list of ToolDefinition objects, one per endpoint operation.
        """
        tools: list[ToolDefinition] = []
        for path, methods in self.spec.get("paths", {}).items():
            for method, operation in methods.items():
                if method not in SUPPORTED_HTTP_METHODS:
                    continue
                params = self._extract_parameters(operation)
                tools.append(
                    ToolDefinition(
                        name=operation.get("operationId", f"{method}_{path}"),
                        description=operation.get("summary", ""),
                        method=method.upper(),
                        path=path,
                        parameters=params,
                        base_url=self.base_url,
                    )
                )
        return tools

    def _extract_parameters(self, operation: dict[str, Any]) -> list[ParameterDef]:
        """Extract path, query, and body parameters from a single operation.

        Args:
            operation: The OpenAPI operation object.

        Returns:
            A list of ParameterDef objects for the operation.
        """
        params: list[ParameterDef] = []
        for p in operation.get("parameters", []):
            params.append(
                ParameterDef(
                    name=p["name"],
                    type=p.get("schema", {}).get("type", DEFAULT_PARAM_TYPE),
                    required=p.get("required", False),
                    location=p["in"],
                    description=p.get("description", ""),
                )
            )
        request_body: dict[str, Any] = operation.get("requestBody", {})
        if request_body:
            content: dict[str, Any] = request_body.get("content", {})
            json_schema: dict[str, Any] = content.get(JSON_CONTENT_TYPE, {}).get("schema", {})
            required_fields: set[str] = set(json_schema.get("required", []))
            for prop_name, prop_schema in json_schema.get("properties", {}).items():
                params.append(
                    ParameterDef(
                        name=prop_name,
                        type=prop_schema.get("type", DEFAULT_PARAM_TYPE),
                        required=prop_name in required_fields,
                        location="body",
                        description=prop_schema.get("description", ""),
                    )
                )
        return params

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Convert parsed tools into OpenAI function-calling format.

        Returns:
            A list of dicts conforming to the OpenAI tools schema.
        """
        tools = self.parse()
        openai_tools: list[dict[str, Any]] = []
        for tool in tools:
            properties: dict[str, dict[str, str]] = {}
            required: list[str] = []
            for p in tool.parameters:
                properties[p.name] = {"type": p.type, "description": p.description}
                if p.required:
                    required.append(p.name)
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": properties,
                            "required": required,
                        },
                    },
                }
            )
        return openai_tools
