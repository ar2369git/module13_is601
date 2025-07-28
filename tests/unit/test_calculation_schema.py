import pytest
from app.schemas.calculation import CalculationCreate, CalculationType

def test_divide_by_zero_schema():
    with pytest.raises(ValueError):
        CalculationCreate(a=5, b=0, type=CalculationType.Divide)

def test_valid_schema():
    calc = CalculationCreate(a=2, b=3, type=CalculationType.Add)
    assert calc.a == 2
