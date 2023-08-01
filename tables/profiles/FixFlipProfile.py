from db_manager import db
from sqlalchemy.sql import func


class FixFlipProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    risk = db.Column(db.String(100), nullable=False)
    budget_high = db.Column(db.Float, nullable=False)
    budget_low = db.Column(db.Float, nullable=True)
    after_repair_high = db.Column(db.Float,  nullable=False)
    after_repair_low = db.Column(db.Float,  nullable=False)
    repair_cost_high = db.Column(db.Float,  nullable=False)
    repair_cost_low = db.Column(db.Float,  nullable=False)
    coc_high = db.Column(db.Float,  nullable=False)
    coc_low = db.Column(db.Float,  nullable=False)
    deleted = db.Column(db.Boolean,  nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    def __repr__(self):
        return f'<FixFlipProfile {self.name}>'
