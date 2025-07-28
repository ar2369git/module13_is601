import logging
import uvicorn
import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import (
    FastAPI, HTTPException, Request, Depends, Header, status
)
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from dotenv import load_dotenv

from app.operations import add, subtract, multiply, divide
from app.db import get_db, init_db
from app.models.user import User
from app.models.calculation import Calculation as CalculationModel, CalculationType
from app.schemas.user import UserCreate, UserRead
from app.schemas.calculation import CalculationCreate, CalculationRead
from app.security import hash_password, verify_password

# — load JWT settings from .env —
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# mount static directory for your HTML/JS
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def on_startup():
    init_db()

# serve your new front‑end pages
@app.get("/register", response_class=HTMLResponse)
def register_page():
    with open("static/register.html") as f:
        return HTMLResponse(f.read())

@app.get("/login", response_class=HTMLResponse)
def login_page():
    with open("static/login.html") as f:
        return HTMLResponse(f.read())

# basic calculator homepage (you can remove if not needed)
@app.get("/", response_class=HTMLResponse)
def homepage():
    return "<h1>Welcome—go to /register or /login</h1>"

# custom exception handlers
@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    logger.error(f"{exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_exc_handler(request: Request, exc: RequestValidationError):
    errors = "; ".join(f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors())
    logger.error(f"ValidationError on {request.url.path}: {errors}")
    return JSONResponse(status_code=400, content={"error": errors})

# — JWT helpers —
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise JWTError()
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate token")

# — request/response models —
class OperationRequest(BaseModel):
    a: float = Field(..., description="First number")
    b: float = Field(..., description="Second number")

    @field_validator("a", "b")
    def must_be_number(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Must be a number")
        return v

class OperationResponse(BaseModel):
    result: float

class ErrorResponse(BaseModel):
    error: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead

class UserLoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=8)

# — calculator endpoints remain unchanged —
@app.post("/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def add_route(op: OperationRequest):
    try:
        return OperationResponse(result=add(op.a, op.b))
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def sub_route(op: OperationRequest):
    try:
        return OperationResponse(result=subtract(op.a, op.b))
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def mul_route(op: OperationRequest):
    try:
        return OperationResponse(result=multiply(op.a, op.b))
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def div_route(op: OperationRequest):
    try:
        return OperationResponse(result=divide(op.a, op.b))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(500, "Internal error")

# — user registration & login returning JWT —
@app.post("/users/register", response_model=TokenResponse, responses={400: {"model": ErrorResponse}})
async def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username==payload.username)|(User.email==payload.email)).first():
        raise HTTPException(400, "Username or email already registered")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password)
    )
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token, user=UserRead.from_orm(user))

@app.post("/users/login", response_model=TokenResponse, responses={401: {"model": ErrorResponse}})
async def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.username==payload.username_or_email)|(User.email==payload.username_or_email)
    ).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token, user=UserRead.from_orm(user))

# — dependency to extract & validate JWT —
async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    token = authorization.split(" ", 1)[1]
    username = decode_access_token(token)
    user = db.query(User).filter(User.username==username).first()
    if not user:
        raise HTTPException(401, "Invalid token")
    return user

# — calculation CRUD, now JWT‑protected —
@app.get("/calculations", response_model=List[CalculationRead], responses={401: {"model": ErrorResponse}})
async def list_calculations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(CalculationModel).all()

@app.post("/calculations", response_model=CalculationRead, responses={401: {"model": ErrorResponse},400: {"model": ErrorResponse}})
async def create_calc(
    payload: CalculationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # compute & save
    if payload.type==CalculationType.Add:      res = add(payload.a, payload.b)
    elif payload.type==CalculationType.Subtract: res = subtract(payload.a, payload.b)
    elif payload.type==CalculationType.Multiply: res = multiply(payload.a, payload.b)
    else: res = divide(payload.a, payload.b)
    calc = CalculationModel(a=payload.a, b=payload.b, type=payload.type, result=res)
    db.add(calc); db.commit(); db.refresh(calc)
    return calc

@app.get("/calculations/{calc_id}", response_model=CalculationRead, responses={401: {"model": ErrorResponse},404: {"model": ErrorResponse}})
async def read_calc(
    calc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    calc = db.query(CalculationModel).get(calc_id)
    if not calc:
        raise HTTPException(404, "Calculation not found")
    return calc

@app.put("/calculations/{calc_id}", response_model=CalculationRead, responses={401: {"model": ErrorResponse},404: {"model": ErrorResponse},400: {"model": ErrorResponse}})
async def update_calc(
    calc_id: int,
    payload: CalculationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    calc = db.query(CalculationModel).get(calc_id)
    if not calc:
        raise HTTPException(404, "Calculation not found")
    calc.a, calc.b, calc.type = payload.a, payload.b, payload.type
    calc.result = {
        CalculationType.Add: add,
        CalculationType.Subtract: subtract,
        CalculationType.Multiply: multiply,
        CalculationType.Divide: divide
    }[payload.type](payload.a, payload.b)
    db.commit(); db.refresh(calc)
    return calc

@app.delete("/calculations/{calc_id}", status_code=status.HTTP_204_NO_CONTENT, responses={401: {"model": ErrorResponse},404: {"model": ErrorResponse}})
async def delete_calc(
    calc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    calc = db.query(CalculationModel).get(calc_id)
    if not calc:
        raise HTTPException(404, "Calculation not found")
    db.delete(calc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
