from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
from extensions import db
from models import User, CarbonEntry, UserAction
from services.recommender import get_recommendations, get_cold_start_recommendations, load_actions
from services.gamification import award_xp, check_badges, BADGES
import json

insights_bp = Blueprint('insights', __name__, url_prefix='/api/insights')


@insights_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def recommendations():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get latest entry for user profile
    latest_entry = CarbonEntry.query.filter_by(user_id=user_id)\
        .order_by(CarbonEntry.entry_date.desc()).first()

    # Get already committed actions
    committed = UserAction.query.filter_by(user_id=user_id).all()
    committed_ids = [a.action_id for a in committed]

    if latest_entry:
        recs = get_recommendations(latest_entry.to_dict(), committed_ids, limit=6)
    else:
        recs = get_cold_start_recommendations(limit=6)

    return jsonify({'recommendations': recs}), 200


@insights_bp.route('/actions/commit', methods=['POST'])
@jwt_required()
def commit_action():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    action_id = data.get('action_id')

    if not action_id:
        return jsonify({'error': 'action_id is required'}), 400

    # Check action exists in catalogue
    all_actions = load_actions()
    action_data = next((a for a in all_actions if a['id'] == action_id), None)
    if not action_data:
        return jsonify({'error': 'Action not found'}), 404

    # Check not already committed
    existing = UserAction.query.filter_by(user_id=user_id, action_id=action_id).first()
    if existing:
        return jsonify({'error': 'Already committed to this action', 'action': existing.to_dict()}), 409

    ua = UserAction(
        user_id=user_id,
        action_id=action_id,
        status='pledged',
        co2_saved_kg=action_data['co2_saving_kg_month'],
    )
    db.session.add(ua)

    xp_gain = 75
    award_xp(user, xp_gain)
    db.session.commit()

    # Check for new badges
    all_entries = CarbonEntry.query.filter_by(user_id=user_id).order_by(CarbonEntry.created_at.desc()).all()
    all_user_actions = UserAction.query.filter_by(user_id=user_id).all()
    earned_badge_ids = check_badges(user, all_entries, all_user_actions)
    new_badges = [b for b in BADGES if b['id'] in earned_badge_ids]

    return jsonify({
        'action': ua.to_dict(),
        'xp_earned': xp_gain,
        'xp_total': user.xp_total,
        'new_badges': new_badges,
    }), 201


@insights_bp.route('/actions/complete', methods=['POST'])
@jwt_required()
def complete_action():
    user_id = get_jwt_identity()
    data = request.get_json()
    action_id = data.get('action_id')

    ua = UserAction.query.filter_by(user_id=user_id, action_id=action_id).first()
    if not ua:
        return jsonify({'error': 'Action pledge not found'}), 404

    ua.status = 'completed'
    ua.completed_at = datetime.utcnow()
    user = User.query.get(user_id)
    award_xp(user, 100)  # Bonus XP for completing
    db.session.commit()

    return jsonify({'action': ua.to_dict(), 'xp_earned': 100, 'xp_total': user.xp_total}), 200


@insights_bp.route('/actions/my', methods=['GET'])
@jwt_required()
def my_actions():
    user_id = get_jwt_identity()
    user_actions = UserAction.query.filter_by(user_id=user_id)\
        .order_by(UserAction.committed_at.desc()).all()

    all_catalogue = load_actions()
    catalogue_map = {a['id']: a for a in all_catalogue}

    result = []
    for ua in user_actions:
        action_detail = catalogue_map.get(ua.action_id, {})
        result.append({**ua.to_dict(), **action_detail})

    return jsonify({'actions': result}), 200
