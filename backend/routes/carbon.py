"""
Carbon footprint calculation and tracking routes.

Provides endpoints for calculating carbon emissions, saving entries,
retrieving history, and generating dashboard summary data.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date
from extensions import db
from models import User, CarbonEntry, UserAction
from services.calculator import calculate_footprint
from services.gamification import update_streak, award_xp, check_badges, BADGES

logger = logging.getLogger('carbontrace.carbon')

carbon_bp = Blueprint('carbon', __name__, url_prefix='/api/carbon')


def _validate_inputs(data: dict) -> str | None:
    """
    Validate carbon calculation input data structure.

    Args:
        data: Raw input dictionary from the client.

    Returns:
        Error message string if invalid, None if valid.
    """
    if not data:
        return 'No input data provided'

    required_sections = ['transport', 'home_energy', 'diet', 'shopping']
    for section in required_sections:
        if not isinstance(data.get(section), dict):
            return f'Missing or invalid section: {section}'

    return None


@carbon_bp.route('/calculate', methods=['POST'])
def calculate():
    """
    Calculate carbon footprint without saving (public endpoint).

    Expects JSON with transport, home_energy, diet, shopping sections.
    Returns: Emission breakdown with benchmarks and percentile (200).
    """
    data = request.get_json()
    validation_err = _validate_inputs(data)
    if validation_err:
        return jsonify({'error': validation_err}), 400

    try:
        result = calculate_footprint(data)
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning('Calculation error: %s', str(exc))
        return jsonify({'error': 'Invalid input values'}), 400

    return jsonify(result), 200


@carbon_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit():
    """
    Calculate and save a carbon footprint entry for the authenticated user.

    Requires: Valid JWT Bearer token.
    Returns: Emission breakdown + XP earned + badges (201).
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    validation_err = _validate_inputs(data)
    if validation_err:
        return jsonify({'error': validation_err}), 400

    try:
        result = calculate_footprint(data)
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning('Submit calculation error for user %s: %s', user_id, str(exc))
        return jsonify({'error': 'Invalid input values'}), 400

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
    base_xp = 25  # XP for submitting an entry
    award_xp(user, xp_earned + base_xp)
    db.session.commit()

    # Check badges
    all_entries = CarbonEntry.query.filter_by(user_id=user_id)\
        .order_by(CarbonEntry.created_at.desc()).all()
    all_actions = UserAction.query.filter_by(user_id=user_id).all()
    earned_badge_ids = check_badges(user, all_entries, all_actions)
    earned_badges = [b for b in BADGES if b['id'] in earned_badge_ids]

    logger.info('Entry submitted by user %s: %.1f kg CO2e', user_id, result['total_kg'])

    return jsonify({
        **result,
        'entry_id': entry.id,
        'streak_days': user.streak_days,
        'xp_earned': xp_earned + base_xp,
        'xp_total': user.xp_total,
        'new_badges': earned_badges,
    }), 201


@carbon_bp.route('/history', methods=['GET'])
@jwt_required()
def history():
    """
    Retrieve all carbon entries for the authenticated user.

    Returns entries sorted by date ascending for timeline rendering.
    """
    user_id = get_jwt_identity()
    entries = CarbonEntry.query.filter_by(user_id=user_id)\
        .order_by(CarbonEntry.entry_date.asc()).all()
    return jsonify({'entries': [e.to_dict() for e in entries]}), 200


@carbon_bp.route('/summary', methods=['GET'])
@jwt_required()
def summary():
    """
    Generate dashboard summary data for the authenticated user.

    Returns: Latest entry, trend percentage, XP level, badges,
    and entry count. Returns has_data=False if no entries exist.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    entries = CarbonEntry.query.filter_by(user_id=user_id)\
        .order_by(CarbonEntry.entry_date.desc()).all()

    if not entries:
        return jsonify({'has_data': False}), 200

    latest = entries[0]
    previous = entries[1] if len(entries) > 1 else None

    trend_pct = None
    if previous and previous.total_kg > 0:
        trend_pct = round(
            ((latest.total_kg - previous.total_kg) / previous.total_kg) * 100, 1
        )

    from services.gamification import get_xp_level
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
