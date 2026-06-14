"""
Seed script — creates a demo account with 6 months of synthetic
carbon footprint data for testing and live demos.

Run: python seed_demo.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from extensions import db
from models import User, CarbonEntry, UserAction
from services.gamification import BADGES
from datetime import date, timedelta
import bcrypt, random, uuid

DEMO_EMAIL = 'demo@carbontrace.app'
DEMO_PASSWORD = 'demo1234'

MONTHS_DATA = [
    # (transport, home_energy, diet, shopping)  — oldest first
    (310.0, 180.0, 165.0, 62.0),
    (295.0, 175.0, 160.0, 45.0),
    (280.0, 168.0, 152.0, 38.0),
    (260.0, 165.0, 148.0, 35.0),
    (245.0, 158.0, 140.0, 30.0),
    (230.0, 152.0, 135.0, 28.0),
]

DEMO_ACTIONS = [
    'switch-public-transit',
    'plant-based-2days',
    'led-bulbs',
    'reduce-food-waste',
    'buy-secondhand',
]

def seed():
    app = create_app()
    with app.app_context():
        # Remove existing demo user
        existing = User.query.filter_by(email=DEMO_EMAIL).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            print(f"Removed existing demo user.")

        # Create demo user
        hashed = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
        user = User(
            id=str(uuid.uuid4()),
            email=DEMO_EMAIL,
            password_hash=hashed,
            display_name='Alex (Demo)',
            country='GB',
            xp_total=875,
            streak_days=14,
            last_log_date=date.today(),
        )
        db.session.add(user)
        db.session.flush()

        # Add 6 months of entries
        today = date.today()
        for i, (t, h, d, s) in enumerate(MONTHS_DATA):
            entry_date = today - timedelta(days=(len(MONTHS_DATA) - 1 - i) * 30)
            noise = lambda: random.uniform(-5, 5)
            entry = CarbonEntry(
                id=str(uuid.uuid4()),
                user_id=user.id,
                entry_date=entry_date,
                transport_kg=round(t + noise(), 2),
                home_energy_kg=round(h + noise(), 2),
                diet_kg=round(d + noise(), 2),
                shopping_kg=round(s + noise(), 2),
                total_kg=round(t + h + d + s + noise(), 2),
                raw_inputs={},
            )
            db.session.add(entry)

        # Add committed actions
        for action_id in DEMO_ACTIONS:
            ua = UserAction(
                id=str(uuid.uuid4()),
                user_id=user.id,
                action_id=action_id,
                status='completed' if action_id in DEMO_ACTIONS[:2] else 'pledged',
                co2_saved_kg=47.0,
            )
            db.session.add(ua)

        db.session.commit()
        print(f"✅ Demo account created!")
        print(f"   Email:    {DEMO_EMAIL}")
        print(f"   Password: {DEMO_PASSWORD}")
        print(f"   Entries:  {len(MONTHS_DATA)} months of data")
        print(f"   Actions:  {len(DEMO_ACTIONS)} actions seeded")

if __name__ == '__main__':
    seed()
