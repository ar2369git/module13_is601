from typing import Union
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

Number = Union[int, float]

def add(a: Number, b: Number) -> Number:
    result = a + b
    logger.info(f"add: {a} + {b} = {result}")
    return result

def subtract(a: Number, b: Number) -> Number:
    result = a - b
    logger.info(f"subtract: {a} - {b} = {result}")
    return result

def multiply(a: Number, b: Number) -> Number:
    result = a * b
    logger.info(f"multiply: {a} * {b} = {result}")
    return result

def divide(a: Number, b: Number) -> float:
    if b == 0:
        logger.error(f"divide: attempt to divide {a} by zero")
        raise ValueError("Cannot divide by zero!")
    result = a / b
    logger.info(f"divide: {a} / {b} = {result}")
    return result
