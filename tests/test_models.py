"""Tests for data models."""

from api_client.models import ParameterDef, ToolDefinition


class TestParameterDef:
    def test_creation_with_all_fields(self):
        param = ParameterDef(
            name="petId",
            type="string",
            required=True,
            location="path",
            description="The pet identifier",
        )
        assert param.name == "petId"
        assert param.type == "string"
        assert param.required is True
        assert param.location == "path"
        assert param.description == "The pet identifier"

    def test_default_description_is_empty_string(self):
        param = ParameterDef(name="limit", type="integer", required=False, location="query")
        assert param.description == ""

    def test_equality_same_values(self):
        a = ParameterDef(name="id", type="string", required=True, location="path")
        b = ParameterDef(name="id", type="string", required=True, location="path")
        assert a == b

    def test_equality_different_values(self):
        a = ParameterDef(name="id", type="string", required=True, location="path")
        b = ParameterDef(name="id", type="integer", required=True, location="path")
        assert a != b


class TestToolDefinition:
    def test_creation_with_all_fields(self):
        params = [
            ParameterDef(name="petId", type="string", required=True, location="path"),
        ]
        tool = ToolDefinition(
            name="showPetById",
            description="Info for a specific pet",
            method="GET",
            path="/pets/{petId}",
            parameters=params,
            base_url="https://api.petstore.com/v1",
        )
        assert tool.name == "showPetById"
        assert tool.description == "Info for a specific pet"
        assert tool.method == "GET"
        assert tool.path == "/pets/{petId}"
        assert tool.parameters == params
        assert tool.base_url == "https://api.petstore.com/v1"

    def test_default_parameters_is_empty_list(self):
        tool = ToolDefinition(
            name="healthCheck",
            description="Health check",
            method="GET",
            path="/health",
        )
        assert tool.parameters == []

    def test_default_base_url_is_empty_string(self):
        tool = ToolDefinition(
            name="healthCheck",
            description="Health check",
            method="GET",
            path="/health",
        )
        assert tool.base_url == ""

    def test_parameters_list_independence(self):
        tool_a = ToolDefinition(name="a", description="a", method="GET", path="/a")
        tool_b = ToolDefinition(name="b", description="b", method="GET", path="/b")
        tool_a.parameters.append(
            ParameterDef(name="x", type="string", required=False, location="query")
        )
        assert tool_b.parameters == []

    def test_equality_same_values(self):
        tool_a = ToolDefinition(
            name="listPets", description="List pets", method="GET", path="/pets"
        )
        tool_b = ToolDefinition(
            name="listPets", description="List pets", method="GET", path="/pets"
        )
        assert tool_a == tool_b

    def test_equality_different_values(self):
        tool_a = ToolDefinition(
            name="listPets", description="List pets", method="GET", path="/pets"
        )
        tool_b = ToolDefinition(
            name="createPet", description="Create pet", method="POST", path="/pets"
        )
        assert tool_a != tool_b
