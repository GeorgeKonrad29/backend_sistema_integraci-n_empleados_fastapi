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