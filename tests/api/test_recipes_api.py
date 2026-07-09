"""Tests for /api/recipes endpoint — recipe registry exposed as live API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from videoforge.api.app import create_app


def _client():
    return TestClient(create_app())


class TestRecipesEndpoint:
    """GET /api/recipes contract tests."""

    def test_returns_200(self):
        resp = _client().get("/api/recipes")
        assert resp.status_code == 200

    def test_content_type_json(self):
        resp = _client().get("/api/recipes")
        assert resp.headers["content-type"].startswith("application/json")

    def test_returns_list(self):
        data = _client().get("/api/recipes").json()
        assert isinstance(data, list)

    def test_returns_all_recipes(self):
        data = _client().get("/api/recipes").json()
        assert len(data) >= 9

    def test_each_recipe_has_required_fields(self):
        data = _client().get("/api/recipes").json()
        for r in data:
            assert r["id"], f"Missing id: {r}"
            assert r["name"], f"Missing name: {r['id']}"
            assert r["sceneKind"], f"Missing sceneKind: {r['id']}"
            assert r["preferredEngine"], f"Missing preferredEngine: {r['id']}"
            assert isinstance(r["tags"], list)

    def test_each_recipe_has_camelCase_keys(self):
        data = _client().get("/api/recipes").json()
        expected_keys = {
            "id", "name", "description", "sceneKind", "preferredEngine",
            "fallbackEngines", "allowedInputs", "entrance", "exit", "tags",
        }
        for r in data:
            assert set(r.keys()) == expected_keys, f"Bad keys in recipe {r['id']}"

    def test_allowed_inputs_have_required_keys(self):
        data = _client().get("/api/recipes").json()
        for r in data:
            for inp in r["allowedInputs"]:
                assert "key" in inp
                assert "type" in inp
                assert "required" in inp
                assert "description" in inp

    def test_known_recipe_map3d(self):
        data = _client().get("/api/recipes").json()
        r = next((r for r in data if r["id"] == "map3d"), None)
        assert r is not None
        assert r["sceneKind"] == "map3d"
        assert r["preferredEngine"] == "manim"
        assert "geospatial" in r["tags"]

    def test_known_recipe_document_highlight(self):
        data = _client().get("/api/recipes").json()
        r = next((r for r in data if r["id"] == "document-highlight"), None)
        assert r is not None
        assert r["sceneKind"] == "title"
        assert r["preferredEngine"] == "remotion"

    def test_known_recipe_screenflow(self):
        data = _client().get("/api/recipes").json()
        r = next((r for r in data if r["id"] == "screenflow"), None)
        assert r is not None
        assert r["sceneKind"] == "comparison"
        assert r["preferredEngine"] == "remotion"

    def test_recipes_sorted_by_id(self):
        data = _client().get("/api/recipes").json()
        ids = [r["id"] for r in data]
        assert ids == sorted(ids)

    def test_duplicate_call_stable(self):
        client = _client()
        a = client.get("/api/recipes").json()
        b = client.get("/api/recipes").json()
        assert a == b
