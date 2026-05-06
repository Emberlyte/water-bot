import pytest

from counter import counter_water_goal
from counter import counter_water_liter

class TestWaterCounter:
    def test_positive_values(self):
        assert counter_water_goal(5) == 150

    def test_zero_weight(self):
        assert counter_water_goal(0) == 0

    def test_negative_values(self):
        with pytest.raises(ValueError):
            counter_water_goal(-5)

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            counter_water_goal("пятьдесят")

    def test_float_values(self):
        assert counter_water_goal(5.5) == 165


class TestMilliliterCounter:
    def test_positive_values(self):
        assert counter_water_liter(1000) == 1

    def test_zero_weight(self):
        assert counter_water_liter(0) == 0

    def test_negative_values(self):
        with pytest.raises(ValueError):
            counter_water_liter(-100)

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            counter_water_liter("сто")

    def test_float_values(self):
        assert counter_water_liter(1000.5) == 1.0005