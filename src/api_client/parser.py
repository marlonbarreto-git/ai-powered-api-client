"""OpenAPI spec parser that generates tool definitions."""

from api_client.models import ParameterDef, ToolDefinition


class OpenAPIParser:
    def __init__(self, spec: dict) -> None:
        self.spec = spec
        servers = spec.get("servers", [])
        self.base_url = servers[0]["url"] if servers else ""

    def parse(self) -> list[ToolDefinition]:
        tools = []
        for path, methods in self.spec.get("paths", {}).items():
            for method, operation in methods.items():
                if method not in ("get", "post", "put", "patch", "delete"):
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

    def _extract_parameters(self, operation: dict) -> list[ParameterDef]:
        params = []
        for p in operation.get("parameters", []):
            params.append(
                ParameterDef(
                    name=p["name"],
                    type=p.get("schema", {}).get("type", "string"),
                    required=p.get("required", False),
                    location=p["in"],
                    description=p.get("description", ""),
                )
            )
        request_body = operation.get("requestBody", {})
        if request_body:
            content = request_body.get("content", {})
            json_schema = content.get("application/json", {}).get("schema", {})
            required_fields = set(json_schema.get("required", []))
            for prop_name, prop_schema in json_schema.get("properties", {}).items():
                params.append(
                    ParameterDef(
                        name=prop_name,
                        type=prop_schema.get("type", "string"),
                        required=prop_name in required_fields,
                        location="body",
                        description=prop_schema.get("description", ""),
                    )
                )
        return params

    def to_openai_tools(self) -> list[dict]:
        tools = self.parse()
        openai_tools = []
        for tool in tools:
            properties = {}
            required = []
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
