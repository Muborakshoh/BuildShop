import math


def material_units(area_m2: float, coverage_per_unit_m2: float, waste_percent: float) -> int:
    if coverage_per_unit_m2 <= 0:
        raise ValueError("coverage must be positive")
    units = area_m2 / coverage_per_unit_m2 * (1 + waste_percent / 100)
    return math.ceil(units)


def material_packs(units: int, units_per_pack: int | None) -> int | None:
    if not units_per_pack or units_per_pack <= 0:
        return None
    return math.ceil(units / units_per_pack)


def test_material_units_with_waste():
    assert material_units(10, 2, 10) == 6


def test_material_packs_rounds_up():
    assert material_packs(6, 5) == 2
    assert material_packs(6, None) is None
