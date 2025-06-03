from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    id: str = Field(alias="_id")  # Use Google ID as MongoDB _id
    email: EmailStr
    name: Optional[str] = None
    available_credits: int = 0
    total_credits_purchased: int = 0
    google_refresh_token: Optional[str] = None  # Google OAuth refresh token
    jwt_refresh_token: Optional[str] = None     # JWT refresh token
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Configure model to handle id/_id aliasing
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: str},
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "108963029321403919701",  # Example Google ID
                "email": "user@example.com",
                "name": "John Doe",
                "available_credits": 10,
                "total_credits_purchased": 20
            }
        }
    )
        
    def model_dump(self, *args, **kwargs):
        """Override model_dump to ensure _id is set"""
        d = super().model_dump(*args, **kwargs)
        if "id" in d:
            d["_id"] = d["id"]
        return d

class UserCreate(BaseModel):
    id: str  # Google ID
    email: EmailStr
    name: str
    
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    available_credits: int
    total_credits_purchased: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "user123",
                "email": "user@example.com",
                "name": "John Doe",
                "available_credits": 10,
                "total_credits_purchased": 20
            }
        }
    )
    
class CreditsPurchase(BaseModel):
    package_id: str = Field(..., description="The ID of the credits package being purchased")
    quantity: int = Field(default=1, description="Number of packages to purchase")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "package_id": "basic",
                "quantity": 1
            }
        }
    )
        
class CreditsPackage(BaseModel):
    id: str
    name: str
    credits: int
    price: float
    is_popular: bool = False
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "basic",
                "name": "Basic Package",
                "credits": 10,
                "price": 4.99,
                "is_popular": False
            }
        }
    ) 