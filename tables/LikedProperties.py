from db_manager import db
from sqlalchemy.sql import func


class LikedPropertiesv2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prop_id = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    imageUrl = db.Column(db.String(100), nullable=False)
    beds = db.Column(db.Integer, nullable=False)
    baths = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    formattedPrice = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    apiInfo = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(100), nullable=False)

    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    def __repr__(self):
        return f'<LikedProperty {self.prop_id}>'
