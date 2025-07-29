# main.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserRead, LoginData
from app.models.user import User
from app.security import get_password_hash, verify_password
from app.db import get_db

app = FastAPI()

# 1) Mount your 'static' folder so you can serve index.html + any assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve any .html in static/ at the root
@app.get("/{page_name}.html", response_class=HTMLResponse)
async def serve_html(page_name: str):
    file_path = f"static/{page_name}.html"
    return FileResponse(file_path)

@app.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # 1) check for existing username or email
    exists = (
        db.query(User)
          .filter(or_(User.username == user.username, User.email == user.email))
          .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="User already exists")
    # 2) hash & save
    hashed = hash_password(user.password)
    db_user = User(username=user.username, email=user.email, password_hash=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # 3) return just the id/email as your tests expect
    return {"id": db_user.id, "email": db_user.email}


@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    # find by username _or_ email
    user = (
        db.query(User)
          .filter(or_(
             User.username == data.username_or_email,
             User.email == data.username_or_email
          ))
          .first()
    )
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    # create a JWT
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# 2) Pydantic models for request and response
class CalculationIn(BaseModel):
    a: float
    b: float

class CalculationOut(BaseModel):
    result: float

# 3) Root route returns your index.html from static/
@app.get("/", response_class=FileResponse)
def read_index():
    return "static/index.html"

# 4) Four simple endpoints, each returning {"result": ...}
@app.post("/add", response_model=CalculationOut)
def add(calc: CalculationIn):
    return CalculationOut(result=calc.a + calc.b)

@app.post("/subtract", response_model=CalculationOut)
def subtract(calc: CalculationIn):
    return CalculationOut(result=calc.a - calc.b)

@app.post("/multiply", response_model=CalculationOut)
def multiply(calc: CalculationIn):
    return CalculationOut(result=calc.a * calc.b)

@app.post("/divide", response_model=CalculationOut)
def divide(calc: CalculationIn):
    if calc.b == 0:
        raise HTTPException(status_code=400, detail="Division by zero")
    return CalculationOut(result=calc.a / calc.b)
