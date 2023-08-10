from db_manager import db
from sqlalchemy.sql import func


class ProfileStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    profile_name = db.Column(db.String(100), nullable=False)
    likes_all_time = db.Column(db.Integer, nullable=False)
    no_searches = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    def __repr__(self):
        return f'<ProfileStat {self.profile_name}>'
