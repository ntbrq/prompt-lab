from datetime import datetime, timezone
from app.extensions import db


class AIConfig(db.Model):
    __tablename__ = "ai_configs"

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.Text, nullable=False)
    display_name = db.Column(db.Text, nullable=False)
    api_key = db.Column(db.Text, nullable=False)
    base_url = db.Column(db.Text, nullable=False)
    default_model = db.Column(db.Text, nullable=False)
    available_models = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self, include_key=False):
        d = {
            "id": self.id,
            "provider": self.provider,
            "display_name": self.display_name,
            "base_url": self.base_url,
            "default_model": self.default_model,
            "available_models": self.available_models,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_key:
            d["api_key"] = self.api_key
        return d
