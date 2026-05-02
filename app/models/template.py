from datetime import datetime, timezone
from app.extensions import db

template_tags = db.Table(
    "template_tags",
    db.Column("template_id", db.Integer, db.ForeignKey("templates.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Template(db.Model):
    __tablename__ = "templates"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    source = db.Column(db.Text, default="builtin")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    category = db.relationship("Category")
    tags = db.relationship("Tag", secondary=template_tags, lazy="selectin")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "description": self.description,
            "category_id": self.category_id,
            "category": self.category.name if self.category else None,
            "tags": [t.to_dict() for t in self.tags],
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
