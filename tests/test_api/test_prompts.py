import json


class TestPromptsAPI:
    def test_list_empty(self, client):
        r = client.get("/api/prompts")
        assert r.status_code == 200
        assert r.json["total"] == 0
        assert r.json["items"] == []

    def test_create_and_get(self, client):
        r = client.post("/api/prompts", json={
            "title": "Hello", "content": "World"
        })
        assert r.status_code == 201
        prompt_id = r.json["id"]

        r = client.get(f"/api/prompts/{prompt_id}")
        assert r.status_code == 200
        assert r.json["title"] == "Hello"

    def test_create_validation(self, client):
        r = client.post("/api/prompts", json={"title": "No content"})
        assert r.status_code == 400

        r = client.post("/api/prompts", json={"content": "No title"})
        assert r.status_code == 400

    def test_update_prompt(self, client, sample_prompt):
        pid = sample_prompt["id"]
        r = client.put(f"/api/prompts/{pid}", json={"title": "Updated"})
        assert r.status_code == 200
        assert r.json["title"] == "Updated"

    def test_delete_prompt(self, client, sample_prompt):
        pid = sample_prompt["id"]
        r = client.delete(f"/api/prompts/{pid}")
        assert r.status_code == 204

        r = client.get(f"/api/prompts/{pid}")
        assert r.status_code == 404

    def test_favorite_toggle(self, client, sample_prompt):
        pid = sample_prompt["id"]
        r = client.post(f"/api/prompts/{pid}/favorite")
        assert r.json["is_favorite"] is True

        r = client.post(f"/api/prompts/{pid}/favorite")
        assert r.json["is_favorite"] is False

    def test_create_with_tags(self, client, sample_tag):
        r = client.post("/api/prompts", json={
            "title": "Tagged", "content": "Content", "tag_ids": [sample_tag["id"]]
        })
        assert r.status_code == 201
        assert len(r.json["tags"]) == 1
        assert r.json["tags"][0]["name"] == "python"

    def test_list_with_filter(self, client):
        client.post("/api/prompts", json={"title": "A", "content": "Content A", "source": "user"})
        client.post("/api/prompts", json={"title": "B", "content": "Content B", "source": "imported"})

        r = client.get("/api/prompts?source=user")
        assert all(p["source"] == "user" for p in r.json["items"])

    def test_pagination(self, client):
        for i in range(25):
            client.post("/api/prompts", json={"title": f"P{i}", "content": "C"})
        r = client.get("/api/prompts?page=1&per_page=10")
        assert len(r.json["items"]) == 10
        assert r.json["total"] == 25
        assert r.json["pages"] == 3

    def test_htmx_list(self, client, sample_prompt):
        r = client.get("/api/prompts", headers={"HX-Request": "true"})
        assert r.status_code == 200
        assert b"Test Prompt" in r.data


class TestTagsAPI:
    def test_crud(self, client):
        r = client.post("/api/tags", json={"name": "test_tag"})
        assert r.status_code == 201

        r = client.get("/api/tags")
        assert any(t["name"] == "test_tag" for t in r.json)

        r = client.post("/api/tags", json={"name": "test_tag"})
        assert r.status_code == 409

    def test_usage_count(self, client, sample_tag, sample_prompt):
        client.put(f"/api/prompts/{sample_prompt['id']}", json={"tag_ids": [sample_tag["id"]]})
        r = client.get("/api/tags")
        assert any(t["usage_count"] > 0 for t in r.json)


class TestCategoriesAPI:
    def test_crud(self, client):
        r = client.post("/api/categories", json={"name": "API Test"})
        assert r.status_code == 201
        cat_id = r.json["id"]

        r = client.put(f"/api/categories/{cat_id}", json={"name": "Renamed"})
        assert r.json["name"] == "Renamed"

        r = client.delete(f"/api/categories/{cat_id}")
        assert r.status_code == 204

    def test_duplicate(self, client, sample_category):
        r = client.post("/api/categories", json={"name": "TestCat"})
        assert r.status_code == 409


class TestSearchAPI:
    def test_empty_query(self, client):
        r = client.get("/api/search?q=")
        assert r.json["total"] == 0

    def test_search_results(self, client):
        client.post("/api/prompts", json={"title": "Python Helper", "content": "Help with Python code"})
        r = client.get("/api/search?q=Python")
        # FTS5 or LIKE fallback should find it
        assert r.status_code == 200

    def test_htmx_search(self, client):
        client.post("/api/prompts", json={"title": "Searchable", "content": "Test content"})
        r = client.get("/api/search?q=Searchable", headers={"HX-Request": "true"})
        assert r.status_code == 200


class TestExportImport:
    def test_export_json(self, client, sample_prompt):
        r = client.get("/api/export?format=json")
        assert r.status_code == 200
        assert r.json["version"] == "1.0"
        assert len(r.json["prompts"]) == 1

    def test_export_markdown(self, client, sample_prompt):
        r = client.get("/api/export?format=markdown")
        assert r.status_code == 200
        assert b"# Prompt:" in r.data

    def test_import_json(self, client):
        import io
        export_data = {
            "version": "1.0",
            "prompts": [
                {"title": "Imported", "content": "From JSON", "tags": ["imported"]}
            ]
        }
        file_data = json.dumps(export_data).encode("utf-8")
        data = {"file": (io.BytesIO(file_data), "test.json")}
        r = client.post("/api/import", data=data, content_type="multipart/form-data")
        assert r.status_code == 200
        assert r.json["imported"] == 1
