import pytest
from ..services.email_service import send_contact_email
import os
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()

@pytest.mark.asyncio
async def test_send_contact_email_integration():
    """
    Integration test for sending actual email.
    Only runs if MAILGUN_API_KEY and other required env vars are set.
    """
    if not all([
        os.getenv('MAILGUN_API_KEY'),
        os.getenv('MAILGUN_DOMAIN'),
        os.getenv('ADMIN_EMAIL')
    ]):
        pytest.skip("Skipping integration test: Missing required environment variables")
    
    # Test data
    test_data = {
        "name": "Test User",
        "email": "test@example.com",
        "message": "This is a test message from the automated test suite."
    }
    
    # Send actual email
    result = await send_contact_email(**test_data)
    
    # Verify
    assert result is True, "Email should be sent successfully"

@pytest.mark.asyncio
async def test_send_contact_email_validation():
    """
    Test input validation and error handling
    """
    # Test with empty values
    with pytest.raises(Exception):
        await send_contact_email("", "", "")
    
    # Test with None values
    with pytest.raises(Exception):
        await send_contact_email(None, None, None)
    
    # Test with invalid email
    with pytest.raises(Exception):
        await send_contact_email("Test", "not_an_email", "message") 