from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    id: str = Field(...)
    email: EmailStr = Field(...)
    name: Optional[str] = None
    available_credits: int = 0
    total_credits_purchased: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
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

class UserCreate(BaseModel):
    id: str
    email: EmailStr
    name: str
    
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    available_credits: int
    total_credits_purchased: int
    created_at: Optional[datetime] = None
    
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