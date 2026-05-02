from datetime import datetime, timezone
from app.extensions import db


class OptimizationLog(db.Model):
    __tablename__ = "optimization_logs"

    id = db.Column(db.Integer, primary_key=True)
    original_prompt_id = db.Column(db.Integer, db.ForeignKey("prompts.id"), nullable=True)
    original_content = db.Column(db.Text, nullable=False)
    optimized_content = db.Column(db.Text, nullable=False)
    model_used = db.Column(db.Text, nullable=False)
    optimization_type = db.Column(db.Text, nullable=False)
    context = db.Column(db.Text, nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    user_rating = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    prompt = db.relationship("Prompt", back_populates="optimization_logs")

    __table_args__ = (
        db.CheckConstraint("user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5)", name="ck_optlog_rating"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "original_prompt_id": self.original_prompt_id,
            "original_content": self.original_content,
            "optimized_content": self.optimized_content,
            "model_used": self.model_used,
            "optimization_type": self.optimization_type,
            "context": self.context,
            "explanation": self.explanation,
            "user_rating": self.user_rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
