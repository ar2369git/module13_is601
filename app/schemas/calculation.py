# app/schemas/calculation.py
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from app.models.calculation import CalculationType


class CalculationCreate(BaseModel):
    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")
    type: CalculationType

    @model_validator(mode="after")
    def no_zero_divide(self):
        if self.type == CalculationType.Divide and self.b == 0:
            raise ValueError("Division by zero is not allowed")
        return self


# For PUT updates – same validation
class CalculationUpdate(CalculationCreate):
    pass


class CalculationRead(BaseModel):
    id: int
    a: float
    b: float
    type: CalculationType
    result: float
    created_at: datetime

    model_config = {"from_attributes": True}
class CalculationIn(BaseModel):
    a: float
    b: float

class CalculationOut(BaseModel):
    result: float