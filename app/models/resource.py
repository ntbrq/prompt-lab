from datetime import datetime, timezone
from app.extensions import db


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    suggested_tags = db.Column(db.Text, nullable=True)
    status = db.Column(db.Text, default="pending_review")
    source_query = db.Column(db.Text, nullable=True)
    imported_prompt_id = db.Column(db.Integer, db.ForeignKey("prompts.id"), nullable=True)
    collected_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = db.Column(db.DateTime, nullable=True)

    imported_prompt = db.relationship("Prompt", back_populates="resources")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "summary": self.summary,
            "suggested_tags": self.suggested_tags,
            "status": self.status,
            "source_query": self.source_query,
            "imported_prompt_id": self.imported_prompt_id,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
