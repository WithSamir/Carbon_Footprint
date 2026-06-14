import json
import os
from config import Config


def load_factors():
    with open(Config.EMISSION_FACTORS_PATH) as f:
        return json.load(f)


def calculate_footprint(inputs: dict) -> dict:
    """
    Convert raw form inputs into monthly CO2e kg per category.
    Returns a breakdown dict + total.
    """
    factors = load_factors()

    # ── TRANSPORT ────────────────────────────────────────────────────────────
    t = inputs.get('transport', {})
    car_type = t.get('car_type', 'car_none')
    car_km_week = float(t.get('car_km_week', 0))
    motorbike_km_week = float(t.get('motorbike_km_week', 0))
    bus_km_week = float(t.get('bus_km_week', 0))
    train_km_week = float(t.get('train_km_week', 0))
    flights_short_year = float(t.get('flights_short_year', 0))
    flights_long_year = float(t.get('flights_long_year', 0))

    car_factor = factors['transport'].get(car_type, 0)
    transport_kg = (
        car_km_week * 4.33 * car_factor +
        motorbike_km_week * 4.33 * factors['transport']['motorbike_per_km'] +
        bus_km_week * 4.33 * factors['transport']['bus_per_km'] +
        train_km_week * 4.33 * factors['transport']['train_per_km'] +
        flights_short_year / 12 * 500 * factors['transport']['flight_short_per_km'] +
        flights_long_year / 12 * 8000 * factors['transport']['flight_long_per_km']
    )

    # ── HOME ENERGY ──────────────────────────────────────────────────────────
    h = inputs.get('home_energy', {})
    home_size = h.get('home_size', 'medium')
    energy_source = h.get('energy_source', 'electricity_kwh_grid')
    heating_type = h.get('heating_type', 'natural_gas_kwh')
    occupants = max(1, int(h.get('occupants', 2)))

    base_kwh = factors['home_energy']['average_home_kwh_month'].get(home_size, 380)
    elec_factor = factors['home_energy'].get(energy_source, factors['home_energy']['electricity_kwh_grid'])
    heat_factor = factors['home_energy'].get(heating_type, factors['home_energy']['natural_gas_kwh'])
    
    # Split 60% electricity, 40% heating (approximate)
    home_energy_kg = (
        (base_kwh * 0.6 * elec_factor + base_kwh * 0.4 * heat_factor) / occupants
    )

    # ── DIET ──────────────────────────────────────────────────────────────────
    d = inputs.get('diet', {})
    diet_type = d.get('diet_type', 'meat_medium_per_day')
    food_waste = d.get('food_waste', 'medium')
    local_food = d.get('local_food', 'sometimes')

    daily_factor = factors['diet'].get(diet_type, factors['diet']['meat_medium_per_day'])
    waste_mult = factors['diet']['food_waste_factor'].get(food_waste, 1.18)
    local_discount = factors['diet']['local_food_discount'].get(local_food, 0.05)

    diet_kg = daily_factor * 30 * waste_mult * (1 - local_discount)

    # ── SHOPPING ──────────────────────────────────────────────────────────────
    s = inputs.get('shopping', {})
    new_clothes_month = float(s.get('new_clothes_month', 2))
    new_electronics_year = s.get('new_electronics_year', [])
    online_orders_week = float(s.get('online_orders_week', 3))

    electronics_co2 = 0
    for item in new_electronics_year:
        electronics_co2 += factors['shopping'].get(f'electronics_{item}', 0)

    shopping_kg = (
        new_clothes_month * factors['shopping']['new_clothes_per_item'] +
        electronics_co2 / 12 +
        online_orders_week * 4.33 * factors['shopping']['online_shopping_package']
    )

    total_kg = transport_kg + home_energy_kg + diet_kg + shopping_kg

    # ── BENCHMARKS ────────────────────────────────────────────────────────────
    country = inputs.get('country', 'global')
    bench_map = {
        'US': 'us_average_kg_year',
        'GB': 'uk_average_kg_year',
        'IN': 'india_average_kg_year',
    }
    bench_key = bench_map.get(country, 'global_average_kg_year')
    national_avg_month = factors['benchmarks'].get(bench_key, 4800) / 12
    global_avg_month = factors['benchmarks']['global_average_kg_year'] / 12
    paris_target_month = factors['benchmarks']['paris_target_kg_year'] / 12

    percentile = _estimate_percentile(total_kg, national_avg_month)

    return {
        'transport_kg': round(transport_kg, 2),
        'home_energy_kg': round(home_energy_kg, 2),
        'diet_kg': round(diet_kg, 2),
        'shopping_kg': round(shopping_kg, 2),
        'total_kg': round(total_kg, 2),
        'benchmarks': {
            'national_avg_month': round(national_avg_month, 2),
            'global_avg_month': round(global_avg_month, 2),
            'paris_target_month': round(paris_target_month, 2),
        },
        'percentile': percentile,
        'annual_projection_kg': round(total_kg * 12, 2),
    }


def _estimate_percentile(user_kg: float, avg_kg: float) -> int:
    """Rough percentile estimate based on ratio to national average."""
    ratio = user_kg / max(avg_kg, 1)
    if ratio < 0.4:
        return 95
    elif ratio < 0.6:
        return 85
    elif ratio < 0.8:
        return 70
    elif ratio < 1.0:
        return 55
    elif ratio < 1.2:
        return 40
    elif ratio < 1.5:
        return 25
    elif ratio < 2.0:
        return 15
    else:
        return 5
