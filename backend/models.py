from extensions import db
from datetime import datetime, date
import uuid


def gen_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(3), default='GBR')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    xp_total = db.Column(db.Integer, default=0)
    streak_days = db.Column(db.Integer, default=0)
    last_log_date = db.Column(db.Date, nullable=True)

    entries = db.relationship('CarbonEntry', backref='user', lazy=True, cascade='all, delete-orphan')
    actions = db.relationship('UserAction', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'display_name': self.display_name or self.email.split('@')[0],
            'country': self.country,
            'xp_total': self.xp_total,
            'streak_days': self.streak_days,
            'created_at': self.created_at.isoformat(),
        }


class CarbonEntry(db.Model):
    __tablename__ = 'carbon_entries'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    entry_date = db.Column(db.Date, default=date.today)
    transport_kg = db.Column(db.Float, default=0.0)
    home_energy_kg = db.Column(db.Float, default=0.0)
    diet_kg = db.Column(db.Float, default=0.0)
    shopping_kg = db.Column(db.Float, default=0.0)
    total_kg = db.Column(db.Float, default=0.0)
    raw_inputs = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'entry_date': self.entry_date.isoformat(),
            'transport_kg': round(self.transport_kg, 2),
            'home_energy_kg': round(self.home_energy_kg, 2),
            'diet_kg': round(self.diet_kg, 2),
            'shopping_kg': round(self.shopping_kg, 2),
            'total_kg': round(self.total_kg, 2),
        }


class UserAction(db.Model):
    __tablename__ = 'user_actions'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    action_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pledged')  # pledged, completed, skipped
    committed_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    co2_saved_kg = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id': self.id,
            'action_id': self.action_id,
            'status': self.status,
            'committed_at': self.committed_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'co2_saved_kg': self.co2_saved_kg,
        }
