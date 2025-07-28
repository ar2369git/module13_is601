import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi import status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator
from typing import List
from sqlalchemy.orm import Session

from app.operations import add, subtract, multiply, divide
from app.db import get_db, init_db
from app.models.user import User
from app.models.calculation import Calculation as CalculationModel, CalculationType
from app.schemas.user import UserCreate, UserRead
from app.schemas.calculation import CalculationCreate, CalculationRead
from app.security import hash_password, verify_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
def startup():
    print("Startup handler running")
    init_db()

@app.get("/", response_class=HTMLResponse)
def homepage():
    return """
    <html>
      <body>
        <h1>Hello World</h1>
        <form id="calculator-form">
          <input id="a" name="a" type="number" />
          <select name="type">
            <option value="Add">Add</option>
            <option value="Subtract">Subtract</option>
            <option value="Multiply">Multiply</option>
            <option value="Divide">Divide</option>
          </select>
          <input id="b" name="b" type="number" />
          <button type="button" onclick="doOp('Add')">Add</button>
          <button type="button" onclick="doOp('Subtract')">Subtract</button>
          <button type="button" onclick="doOp('Multiply')">Multiply</button>
          <button type="button" onclick="doOp('Divide')">Divide</button>
        </form>
        <div id="result"></div>
        <script>
          async function doOp(type) {
            const a = parseFloat(document.getElementById('a').value);
            const b = parseFloat(document.getElementById('b').value);
            const resp = await fetch('/' + type.toLowerCase(), {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({a, b})
            });
            const data = await resp.json();
            if (resp.ok) {
              document.getElementById('result').textContent = 'Calculation Result: ' + data.result;
            } else {
              document.getElementById('result').textContent = 'Error: ' + data.error;
            }
          }
        </script>
      </body>
    </html>
    """

class OperationRequest(BaseModel):
    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")

    @field_validator("a", "b")
    def validate_numbers(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Both a and b must be numbers.")
        return v

class OperationResponse(BaseModel):
    result: float = Field(..., description="The result of the operation")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException on {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = "; ".join(f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors())
    logger.error(f"ValidationError on {request.url.path}: {error_messages}")
    return JSONResponse(status_code=400, content={"error": error_messages})

# Simple calculator routes
@app.post("/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def add_route(operation: OperationRequest):
    try:
        return OperationResponse(result=add(operation.a, operation.b))
    except Exception as e:
        logger.error(f"Add Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def subtract_route(operation: OperationRequest):
    try:
        return OperationResponse(result=subtract(operation.a, operation.b))
    except Exception as e:
        logger.error(f"Subtract Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def multiply_route(operation: OperationRequest):
    try:
        return OperationResponse(result=multiply(operation.a, operation.b))
    except Exception as e:
        logger.error(f"Multiply Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def divide_route(operation: OperationRequest):
    try:
        return OperationResponse(result=divide(operation.a, operation.b))
    except ValueError as e:
        logger.error(f"Divide Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Divide Operation Internal Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# User endpoints
class UserLoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=8)

@app.post("/users/register", response_model=UserRead, responses={400: {"model": ErrorResponse}})
async def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.email)
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserRead.from_orm(user)

@app.post("/users/login")
async def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.username == payload.username_or_email) |
        (User.email == payload.username_or_email)
    ).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = user.username
    return {"token": token}

# Auth dependency
async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    user = db.query(User).filter(User.username == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

# Calculation CRUD endpoints (BREAD)
@app.get("/calculations", response_model=List[CalculationRead], responses={401: {"model": ErrorResponse}})
async def browse_calculations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(CalculationModel).all()

@app.post("/calculations", response_model=CalculationRead, responses={400: {"model": ErrorResponse},401: {"model": ErrorResponse}})
async def create_calculation(
    payload: CalculationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.type == CalculationType.Add:
        result = add(payload.a, payload.b)
    elif payload.type == CalculationType.Subtract:
        result = subtract(payload.a, payload.b)
    elif payload.type == CalculationType.Multiply:
        result = multiply(payload.a, payload.b)
    else:
        result = divide(payload.a, payload.b)
    calc = CalculationModel(a=payload.a, b=payload.b, type=payload.type, result=result)
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc

@app.get("/calculations/{calc_id}", response_model=CalculationRead, responses={404: {"model": ErrorResponse},401: {"model": ErrorResponse}})
async def get_calculation(
    calc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    calc = db.query(CalculationModel).filter(CalculationModel.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return calc

@app.put("/calculations/{calc_id}", response_model=CalculationRead, responses={400: {"model": ErrorResponse},404: {"model": ErrorResponse},401: {"model": ErrorResponse}})
async def update_calculation(
    calc_id: int,
    payload: CalculationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    calc = db.query(CalculationModel).filter(CalculationModel.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    calc.a = payload.a
    calc.b = payload.b
    calc.type = payload.type
    if payload.type == CalculationType.Add:
        calc.result = add(payload.a, payload.b)
    elif payload.type == CalculationType.Subtract:
        calc.result = subtract(payload.a, payload.b)
    elif payload.type == CalculationType.Multiply:
        calc.result = multiply(payload.a, payload.b)
    else:
        calc.result = divide(payload.a, payload.b)
    db.commit()
    db.refresh(calc)
    return calc

@app.delete("/calculations/{calc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calculation(
    calc_id: int,
    db: Session = Depends(get_db),
):
    calc = db.query(CalculationModel).filter(CalculationModel.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    db.delete(calc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="127.0.0.1", port=8000)
