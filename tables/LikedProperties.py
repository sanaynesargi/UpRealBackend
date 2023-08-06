from db_manager import db
from sqlalchemy.sql import func


class LikedProperties(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prop_id = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    def __repr__(self):
        return f'<LikedProperty {self.prop_id}>'
