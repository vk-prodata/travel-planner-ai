import requests
import os
from dotenv import load_dotenv
import logging
from typing import Optional
import re

logger = logging.getLogger(__name__)
load_dotenv()

# Add debug logging for environment variables
logger.info("Loading environment variables:")
logger.info(f"MAILGUN_DOMAIN: {os.getenv('MAILGUN_DOMAIN', 'default')}")
logger.info(f"ADMIN_EMAIL: {os.getenv('ADMIN_EMAIL', 'default')}")

MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN', 'mg.travelplannerai.org')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'vkusa87@gmail.com')

if not MAILGUN_API_KEY:
    raise ValueError("MAILGUN_API_KEY environment variable is not set")

MAILGUN_BASE_URL = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}"

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_input(name: Optional[str], email: Optional[str], message: Optional[str]) -> None:
    """Validate input parameters"""
    if not all([name, email, message]):
        raise ValueError("Name, email, and message are required")
    
    if not validate_email(email):
        raise ValueError("Invalid email format")
    
    if len(message.strip()) < 10:
        raise ValueError("Message must be at least 10 characters long")

async def send_contact_email(name: str, email: str, message: str) -> bool:
    try:
        # Validate input
        validate_input(name, email, message)
        
        # Prepare email data
        email_data = {
            "from": f"Travel Planner AI <noreply@{MAILGUN_DOMAIN}>",
            "to": ADMIN_EMAIL,
            "subject": f"New Contact Form Submission from {name}",
            "text": f"""
New contact form submission:

Name: {name}
Email: {email}

Message:
{message}
            """,
            # Add HTML version for better formatting
            "html": f"""
<h2>New Contact Form Submission</h2>
<p><strong>Name:</strong> {name}</p>
<p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
<h3>Message:</h3>
<p>{message}</p>
            """
        }
        
        # Log the exact data being sent to Mailgun
        logger.info("Sending email with the following data:")
        logger.info(f"From: {email_data['from']}")
        logger.info(f"To: {email_data['to']}")
        logger.info(f"Subject: {email_data['subject']}")
        
        # Send email via Mailgun
        response = requests.post(
            f"{MAILGUN_BASE_URL}/messages",
            auth=("api", MAILGUN_API_KEY),
            data=email_data
        )
        
        # Log the response from Mailgun
        logger.info(f"Mailgun API Response: {response.status_code}")
        logger.info(f"Mailgun Response Body: {response.text}")
        
        if response.status_code == 200:
            logger.info(f"Email sent successfully. Status code: {response.status_code}")
            return True
        else:
            logger.error(f"Failed to send email. Status code: {response.status_code}, Response: {response.text}")
            return False
            
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False 