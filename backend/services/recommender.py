import json
from functools import lru_cache
from config import Config


@lru_cache(maxsize=1)
def load_actions():
    with open(Config.ACTIONS_CATALOGUE_PATH) as f:
        return json.load(f)


def get_recommendations(user_entry: dict, committed_action_ids: list, limit: int = 5) -> list:
    """
    Hybrid recommender: rule-based ranking by impact ROI.
    Filters out actions already committed, ranks remaining by
    (co2_saving_kg_month / effort_score) weighted by the user's
    highest-emission category.
    """
    actions = load_actions()
    committed_set = set(committed_action_ids)

    # Determine user's top emission category
    categories = {
        'transport': user_entry.get('transport_kg', 0),
        'diet': user_entry.get('diet_kg', 0),
        'energy': user_entry.get('home_energy_kg', 0),
        'shopping': user_entry.get('shopping_kg', 0),
    }
    top_category = max(categories, key=categories.get)

    scored = []
    for action in actions:
        if action['id'] in committed_set:
            continue

        # Base score: Impact ROI
        base_score = action['co2_saving_kg_month'] / max(action['effort_score'], 1)

        # Category boost: 50% bonus if action targets the user's top category
        category_match = action['category'] == top_category or (
            action['category'] == 'energy' and top_category == 'energy'
        )
        category_boost = 1.5 if category_match else 1.0

        # Effort penalty: prefer easier actions for new users
        effort_penalty = 1.0 - (action['effort_score'] - 1) * 0.05

        final_score = base_score * category_boost * effort_penalty

        scored.append({
            **action,
            '_score': round(final_score, 3),
            'category_match': category_match,
            'user_top_category': top_category,
            'estimated_annual_saving_kg': round(action['co2_saving_kg_month'] * 12, 1),
        })

    scored.sort(key=lambda x: x['_score'], reverse=True)
    
    # Return top N, remove internal score field
    result = []
    for item in scored[:limit]:
        item.pop('_score', None)
        result.append(item)
    
    return result


def get_cold_start_recommendations(limit: int = 5) -> list:
    """Fallback for users with no entries yet — return high-impact, low-effort actions."""
    actions = load_actions()
    scored = [
        {**a, '_score': a['co2_saving_kg_month'] / max(a['effort_score'], 1)}
        for a in actions
    ]
    scored.sort(key=lambda x: x['_score'], reverse=True)
    result = []
    for item in scored[:limit]:
        item.pop('_score', None)
        result.append(item)
    return result
