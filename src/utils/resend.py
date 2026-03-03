import os
from typing import Optional

async def fetch(request, env) -> Optional[str]:
    """
    Fetch Resend API key from environment
    
    Args:
        request: Request object
        env: Environment object with secrets
        
    Returns:
        API key string or None
    """
    # Get the Resend API key from environment secrets
    api_key = await env.resend.get()
    
    return api_key
    
async def send_email(request, env, to: str, subject: str, html: str):
    """
    Send an email using Resend
    
    Args:
        request: Request object
        env: Environment object with secrets
        to: Recipient email address
        subject: Email subject
        html: Email body in HTML format
    """
    api_key = await fetch(request, env)
    
    if not api_key:
        raise Exception("Resend API key not found")
    
    from resend import Resend
    
    resend = Resend(api_key)
    
    try:
        response = resend.emails.send(
            from_email="[EMAIL_ADDRESS]",
            to_email=to,
            subject=subject,
            html_content=html
        )
        return response
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")