from datetime import datetime, timezone
from app.extensions import db

prompt_tags = db.Table(
    "prompt_tags",
    db.Column("prompt_id", db.Integer, db.ForeignKey("prompts.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Prompt(db.Model):
    __tablename__ = "prompts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    model_used = db.Column(db.Text, nullable=True)
    result_quality = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_favorite = db.Column(db.Boolean, default=False)
    source = db.Column(db.Text, default="user")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    category = db.relationship("Category", back_populates="prompts")
    tags = db.relationship("Tag", secondary=prompt_tags, lazy="selectin")
    optimization_logs = db.relationship("OptimizationLog", back_populates="prompt", lazy="dynamic")
    resources = db.relationship("Resource", back_populates="imported_prompt", lazy="dynamic")

    __table_args__ = (
        db.CheckConstraint("result_quality IS NULL OR (result_quality >= 1 AND result_quality <= 5)", name="ck_prompt_rating"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category_id": self.category_id,
            "category": self.category.to_dict() if self.category else None,
            "model_used": self.model_used,
            "result_quality": self.result_quality,
            "notes": self.notes,
            "is_favorite": self.is_favorite,
            "source": self.source,
            "tags": [t.to_dict() for t in self.tags],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
