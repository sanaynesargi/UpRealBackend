from db_manager import db
from sqlalchemy.sql import func


class RentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    risk = db.Column(db.String(100), nullable=False)
    budget_high = db.Column(db.Float, nullable=False)
    budget_low = db.Column(db.Float, nullable=True)
    appreciation_high = db.Column(db.Float,  nullable=False)
    appreciation_low = db.Column(db.Float,  nullable=False)
    cashflow_high = db.Column(db.Float,  nullable=False)
    cashflow_low = db.Column(db.Float,  nullable=False)
    coc_high = db.Column(db.Float,  nullable=False)
    coc_low = db.Column(db.Float,  nullable=False)
    main_high = db.Column(db.Float,  nullable=False)
    main_low = db.Column(db.Float,  nullable=False)
    hold_high = db.Column(db.Integer,  nullable=False)
    hold_low = db.Column(db.Integer,  nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    def __repr__(self):
        return f'<RentProfile {self.name}>'
