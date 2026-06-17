"""Tests for carbon calculator service logic."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.calculator import calculate_footprint, _estimate_percentile


class TestCalculateFootprint:
    """Unit tests for the calculate_footprint function."""

    def test_output_keys(self, sample_inputs):
        """Result contains all required keys."""
        result = calculate_footprint(sample_inputs)
        required = ['transport_kg', 'home_energy_kg', 'diet_kg',
                     'shopping_kg', 'total_kg', 'benchmarks',
                     'percentile', 'annual_projection_kg']
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_total_is_sum_of_categories(self, sample_inputs):
        """Total kg equals sum of all categories."""
        r = calculate_footprint(sample_inputs)
        expected = r['transport_kg'] + r['home_energy_kg'] + r['diet_kg'] + r['shopping_kg']
        assert abs(r['total_kg'] - expected) < 0.1

    def test_no_car_reduces_transport(self, sample_inputs):
        """Setting car_type to none produces lower transport emissions."""
        result_car = calculate_footprint(sample_inputs)
        sample_inputs['transport']['car_type'] = 'car_none'
        sample_inputs['transport']['car_km_week'] = 0
        result_none = calculate_footprint(sample_inputs)
        assert result_none['transport_kg'] < result_car['transport_kg']

    def test_vegan_diet_lower_than_meat(self, sample_inputs):
        """Vegan diet produces lower diet emissions than meat."""
        sample_inputs['diet']['diet_type'] = 'meat_heavy_per_day'
        result_meat = calculate_footprint(sample_inputs)
        sample_inputs['diet']['diet_type'] = 'vegan_per_day'
        result_vegan = calculate_footprint(sample_inputs)
        assert result_vegan['diet_kg'] < result_meat['diet_kg']

    def test_more_occupants_reduces_energy(self, sample_inputs):
        """More occupants reduces per-person home energy."""
        sample_inputs['home_energy']['occupants'] = 1
        result_1 = calculate_footprint(sample_inputs)
        sample_inputs['home_energy']['occupants'] = 4
        result_4 = calculate_footprint(sample_inputs)
        assert result_4['home_energy_kg'] < result_1['home_energy_kg']

    def test_all_values_non_negative(self, sample_inputs):
        """All emission values are non-negative."""
        result = calculate_footprint(sample_inputs)
        assert result['transport_kg'] >= 0
        assert result['home_energy_kg'] >= 0
        assert result['diet_kg'] >= 0
        assert result['shopping_kg'] >= 0
        assert result['total_kg'] >= 0

    def test_annual_projection_is_12x_monthly(self, sample_inputs):
        """Annual projection equals monthly × 12."""
        result = calculate_footprint(sample_inputs)
        assert abs(result['annual_projection_kg'] - result['total_kg'] * 12) < 0.1


class TestEstimatePercentile:
    """Unit tests for _estimate_percentile helper."""

    def test_low_emission_high_percentile(self):
        """Very low emissions produce high percentile."""
        assert _estimate_percentile(100, 500) >= 85

    def test_average_emission_mid_percentile(self):
        """Average emissions produce middle percentile."""
        p = _estimate_percentile(500, 500)
        assert 30 <= p <= 70

    def test_high_emission_low_percentile(self):
        """Very high emissions produce low percentile."""
        assert _estimate_percentile(1500, 500) <= 15

    def test_zero_average_handled(self):
        """Zero average doesn't cause division error."""
        result = _estimate_percentile(100, 0)
        assert isinstance(result, int)
