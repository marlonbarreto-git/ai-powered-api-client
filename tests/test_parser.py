"""Tests for OpenAPI spec parser."""

from api_client.models import ToolDefinition
from api_client.parser import OpenAPIParser

SAMPLE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Pet Store", "version": "1.0.0"},
    "servers": [{"url": "https://api.petstore.com/v1"}],
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "summary": "List all pets",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer"},
                        "required": False,
                    }
                ],
                "responses": {"200": {"description": "OK"}},
            },
            "post": {
                "operationId": "createPet",
                "summary": "Create a pet",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "tag": {"type": "string"},
                                },
                                "required": ["name"],
                            }
                        }
                    },
                },
                "responses": {"201": {"description": "Created"}},
            },
        },
        "/pets/{petId}": {
            "get": {
                "operationId": "showPetById",
                "summary": "Info for a specific pet",
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {"200": {"description": "OK"}},
            }
        },
    },
}


class TestOpenAPIParserInit:
    def test_initialization_stores_spec(self):
        parser = OpenAPIParser(SAMPLE_SPEC)
        assert parser.spec is SAMPLE_SPEC

    def test_initialization_extracts_base_url(self):
        parser = OpenAPIParser(SAMPLE_SPEC)
        assert parser.base_url == "https://api.petstore.com/v1"

    def test_initialization_no_servers(self):
        spec = {"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0.0"}, "paths": {}}
        parser = OpenAPIParser(spec)
        assert parser.base_url == ""


class TestParseEndpoints:
    def test_parse_extracts_all_endpoints(self):
        parser = OpenAPIParser(SAMPLE_SPEC)
        tools = parser.parse()
        names = [t.name for t in tools]
        assert "listPets" in names
        assert "createPet" in names
        assert "showPetById" in names
        assert len(tools) == 3

    def test_parse_extracts_method(self):
        parser = OpenAPIParser(SAMPLE_SPEC)
        tools = parser.parse()
        tools_by_name = {t.name: t for t in tools}
        assert tools_by_name["listPets"].method == "GET"
        assert tools_by_name["createPet"].method == "POST"
        assert tools_by_name["showPetById"].method == "GET"

    def test_parse_extracts_path(self):
        parser = OpenAPIParser(SAMPLE_SPEC)
        tools = parser.parse()
        tools_by_name = {t.name: t for t in tools}
        assert tools_by_name["listPets"].path == "/pets"
        assert tools_by_name["showPetById"].path == "/pets/{petId}"


class TestParseParameters:
    def test_parse_extracts_path_parameters(self):
        parser = OpenAPIParser(SAMPLE_SPEC)
        tools = parser.parse()
        tools_by_name = {t.name: t for t in tools}
        show_pet = tools_by_name["showPetById"]
        path_params = [p for p in show_pet.parameters if p.location == "path"]
        assert len(path_params) == 1
        assert path_params[0].name == "petId"
        assert path_params[0].required is True
        assert path_params[0].type == "string"

    def test_parse_extracts_query_parameters(self):
        parser = OpenAPIParser(SAMPLE_SPEC)
        tools = parser.parse()
        tools_by_name = {t.name: t for t in tools}
        list_pets = tools_by_name["listPets"]
        query_params = [p for p in list_pets.parameters if p.location == "query"]
        assert len(query_params) == 1
        assert query_params[0].name == "limit"
        assert query_params[0].required is False
        assert query_params[0].type == "integer"

    def test_parse_extracts_request_body_schema(self):
        parser = OpenAPIParser(SAMPLE_SPEC)
        tools = parser.parse()
        tools_by_name = {t.name: t for t in tools}
        create_pet = tools_by_name["createPet"]
        body_params = [p for p in create_pet.parameters if p.location == "body"]
        assert len(body_params) == 2
        body_names = {p.name for p in body_params}
        assert "name" in body_names
        assert "tag" in body_names
        name_param = next(p for p in body_params if p.name == "name")
        tag_param = next(p for p in body_params if p.name == "tag")
        assert name_param.required is True
        assert tag_param.required is False


class TestToolDefinitions:
    def test_parse_generates_tool_definitions(self):
        parser = OpenAPIParser(SAMPLE_SPEC)
        tools = parser.parse()
        for tool in tools:
            assert isinstance(tool, ToolDefinition)
            assert tool.name
            assert tool.description
            assert tool.method in ("GET", "POST", "PUT", "PATCH", "DELETE")
            assert tool.path.startswith("/")

    def test_tool_definitions_have_base_url(self):
        parser = OpenAPIParser(SAMPLE_SPEC)
        tools = parser.parse()
        for tool in tools:
            assert tool.base_url == "https://api.petstore.com/v1"

    def test_to_openai_tools_returns_list(self):
        parser = OpenAPIParser(SAMPLE_SPEC)
        openai_tools = parser.to_openai_tools()
        assert isinstance(openai_tools, list)
        assert len(openai_tools) == 3
        for tool in openai_tools:
            assert tool["type"] == "function"
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]


class TestEdgeCases:
    def test_handles_spec_with_no_paths(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Empty API", "version": "1.0.0"},
            "paths": {},
        }
        parser = OpenAPIParser(spec)
        tools = parser.parse()
        assert tools == []

    def test_handles_endpoint_with_no_parameters(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Simple API", "version": "1.0.0"},
            "paths": {
                "/health": {
                    "get": {
                        "operationId": "healthCheck",
                        "summary": "Health check",
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            },
        }
        parser = OpenAPIParser(spec)
        tools = parser.parse()
        assert len(tools) == 1
        assert tools[0].name == "healthCheck"
        assert tools[0].parameters == []
