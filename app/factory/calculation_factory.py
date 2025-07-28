from app.models.calculation import CalculationType
from app.operations import add, subtract, multiply, divide

def compute(type: CalculationType, a: float, b: float) -> float:
    if type == CalculationType.Add:
        return add(a, b)
    if type == CalculationType.Subtract:
        return subtract(a, b)
    if type == CalculationType.Multiply:
        return multiply(a, b)
    if type == CalculationType.Divide:
        return divide(a, b)
    raise ValueError(f"Unsupported calculation type: {type}")
