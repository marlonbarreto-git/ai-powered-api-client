from dataclasses import dataclass, field


@dataclass
class ParameterDef:
    """Definition of a single API parameter extracted from an OpenAPI spec."""

    name: str
    type: str
    required: bool
    location: str  # "path", "query", "body"
    description: str = ""


@dataclass
class ToolDefinition:
    """LLM-callable tool describing a single API endpoint."""

    name: str
    description: str
    method: str
    path: str
    parameters: list[ParameterDef] = field(default_factory=list)
    base_url: str = ""
