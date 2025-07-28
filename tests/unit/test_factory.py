import pytest
from app.factory.calculation_factory import compute
from app.models.calculation import CalculationType

@pytest.mark.parametrize("type,a,b,expected", [
    (CalculationType.Add, 2, 3, 5),
    (CalculationType.Subtract, 5, 2, 3),
    (CalculationType.Multiply, 3, 4, 12),
    (CalculationType.Divide, 10, 2, 5),
])
def test_compute(type, a, b, expected):
    assert compute(type, a, b) == expected

def test_compute_invalid():
    with pytest.raises(ValueError):
        compute("Unknown", 1, 1)
