"""Tests for gamification service — XP, streaks, badges, and levels."""

import os
import sys
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.gamification import (
    award_xp, update_streak, check_badges, get_xp_level, _calc_progress
)


class TestAwardXP:
    """Unit tests for award_xp function."""

    def test_award_increases_total(self):
        """XP total increases by the awarded amount."""
        user = MagicMock(xp_total=100)
        result = award_xp(user, 50)
        assert user.xp_total == 150

    def test_award_from_none(self):
        """XP total initializes from None."""
        user = MagicMock(xp_total=None)
        award_xp(user, 25)
        assert user.xp_total == 25


class TestUpdateStreak:
    """Unit tests for update_streak function."""

    def test_first_log(self):
        """First-ever log sets streak to 1."""
        user = MagicMock(last_log_date=None, streak_days=0)
        streak, xp = update_streak(user)
        assert streak == 1
        assert xp > 0

    def test_consecutive_day(self):
        """Logging on consecutive days increments streak."""
        user = MagicMock(
            last_log_date=date.today() - timedelta(days=1),
            streak_days=5
        )
        streak, xp = update_streak(user)
        assert streak == 6
        assert xp > 0

    def test_same_day_no_change(self):
        """Logging again same day doesn't change streak."""
        user = MagicMock(last_log_date=date.today(), streak_days=3)
        streak, xp = update_streak(user)
        assert streak == 3
        assert xp == 0

    def test_broken_streak_resets(self):
        """Missing a day resets streak to 1."""
        user = MagicMock(
            last_log_date=date.today() - timedelta(days=3),
            streak_days=10
        )
        streak, xp = update_streak(user)
        assert streak == 1


class TestCheckBadges:
    """Unit tests for check_badges function."""

    def _make_entry(self, total_kg):
        entry = MagicMock()
        entry.total_kg = total_kg
        return entry

    def _make_action(self, action_id):
        action = MagicMock()
        action.action_id = action_id
        return action

    def test_first_entry_badge(self):
        """Carbon Aware badge earned after first entry."""
        user = MagicMock(streak_days=0)
        entries = [self._make_entry(500)]
        earned = check_badges(user, entries, [])
        assert 'carbon-aware' in earned

    def test_streak_7_badge(self):
        """Week Warrior badge earned at 7-day streak."""
        user = MagicMock(streak_days=7)
        earned = check_badges(user, [self._make_entry(500)], [])
        assert 'week-warrior' in earned

    def test_streak_30_badge(self):
        """Eco Streak badge earned at 30-day streak."""
        user = MagicMock(streak_days=30)
        earned = check_badges(user, [self._make_entry(500)], [])
        assert 'eco-streak' in earned

    def test_first_action_badge(self):
        """Action Taker badge earned after first action."""
        user = MagicMock(streak_days=0)
        actions = [self._make_action('test-action')]
        earned = check_badges(user, [self._make_entry(500)], actions)
        assert 'action-taker' in earned

    def test_actions_5_badge(self):
        """Planet Protector badge earned at 5 actions."""
        user = MagicMock(streak_days=0)
        actions = [self._make_action(f'action-{i}') for i in range(5)]
        earned = check_badges(user, [self._make_entry(500)], actions)
        assert 'planet-protector' in earned

    def test_reduction_badge(self):
        """Carbon Cutter badge earned for 10%+ reduction."""
        user = MagicMock(streak_days=0)
        entries = [self._make_entry(400), self._make_entry(500)]  # newest first
        earned = check_badges(user, entries, [])
        assert 'carbon-cutter' in earned

    def test_no_reduction_badge_without_improvement(self):
        """Carbon Cutter not earned if footprint increased."""
        user = MagicMock(streak_days=0)
        entries = [self._make_entry(600), self._make_entry(500)]
        earned = check_badges(user, entries, [])
        assert 'carbon-cutter' not in earned


class TestGetXPLevel:
    """Unit tests for get_xp_level function."""

    def test_zero_xp_is_seedling(self):
        """Zero XP returns Seedling level."""
        level = get_xp_level(0)
        assert level['level_name'] == 'Seedling'

    def test_high_xp_is_planet_guardian(self):
        """2000+ XP returns PlanetGuardian level."""
        level = get_xp_level(2500)
        assert level['level_name'] == 'PlanetGuardian'

    def test_progress_percentage(self):
        """Progress is between 0 and 100."""
        level = get_xp_level(150)
        assert 0 <= level['progress_pct'] <= 100

    def test_max_level_progress_is_100(self):
        """Max level has 100% progress."""
        level = get_xp_level(5000)
        assert level['progress_pct'] == 100


class TestCalcProgress:
    """Unit tests for _calc_progress helper."""

    def test_at_threshold_is_zero(self):
        """Progress at current threshold is 0."""
        assert _calc_progress(100, 100, 300) == 0

    def test_at_next_threshold_is_100(self):
        """Progress at next threshold is 100."""
        assert _calc_progress(300, 100, 300) == 100

    def test_no_next_level_is_100(self):
        """No next threshold returns 100."""
        assert _calc_progress(5000, 2000, None) == 100
