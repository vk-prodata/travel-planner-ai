from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from ..services.email_service import send_contact_email

router = APIRouter()

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str

@router.post("/api/contact")
async def contact(form: ContactForm):
    success = await send_contact_email(form.name, form.email, form.message)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
    
    return {"message": "Email sent successfully"} 