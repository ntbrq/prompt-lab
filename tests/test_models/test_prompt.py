from app.models import Prompt, Tag, Category
from app.extensions import db


class TestPromptModel:
    def test_create_prompt(self, app, client):
        with app.app_context():
            prompt = Prompt(title="Test", content="Content")
            db.session.add(prompt)
            db.session.commit()
            assert prompt.id is not None
            assert prompt.source == "user"
            assert prompt.is_favorite is False

    def test_prompt_with_tags(self, app, client, sample_tag):
        with app.app_context():
            tag = Tag.query.filter_by(name="python").first()
            prompt = Prompt(title="Tagged", content="Content", tags=[tag])
            db.session.add(prompt)
            db.session.commit()
            assert len(prompt.tags) == 1
            assert prompt.tags[0].name == "python"

    def test_prompt_with_category(self, app, client, sample_category):
        with app.app_context():
            cat = Category.query.filter_by(name="TestCat").first()
            prompt = Prompt(title="Categorized", content="Content", category_id=cat.id)
            db.session.add(prompt)
            db.session.commit()
            assert prompt.category.name == "TestCat"

    def test_prompt_to_dict(self, app, client):
        with app.app_context():
            prompt = Prompt(title="Dict Test", content="Content", model_used="gpt-4", result_quality=4)
            db.session.add(prompt)
            db.session.commit()
            d = prompt.to_dict()
            assert d["title"] == "Dict Test"
            assert d["model_used"] == "gpt-4"
            assert d["result_quality"] == 4
            assert "tags" in d
            assert "created_at" in d

    def test_prompt_rating_constraint(self, app, client):
        with app.app_context():
            prompt = Prompt(title="Bad Rating", content="Content", result_quality=6)
            db.session.add(prompt)
            try:
                db.session.commit()
                assert False, "Should have raised"
            except Exception:
                db.session.rollback()

    def test_cascade_delete_tag(self, app, client, sample_tag):
        with app.app_context():
            tag = Tag.query.filter_by(name="python").first()
            prompt = Prompt(title="Cascade", content="Content", tags=[tag])
            db.session.add(prompt)
            db.session.commit()
            prompt_id = prompt.id
            db.session.delete(prompt)
            db.session.commit()
            assert Prompt.query.get(prompt_id) is None


class TestTagModel:
    def test_create_tag(self, app, client):
        with app.app_context():
            tag = Tag(name="unique_tag", color="#ff0000")
            db.session.add(tag)
            db.session.commit()
            assert tag.id is not None
            assert tag.to_dict()["name"] == "unique_tag"

    def test_unique_tag_name(self, app, client, sample_tag):
        with app.app_context():
            tag = Tag(name="python")
            db.session.add(tag)
            try:
                db.session.commit()
                assert False, "Should have raised"
            except Exception:
                db.session.rollback()


class TestCategoryModel:
    def test_create_category(self, app, client):
        with app.app_context():
            cat = Category(name="NewCat", description="Desc", sort_order=5)
            db.session.add(cat)
            db.session.commit()
            assert cat.to_dict()["name"] == "NewCat"
            assert cat.to_dict()["sort_order"] == 5
