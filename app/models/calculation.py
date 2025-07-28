# app/models/calculation.py
import enum
from sqlalchemy import Column, Integer, Enum, Float, DateTime, func
from app.db import Base


class CalculationType(str, enum.Enum):
    Add = "Add"
    Subtract = "Subtract"
    Multiply = "Multiply"
    Divide = "Divide"


class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    type = Column(Enum(CalculationType), nullable=False)
    result = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Optional relationship to User could go here (user_id)
