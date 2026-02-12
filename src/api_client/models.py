from dataclasses import dataclass, field


@dataclass
class ParameterDef:
    name: str
    type: str
    required: bool
    location: str  # "path", "query", "body"
    description: str = ""


@dataclass
class ToolDefinition:
    name: str
    description: str
    method: str
    path: str
    parameters: list[ParameterDef] = field(default_factory=list)
    base_url: str = ""
