# main.py
import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.schemas.calculation import CalculationIn, CalculationOut
from app.db import Base, engine, SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, Token, LoginData
from app.security import hash_password, verify_password, create_access_token

# 1) Create FastAPI app and mount your "static" folder (for JS/CSS, etc.)
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
Base.metadata.create_all(bind=engine)


# 2) Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# we'll read our HTML out of static/
BASE_DIR = os.getcwd()
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 3) Serve HTML
@app.get("/", response_class=HTMLResponse)
def read_index():
    with open(os.path.join(STATIC_DIR, "index.html"), "r") as f:
        return f.read()

@app.get("/register.html", response_class=HTMLResponse)
def read_register():
    with open(os.path.join(STATIC_DIR, "register.html"), "r") as f:
        return f.read()

@app.get("/login.html", response_class=HTMLResponse)
def read_login():
    with open(os.path.join(STATIC_DIR, "login.html"), "r") as f:
        return f.read()

# 4) DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5) Registration
@app.post("/register", response_model=UserRead)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # avoid duplicate username/email
    existing = (
        db.query(User)
          .filter(or_(User.username == user.username, User.email == user.email))
          .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # hash & write
    hashed = hash_password(user.password)
    new_u = User(username=user.username, email=user.email, password_hash=hashed)
    db.add(new_u)
    db.commit()
    db.refresh(new_u)
    return new_u

# 6) Login
@app.post("/login", response_model=Token)
def login(data: LoginData, db: Session = Depends(get_db)):
    user = (
        db.query(User)
          .filter(
              or_(User.username == data.username_or_email,
                  User.email    == data.username_or_email)
          )
          .first()
    )
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# 7) Calculator endpoints
@app.post("/add",      response_model=CalculationOut)
def add(calc: CalculationIn):
    return {"result": calc.a + calc.b}

@app.post("/subtract", response_model=CalculationOut)
def subtract(calc: CalculationIn):
    return {"result": calc.a - calc.b}

@app.post("/multiply", response_model=CalculationOut)
def multiply(calc: CalculationIn):
    return {"result": calc.a * calc.b}

@app.post("/divide",   response_model=CalculationOut)
def divide(calc: CalculationIn):
    if calc.b == 0:
        raise HTTPException(status_code=400, detail="Division by zero")
    return {"result": calc.a / calc.b}