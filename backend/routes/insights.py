"""
Insights and green action recommendation routes.

Provides AI-powered personalized recommendations ranked by impact-to-effort
ratio, action pledging/completion tracking, and potential impact summaries.
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, CarbonEntry, UserAction
from services.recommender import (
    get_recommendations,
    get_cold_start_recommendations,
    load_actions,
)
from services.gamification import award_xp, check_badges, BADGES

logger = logging.getLogger('carbontrace.insights')

insights_bp = Blueprint('insights', __name__, url_prefix='/api/insights')


@insights_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def recommendations():
    """
    Retrieve personalized green action recommendations.

    Ranks actions by the user's highest-emission category and
    excludes already-committed actions. Falls back to cold-start
    recommendations for users with no carbon entries.

    Returns: List of ranked recommendation objects (200).
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
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
    """
    Pledge to perform a green action.

    Validates that the action exists in the catalogue and hasn't
    already been committed. Awards 75 XP on successful pledge.

    Expects JSON: {action_id}
    Returns: Action details + XP earned + new badges (201).
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    action_id = data.get('action_id', '').strip()
    if not action_id:
        return jsonify({'error': 'action_id is required'}), 400

    # Validate action exists in catalogue
    all_actions = load_actions()
    action_data = next((a for a in all_actions if a['id'] == action_id), None)
    if not action_data:
        return jsonify({'error': 'Action not found in catalogue'}), 404

    # Prevent duplicate commitments
    existing = UserAction.query.filter_by(
        user_id=user_id, action_id=action_id
    ).first()
    if existing:
        return jsonify({
            'error': 'Already committed to this action',
            'action': existing.to_dict(),
        }), 409

    user_action = UserAction(
        user_id=user_id,
        action_id=action_id,
        status='pledged',
        co2_saved_kg=action_data['co2_saving_kg_month'],
    )
    db.session.add(user_action)

    xp_gain = 75
    award_xp(user, xp_gain)
    db.session.commit()

    # Check for new badges
    all_entries = CarbonEntry.query.filter_by(user_id=user_id)\
        .order_by(CarbonEntry.created_at.desc()).all()
    all_user_actions = UserAction.query.filter_by(user_id=user_id).all()
    earned_badge_ids = check_badges(user, all_entries, all_user_actions)
    new_badges = [b for b in BADGES if b['id'] in earned_badge_ids]

    logger.info('User %s pledged action: %s (+%d XP)', user_id, action_id, xp_gain)

    return jsonify({
        'action': user_action.to_dict(),
        'xp_earned': xp_gain,
        'xp_total': user.xp_total,
        'new_badges': new_badges,
    }), 201


@insights_bp.route('/actions/complete', methods=['POST'])
@jwt_required()
def complete_action():
    """
    Mark a pledged action as completed.

    Awards 100 bonus XP for completion. Action must have
    been previously pledged.

    Expects JSON: {action_id}
    Returns: Updated action + XP earned (200).
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    action_id = data.get('action_id', '').strip()
    if not action_id:
        return jsonify({'error': 'action_id is required'}), 400

    user_action = UserAction.query.filter_by(
        user_id=user_id, action_id=action_id
    ).first()
    if not user_action:
        return jsonify({'error': 'Action pledge not found'}), 404

    if user_action.status == 'completed':
        return jsonify({'error': 'Action already completed'}), 409

    user_action.status = 'completed'
    user_action.completed_at = datetime.utcnow()
    user = db.session.get(User, user_id)
    completion_xp = 100
    award_xp(user, completion_xp)
    db.session.commit()

    logger.info('User %s completed action: %s (+%d XP)', user_id, action_id, completion_xp)

    return jsonify({
        'action': user_action.to_dict(),
        'xp_earned': completion_xp,
        'xp_total': user.xp_total,
    }), 200


@insights_bp.route('/actions/my', methods=['GET'])
@jwt_required()
def my_actions():
    """
    Retrieve all pledged and completed actions for the authenticated user.

    Enriches each action with catalogue metadata (title, description,
    CO2 saving, effort score, etc.).

    Returns: List of user actions with full details (200).
    """
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
