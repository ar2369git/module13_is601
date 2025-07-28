from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class UserLogin(BaseModel):
    username_or_email: str = Field(..., description="Username or email for authentication")
    password: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    token: str
    user: UserRead
