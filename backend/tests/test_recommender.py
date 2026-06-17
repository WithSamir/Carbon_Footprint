"""Tests for the recommendation engine service."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.recommender import get_recommendations, get_cold_start_recommendations


class TestGetRecommendations:
    """Unit tests for get_recommendations function."""

    def test_returns_list(self):
        """Recommendations returns a list of actions."""
        entry = {'transport_kg': 200, 'diet_kg': 100,
                 'home_energy_kg': 50, 'shopping_kg': 30}
        result = get_recommendations(entry, [], limit=5)
        assert isinstance(result, list)
        assert len(result) <= 5

    def test_excludes_committed(self):
        """Already committed actions are excluded."""
        entry = {'transport_kg': 200, 'diet_kg': 100,
                 'home_energy_kg': 50, 'shopping_kg': 30}
        all_recs = get_recommendations(entry, [], limit=20)
        if all_recs:
            committed_id = all_recs[0]['id']
            filtered = get_recommendations(entry, [committed_id], limit=20)
            ids = [r['id'] for r in filtered]
            assert committed_id not in ids

    def test_prioritizes_top_category(self):
        """Actions from top emission category are ranked higher."""
        entry = {'transport_kg': 500, 'diet_kg': 50,
                 'home_energy_kg': 50, 'shopping_kg': 50}
        result = get_recommendations(entry, [], limit=3)
        if result:
            transport_recs = [r for r in result if r.get('category') == 'transport']
            assert len(transport_recs) > 0

    def test_result_has_required_fields(self):
        """Each recommendation has required fields."""
        entry = {'transport_kg': 200, 'diet_kg': 100,
                 'home_energy_kg': 50, 'shopping_kg': 30}
        result = get_recommendations(entry, [], limit=3)
        for rec in result:
            assert 'id' in rec
            assert 'title' in rec
            assert 'co2_saving_kg_month' in rec
            assert 'effort_score' in rec

    def test_no_internal_score_leaked(self):
        """Internal _score field is not in the output."""
        entry = {'transport_kg': 200, 'diet_kg': 100,
                 'home_energy_kg': 50, 'shopping_kg': 30}
        result = get_recommendations(entry, [], limit=5)
        for rec in result:
            assert '_score' not in rec


class TestColdStartRecommendations:
    """Unit tests for cold-start (no user data) recommendations."""

    def test_returns_list(self):
        """Cold-start returns a list of actions."""
        result = get_cold_start_recommendations(limit=5)
        assert isinstance(result, list)
        assert len(result) <= 5

    def test_sorted_by_impact(self):
        """Cold-start results are sorted by impact/effort ratio."""
        result = get_cold_start_recommendations(limit=10)
        if len(result) >= 2:
            ratios = [r['co2_saving_kg_month'] / max(r['effort_score'], 1)
                      for r in result]
            assert ratios == sorted(ratios, reverse=True)
