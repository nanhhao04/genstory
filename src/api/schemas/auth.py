from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6)
    email: str

    @field_validator("email")
    @classmethod
    def email_must_be_gmail(cls, value: str) -> str:
        if not value.endswith("@gmail.com"):
            raise ValueError("Email must be a @gmail.com address")
        return value
