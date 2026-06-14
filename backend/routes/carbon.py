from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date
from extensions import db
from models import User, CarbonEntry
from services.calculator import calculate_footprint
from services.gamification import update_streak, award_xp, check_badges, BADGES

carbon_bp = Blueprint('carbon', __name__, url_prefix='/api/carbon')


@carbon_bp.route('/calculate', methods=['POST'])
def calculate():
    """Public endpoint — calculate without saving."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    result = calculate_footprint(data)
    return jsonify(result), 200


@carbon_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit():
    """Authenticated — calculate and save entry for logged-in user."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    result = calculate_footprint(data)

    entry = CarbonEntry(
        user_id=user_id,
        entry_date=date.today(),
        transport_kg=result['transport_kg'],
        home_energy_kg=result['home_energy_kg'],
        diet_kg=result['diet_kg'],
        shopping_kg=result['shopping_kg'],
        total_kg=result['total_kg'],
        raw_inputs=data,
    )
    db.session.add(entry)

    # Update streak and award XP
    streak, xp_earned = update_streak(user)
    award_xp(user, xp_earned + 25)  # 25 XP for submitting
    db.session.commit()

    # Check badges
    all_entries = CarbonEntry.query.filter_by(user_id=user_id).order_by(CarbonEntry.created_at.desc()).all()
    from models import UserAction
    all_actions = UserAction.query.filter_by(user_id=user_id).all()
    earned_badge_ids = check_badges(user, all_entries, all_actions)
    earned_badges = [b for b in BADGES if b['id'] in earned_badge_ids]

    return jsonify({
        **result,
        'entry_id': entry.id,
        'streak_days': user.streak_days,
        'xp_earned': xp_earned + 25,
        'xp_total': user.xp_total,
        'new_badges': earned_badges,
    }), 201


@carbon_bp.route('/history', methods=['GET'])
@jwt_required()
def history():
    """Return all carbon entries for the logged-in user."""
    user_id = get_jwt_identity()
    entries = CarbonEntry.query.filter_by(user_id=user_id)\
        .order_by(CarbonEntry.entry_date.asc()).all()
    return jsonify({'entries': [e.to_dict() for e in entries]}), 200


@carbon_bp.route('/summary', methods=['GET'])
@jwt_required()
def summary():
    """Return latest entry + trend data for dashboard."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    entries = CarbonEntry.query.filter_by(user_id=user_id)\
        .order_by(CarbonEntry.entry_date.desc()).all()

    if not entries:
        return jsonify({'has_data': False}), 200

    latest = entries[0]
    previous = entries[1] if len(entries) > 1 else None

    trend_pct = None
    if previous and previous.total_kg > 0:
        trend_pct = round(((latest.total_kg - previous.total_kg) / previous.total_kg) * 100, 1)

    from services.gamification import get_xp_level, check_badges, BADGES
    from models import UserAction
    all_actions = UserAction.query.filter_by(user_id=user_id).all()
    earned_badge_ids = check_badges(user, entries, all_actions)
    earned_badges = [b for b in BADGES if b['id'] in earned_badge_ids]

    return jsonify({
        'has_data': True,
        'latest': latest.to_dict(),
        'trend_pct': trend_pct,
        'streak_days': user.streak_days,
        'xp_level': get_xp_level(user.xp_total or 0),
        'badges': earned_badges,
        'entries_count': len(entries),
    }), 200
