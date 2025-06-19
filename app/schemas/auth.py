from pydantic import BaseModel, EmailStr, Field


class EmailSchema(BaseModel):
    email: EmailStr

class RegisterSchema(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., min_length=6, example="securepassword123")
    code: str = Field(..., example="123456")

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str

class ResetPasswordSchema(BaseModel):
    email: EmailStr
    code: str
    new_password: str