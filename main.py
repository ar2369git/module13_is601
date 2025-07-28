import logging
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, or_
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool

# ---------- Database setup ----------

# In‑memory SQLite, shared across all sessions
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# ---------- Pydantic schemas ----------

class RegisterRequest(BaseModel):
    email: EmailStr
    username: constr(min_length=3)
    password: constr(min_length=8)
    confirm_password: str

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

# ---------- App & startup ----------

app = FastAPI()

# Serve your static folder (make sure register.html & login.html are in ./static)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# ---------- Exception handler ----------

@app.exception_handler(Request)
async def validation_exception_handler(request: Request, exc):
    # collapse all validation errors into one message
    if hasattr(exc, "errors"):
        msgs = [e.get("msg", "") for e in exc.errors()]
        detail = "; ".join(msgs)
        logging.error(f"ValidationError on {request.url.path}: {detail}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": detail},
        )
    # fallback
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )

# ---------- Dependency ----------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Auth endpoints ----------

@app.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if req.password != req.confirm_password:
        raise HTTPException(400, "Passwords do not match")
    # hash with bcrypt
    import bcrypt
    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    user = User(username=req.username, email=req.email, password_hash=hashed)
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Username or email already registered")
    return {"id": user.id, "email": user.email}

@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    import bcrypt
    user = (
        db.query(User)
          .filter(
            or_(
              User.username == req.username_or_email,
              User.email == req.username_or_email
            )
          )
          .first()
    )
    if not user or not bcrypt.checkpw(
        req.password.encode(), user.password_hash.encode()
    ):
        raise HTTPException(400, "Invalid credentials")
    return {"id": user.id, "email": user.email}

# legacy endpoints

@app.post("/users/register", status_code=201)
def users_register(req: RegisterRequest, db: Session = Depends(get_db)):
    return register(req, db)

@app.post("/users/login")
def users_login(req: LoginRequest, db: Session = Depends(get_db)):
    return login(req, db)

# ---------- Root & misc ----------

@app.get("/", response_class=HTMLResponse)
def read_index():
    # Because we mounted static at "/", this will serve "index.html"
    return FileResponse("static/index.html")
