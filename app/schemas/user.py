# app/schemas/user.py

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, root_validator

# ── Registration payload ────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str

    @root_validator(skip_on_failure=True)
    def passwords_match(cls, values):
        pw = values.get("password")
        cpw = values.get("confirm_password")
        if pw != cpw:
            raise ValueError("Passwords do not match")
        return values
    
    

# ── Login payload ───────────────────────────────────────────────────────────────
class LoginData(BaseModel):
    username_or_email: str
    password: str

# ── What we return to the client after registering ─────────────────────────────
class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True

# ── JWT token response ─────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str

# ── JWT payload data ───────────────────────────────────────────────────────────
class TokenData(BaseModel):
    username: Optional[str] = None
