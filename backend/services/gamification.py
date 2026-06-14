from datetime import date, timedelta


BADGES = [
    {
        'id': 'carbon-aware',
        'name': 'Carbon Aware',
        'description': 'Completed your first carbon footprint calculation',
        'icon': '🌱',
        'xp': 50,
        'condition': 'first_entry',
    },
    {
        'id': 'week-warrior',
        'name': 'Week Warrior',
        'description': 'Logged your footprint 7 days in a row',
        'icon': '🔥',
        'xp': 100,
        'condition': 'streak_7',
    },
    {
        'id': 'action-taker',
        'name': 'Action Taker',
        'description': 'Committed to your first green action',
        'icon': '⚡',
        'xp': 75,
        'condition': 'first_action',
    },
    {
        'id': 'planet-protector',
        'name': 'Planet Protector',
        'description': 'Committed to 5 green actions',
        'icon': '🌍',
        'xp': 150,
        'condition': 'actions_5',
    },
    {
        'id': 'plant-pioneer',
        'name': 'Plant Pioneer',
        'description': 'Committed to a plant-based diet action',
        'icon': '🥗',
        'xp': 100,
        'condition': 'diet_action',
    },
    {
        'id': 'carbon-cutter',
        'name': 'Carbon Cutter',
        'description': 'Reduced your total footprint by 10%',
        'icon': '✂️',
        'xp': 200,
        'condition': 'reduction_10',
    },
    {
        'id': 'eco-streak',
        'name': 'Eco Streak',
        'description': '30-day logging streak — you\'re unstoppable!',
        'icon': '🏅',
        'xp': 300,
        'condition': 'streak_30',
    },
    {
        'id': 'community-champion',
        'name': 'Community Champion',
        'description': 'Completed 10 green actions',
        'icon': '🏆',
        'xp': 500,
        'condition': 'actions_10',
    },
]


def award_xp(user, amount: int):
    """Award XP to user and return new total."""
    user.xp_total = (user.xp_total or 0) + amount
    return user.xp_total


def update_streak(user):
    """Update streak based on last log date. Returns (streak_days, xp_awarded)."""
    today = date.today()
    xp = 0

    if user.last_log_date is None:
        # First ever log
        user.streak_days = 1
        user.last_log_date = today
        xp = 10
    elif user.last_log_date == today:
        # Already logged today
        pass
    elif user.last_log_date == today - timedelta(days=1):
        # Consecutive day
        user.streak_days = (user.streak_days or 0) + 1
        user.last_log_date = today
        xp = 10 + (user.streak_days * 2)  # Increasing XP for longer streaks
    else:
        # Streak broken
        user.streak_days = 1
        user.last_log_date = today
        xp = 10

    return user.streak_days, xp


def check_badges(user, entries: list, actions: list) -> list:
    """
    Evaluate which badges the user has earned.
    Returns list of earned badge IDs.
    """
    earned = []
    entry_count = len(entries)
    action_count = len(actions)
    action_ids = [a.action_id for a in actions]

    for badge in BADGES:
        cond = badge['condition']

        if cond == 'first_entry' and entry_count >= 1:
            earned.append(badge['id'])
        elif cond == 'streak_7' and (user.streak_days or 0) >= 7:
            earned.append(badge['id'])
        elif cond == 'streak_30' and (user.streak_days or 0) >= 30:
            earned.append(badge['id'])
        elif cond == 'first_action' and action_count >= 1:
            earned.append(badge['id'])
        elif cond == 'actions_5' and action_count >= 5:
            earned.append(badge['id'])
        elif cond == 'actions_10' and action_count >= 10:
            earned.append(badge['id'])
        elif cond == 'diet_action' and any(
            aid in ['plant-based-2days', 'reduce-beef', 'buy-local-seasonal']
            for aid in action_ids
        ):
            earned.append(badge['id'])
        elif cond == 'reduction_10' and len(entries) >= 2:
            first = entries[-1].total_kg  # oldest
            latest = entries[0].total_kg   # newest
            if first > 0 and (first - latest) / first >= 0.10:
                earned.append(badge['id'])

    return earned


def get_xp_level(xp: int) -> dict:
    """Return current level info based on XP total."""
    levels = [
        (0, 'Seedling', '🌱'),
        (100, 'Sprout', '🌿'),
        (300, 'Sapling', '🌳'),
        (600, 'EcoWarrior', '⚡'),
        (1000, 'GreenChampion', '🏆'),
        (2000, 'PlanetGuardian', '🌍'),
    ]
    current_level = levels[0]
    next_level = levels[1] if len(levels) > 1 else None

    for i, level in enumerate(levels):
        if xp >= level[0]:
            current_level = level
            next_level = levels[i + 1] if i + 1 < len(levels) else None

    return {
        'level_name': current_level[1],
        'level_icon': current_level[2],
        'xp': xp,
        'xp_for_next': next_level[0] if next_level else None,
        'next_level_name': next_level[1] if next_level else 'Max Level',
        'progress_pct': _calc_progress(xp, current_level[0], next_level[0] if next_level else None),
    }


def _calc_progress(xp, current_threshold, next_threshold):
    if next_threshold is None:
        return 100
    span = next_threshold - current_threshold
    earned = xp - current_threshold
    return min(100, int((earned / span) * 100))
