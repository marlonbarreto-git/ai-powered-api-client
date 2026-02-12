from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api_client.caller import APICaller, APIRequest, APIResponse
from api_client.models import ParameterDef, ToolDefinition


class TestAPICallerInit:
    def test_default_headers_empty(self):
        caller = APICaller()
        assert caller.default_headers == {}

    def test_custom_default_headers(self):
        headers = {"Authorization": "Bearer token123", "Accept": "application/json"}
        caller = APICaller(default_headers=headers)
        assert caller.default_headers == headers


class TestBuildRequest:
    def setup_method(self):
        self.caller = APICaller()

    def test_path_params_substituted(self):
        tool = ToolDefinition(
            name="get_user",
            description="Get a user",
            method="GET",
            path="/users/{user_id}",
            parameters=[
                ParameterDef(name="user_id", type="string", required=True, location="path"),
            ],
        )
        request = self.caller.build_request(tool, {"user_id": "42"})
        assert request.url == "/users/42"
        assert request.method == "GET"

    def test_query_params_added(self):
        tool = ToolDefinition(
            name="list_users",
            description="List users",
            method="GET",
            path="/users",
            parameters=[
                ParameterDef(name="page", type="integer", required=False, location="query"),
                ParameterDef(name="limit", type="integer", required=False, location="query"),
            ],
        )
        request = self.caller.build_request(tool, {"page": 2, "limit": 10})
        assert request.query_params == {"page": 2, "limit": 10}

    def test_body_params_create_json_body(self):
        tool = ToolDefinition(
            name="create_user",
            description="Create a user",
            method="POST",
            path="/users",
            parameters=[
                ParameterDef(name="name", type="string", required=True, location="body"),
                ParameterDef(name="email", type="string", required=True, location="body"),
            ],
        )
        request = self.caller.build_request(tool, {"name": "Alice", "email": "alice@example.com"})
        assert request.json_body == {"name": "Alice", "email": "alice@example.com"}

    def test_base_url_prepended(self):
        tool = ToolDefinition(
            name="get_user",
            description="Get a user",
            method="GET",
            path="/users/{user_id}",
            base_url="https://api.example.com",
            parameters=[
                ParameterDef(name="user_id", type="string", required=True, location="path"),
            ],
        )
        request = self.caller.build_request(tool, {"user_id": "7"})
        assert request.url == "https://api.example.com/users/7"

    def test_mixed_param_types(self):
        tool = ToolDefinition(
            name="update_user",
            description="Update a user",
            method="PUT",
            path="/users/{user_id}",
            base_url="https://api.example.com",
            parameters=[
                ParameterDef(name="user_id", type="string", required=True, location="path"),
                ParameterDef(name="include", type="string", required=False, location="query"),
                ParameterDef(name="name", type="string", required=True, location="body"),
                ParameterDef(name="email", type="string", required=False, location="body"),
            ],
        )
        request = self.caller.build_request(
            tool,
            {"user_id": "99", "include": "profile", "name": "Bob", "email": "bob@test.com"},
        )
        assert request.url == "https://api.example.com/users/99"
        assert request.query_params == {"include": "profile"}
        assert request.json_body == {"name": "Bob", "email": "bob@test.com"}
        assert request.method == "PUT"

    def test_missing_optional_params_skipped(self):
        tool = ToolDefinition(
            name="list_users",
            description="List users",
            method="GET",
            path="/users",
            parameters=[
                ParameterDef(name="page", type="integer", required=False, location="query"),
                ParameterDef(name="limit", type="integer", required=False, location="query"),
            ],
        )
        request = self.caller.build_request(tool, {"page": 1})
        assert request.query_params == {"page": 1}
        assert "limit" not in request.query_params

    def test_no_body_params_yields_none_json_body(self):
        tool = ToolDefinition(
            name="get_user",
            description="Get a user",
            method="GET",
            path="/users/{user_id}",
            parameters=[
                ParameterDef(name="user_id", type="string", required=True, location="path"),
            ],
        )
        request = self.caller.build_request(tool, {"user_id": "1"})
        assert request.json_body is None

    def test_default_headers_included_in_request(self):
        caller = APICaller(default_headers={"Authorization": "Bearer abc"})
        tool = ToolDefinition(
            name="get_user",
            description="Get a user",
            method="GET",
            path="/users",
        )
        request = caller.build_request(tool, {})
        assert request.headers == {"Authorization": "Bearer abc"}


class TestAPIResponse:
    def test_response_has_status_code(self):
        resp = APIResponse(status_code=200, body={"ok": True})
        assert resp.status_code == 200

    def test_response_has_body(self):
        resp = APIResponse(status_code=200, body={"data": [1, 2, 3]})
        assert resp.body == {"data": [1, 2, 3]}

    def test_response_has_headers(self):
        resp = APIResponse(
            status_code=200,
            body="ok",
            headers={"content-type": "text/plain"},
        )
        assert resp.headers == {"content-type": "text/plain"}

    def test_response_default_headers_empty(self):
        resp = APIResponse(status_code=404, body="not found")
        assert resp.headers == {}


class TestAPICallerCall:
    @pytest.mark.asyncio
    async def test_call_returns_api_response_json(self):
        tool = ToolDefinition(
            name="get_user",
            description="Get a user",
            method="GET",
            path="/users/1",
            base_url="https://api.example.com",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "Alice"}
        mock_response.headers = {"content-type": "application/json"}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("api_client.caller.httpx.AsyncClient", return_value=mock_client):
            caller = APICaller()
            result = await caller.call(tool, {})

        assert isinstance(result, APIResponse)
        assert result.status_code == 200
        assert result.body == {"id": 1, "name": "Alice"}

    @pytest.mark.asyncio
    async def test_call_returns_text_for_non_json(self):
        tool = ToolDefinition(
            name="get_page",
            description="Get a page",
            method="GET",
            path="/page",
            base_url="https://example.com",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Hello</html>"
        mock_response.headers = {"content-type": "text/html"}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("api_client.caller.httpx.AsyncClient", return_value=mock_client):
            caller = APICaller()
            result = await caller.call(tool, {})

        assert result.status_code == 200
        assert result.body == "<html>Hello</html>"

    @pytest.mark.asyncio
    async def test_call_passes_correct_params_to_httpx(self):
        tool = ToolDefinition(
            name="create_user",
            description="Create a user",
            method="POST",
            path="/users",
            base_url="https://api.example.com",
            parameters=[
                ParameterDef(name="q", type="string", required=False, location="query"),
                ParameterDef(name="name", type="string", required=True, location="body"),
            ],
        )

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1}
        mock_response.headers = {"content-type": "application/json"}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("api_client.caller.httpx.AsyncClient", return_value=mock_client):
            caller = APICaller(default_headers={"X-Api-Key": "secret"})
            await caller.call(tool, {"q": "search", "name": "Bob"})

        mock_client.request.assert_called_once_with(
            method="POST",
            url="https://api.example.com/users",
            params={"q": "search"},
            json={"name": "Bob"},
            headers={"X-Api-Key": "secret"},
        )
