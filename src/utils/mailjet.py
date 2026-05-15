import base64
import os
from typing import Any, Dict, List, Optional

import httpx


async def fetch_api_credentials(request, env) -> tuple[Optional[str], Optional[str]]:
    """
    Fetch Mailjet API credentials from environment

    Args:
        request: Request object
        env: Environment object with secrets

    Returns:
        Tuple of (api_key_public, api_key_private) or (None, None)
    """
    # Get the Mailjet API credentials from environment secrets
    api_key_public = await env.mailjet_public_key.get()
    api_key_private = await env.mailjet_private_key.get()

    return api_key_public, api_key_private


async def _make_mailjet_request(
    api_key_public: str, api_key_private: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Make a request to Mailjet Send API v3

    Args:
        api_key_public: Mailjet public API key
        api_key_private: Mailjet private API key
        payload: JSON payload for the email

    Returns:
        Response from Mailjet API

    Raises:
        Exception: If the request fails
    """
    url = "https://api.mailjet.com/v3/send"

    # Create Basic Auth header
    credentials = f"{api_key_public}:{api_key_private}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, json=payload, headers=headers, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Mailjet API error: {str(e)}")


async def send_email(
    request,
    env,
    to: str,
    subject: str,
    html: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    text: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    reply_to: Optional[str] = None,
    variables: Optional[Dict[str, Any]] = None,
    custom_id: Optional[str] = None,
    attachments: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Send an email using Mailjet Send API v3

    Args:
        request: Request object
        env: Environment object with secrets
        to: Recipient email address (single recipient)
        subject: Email subject
        html: Email body in HTML format
        from_email: Sender email address (optional, uses env var if not provided)
        from_name: Sender name (optional)
        text: Email body in text format (optional)
        cc: List of CC email addresses (optional)
        bcc: List of BCC email addresses (optional)
        reply_to: Reply-To email address (optional)
        variables: Dict of personalization variables (optional)
        custom_id: Custom message ID for tracking (optional)
        attachments: List of attachment dicts with 'path', 'name', 'type' keys (optional)

    Returns:
        Response from Mailjet API

    Raises:
        Exception: If API credentials are missing or request fails
    """
    api_key_public, api_key_private = await fetch_api_credentials(request, env)

    if not api_key_public or not api_key_private:
        raise Exception("Mailjet API credentials not found in environment")

    # Use provided from_email or get from environment
    if not from_email:
        from_email = os.getenv("MAILJET_FROM_EMAIL")

    if not from_email:
        raise Exception(
            "Sender email address not provided and not found in environment"
        )

    # Build recipients list
    recipients = [{"Email": to}]

    # Add CC recipients if provided
    if cc:
        recipients.extend([{"Email": cc_email} for cc_email in cc])

    # Add BCC recipients if provided
    if bcc:
        recipients.extend([{"Email": bcc_email} for bcc_email in bcc])

    # Build the payload
    payload = {
        "FromEmail": from_email,
        "Subject": subject,
        "Recipients": recipients,
    }

    # Add optional from_name
    if from_name:
        payload["FromName"] = from_name

    # Add HTML part (required at least one of Text-part or Html-part)
    if html:
        payload["Html-part"] = html

    # Add text part if provided
    if text:
        payload["Text-part"] = text

    # Add variables for personalization if provided
    if variables:
        payload["Vars"] = variables

    # Add custom ID for tracking if provided
    if custom_id:
        payload["Mj-CustomID"] = custom_id

    # Add reply-to header if provided
    if reply_to:
        payload["Headers"] = {"Reply-To": reply_to}

    # Add attachments if provided
    if attachments:
        processed_attachments = []
        for attachment in attachments:
            processed_attachments.append(_process_attachment(attachment))
        payload["Attachments"] = processed_attachments

    # Make the request
    response = await _make_mailjet_request(api_key_public, api_key_private, payload)

    return response


async def send_email_bulk(
    request,
    env,
    recipients: List[Dict[str, Any]],
    subject: str,
    html: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    text: Optional[str] = None,
    reply_to: Optional[str] = None,
    custom_id: Optional[str] = None,
    attachments: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Send emails to multiple recipients in bulk using Mailjet Send API v3

    Each recipient will receive a separate message.

    Args:
        request: Request object
        env: Environment object with secrets
        recipients: List of recipient dicts with 'email', 'name' (optional), 'variables' (optional) keys
        subject: Email subject
        html: Email body in HTML format
        from_email: Sender email address (optional, uses env var if not provided)
        from_name: Sender name (optional)
        text: Email body in text format (optional)
        reply_to: Reply-To email address (optional)
        custom_id: Custom message ID for tracking (optional)
        attachments: List of attachment dicts with 'path', 'name', 'type' keys (optional)

    Returns:
        Response from Mailjet API

    Raises:
        Exception: If API credentials are missing, no recipients provided, or request fails
    """
    api_key_public, api_key_private = await fetch_api_credentials(request, env)

    if not api_key_public or not api_key_private:
        raise Exception("Mailjet API credentials not found in environment")

    if not recipients:
        raise Exception("At least one recipient must be provided")

    # Use provided from_email or get from environment
    if not from_email:
        from_email = os.getenv("MAILJET_FROM_EMAIL")

    if not from_email:
        raise Exception(
            "Sender email address not provided and not found in environment"
        )

    # Process attachments once if provided
    processed_attachments = []
    if attachments:
        for attachment in attachments:
            processed_attachments.append(_process_attachment(attachment))

    # Build messages array - one message per recipient for individual delivery
    messages = []
    for recipient in recipients:
        recipient_email = recipient.get("email")
        recipient_name = recipient.get("name", "")
        recipient_vars = recipient.get("variables", {})

        if not recipient_email:
            raise Exception("Each recipient must have an 'email' key")

        # Build recipient entry
        recipient_entry = {"Email": recipient_email}
        if recipient_name:
            recipient_entry["Name"] = recipient_name

        # Build message
        message = {
            "FromEmail": from_email,
            "Subject": subject,
            "Recipients": [recipient_entry],
        }

        # Add optional fields
        if from_name:
            message["FromName"] = from_name

        if html:
            message["Html-part"] = html

        if text:
            message["Text-part"] = text

        # Add recipient-specific variables
        if recipient_vars:
            message["Vars"] = recipient_vars

        if reply_to:
            message["Headers"] = {"Reply-To": reply_to}

        if custom_id:
            message["Mj-CustomID"] = custom_id

        if processed_attachments:
            message["Attachments"] = processed_attachments

        messages.append(message)

    # Build payload
    payload = {"Messages": messages}

    # Make the request
    response = await _make_mailjet_request(api_key_public, api_key_private, payload)

    return response


async def send_email_with_template(
    request,
    env,
    to: str,
    template_id: int,
    variables: Optional[Dict[str, Any]] = None,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    reply_to: Optional[str] = None,
    custom_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send an email using a Mailjet template

    Args:
        request: Request object
        env: Environment object with secrets
        to: Recipient email address
        template_id: Mailjet template ID
        variables: Dict of template variables (optional)
        from_email: Sender email address (optional, uses env var if not provided)
        from_name: Sender name (optional)
        reply_to: Reply-To email address (optional)
        custom_id: Custom message ID for tracking (optional)

    Returns:
        Response from Mailjet API

    Raises:
        Exception: If API credentials are missing or request fails
    """
    api_key_public, api_key_private = await fetch_api_credentials(request, env)

    if not api_key_public or not api_key_private:
        raise Exception("Mailjet API credentials not found in environment")

    # Use provided from_email or get from environment
    if not from_email:
        from_email = os.getenv("MAILJET_FROM_EMAIL")

    if not from_email:
        raise Exception(
            "Sender email address not provided and not found in environment"
        )

    # Build the payload
    payload = {
        "FromEmail": from_email,
        "Recipients": [{"Email": to}],
        "Mj-TemplateID": template_id,
        "Mj-TemplateLanguage": True,
    }

    # Add optional fields
    if from_name:
        payload["FromName"] = from_name

    if variables:
        payload["Vars"] = variables

    if reply_to:
        payload["Headers"] = {"Reply-To": reply_to}

    if custom_id:
        payload["Mj-CustomID"] = custom_id

    # Make the request
    response = await _make_mailjet_request(api_key_public, api_key_private, payload)

    return response


def _process_attachment(attachment: Dict[str, str]) -> Dict[str, str]:
    """
    Process an attachment and encode it to base64

    Args:
        attachment: Dict with 'path', 'name', and 'type' keys
                   - path: File path to attachment
                   - name: Filename to show in email (e.g., "document.pdf")
                   - type: MIME type (e.g., "application/pdf")

    Returns:
        Dict ready for Mailjet API with 'Content-type', 'Filename', and 'content' keys

    Raises:
        Exception: If file not found or cannot be read
    """
    file_path = attachment.get("path")
    file_name = attachment.get("name")
    mime_type = attachment.get("type", "application/octet-stream")

    if not file_path or not file_name:
        raise Exception("Attachment must have 'path' and 'name' keys")

    try:
        # Read file and encode to base64
        with open(file_path, "rb") as f:
            file_content = f.read()

        encoded_content = base64.b64encode(file_content).decode("utf-8")

        return {
            "Content-type": mime_type,
            "Filename": file_name,
            "content": encoded_content,
        }
    except FileNotFoundError:
        raise Exception(f"Attachment file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error processing attachment {file_name}: {str(e)}")


def _process_inline_attachment(attachment: Dict[str, str]) -> Dict[str, str]:
    """
    Process an inline attachment for embedding in email body

    Args:
        attachment: Dict with 'path', 'name', and 'type' keys
                   - path: File path to attachment
                   - name: Filename to reference in HTML (e.g., "logo.png")
                   - type: MIME type (e.g., "image/png")

    Returns:
        Dict ready for Mailjet API with 'Content-type', 'Filename', and 'content' keys

    Raises:
        Exception: If file not found or cannot be read
    """
    # Same processing as regular attachment but used for Inline_attachments
    return _process_attachment(attachment)


async def send_onboarding_email(
    request,
    env,
    to: str,
    employee_name: str,
    position: str,
    area: str,
    start_date: str,
    end_date: str,
    onboarding_url: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = "Sinergia Financiera",
) -> Dict[str, Any]:
    """
    Send an onboarding email using the Mailjet template (ID: 8024045)

    This function sends an onboarding notification email to a manager with
    information about a new employee assigned to their area.

    Args:
        request: Request object
        env: Environment object with secrets
        to: Recipient email address (manager/supervisor)
        employee_name: Name of the new employee
        position: Job position of the new employee
        area: Department/Area of the new employee
        start_date: Employee start date (format: YYYY-MM-DD or as needed)
        end_date: Estimated end date of onboarding process (format: YYYY-MM-DD or as needed)
        onboarding_url: URL to the onboarding platform/form
        from_email: Sender email address (optional, uses env var if not provided)
        from_name: Sender name (default: "Sinergia Financiera")

    Returns:
        Response from Mailjet API

    Raises:
        Exception: If API credentials are missing or request fails

    Example:
        response = await send_onboarding_email(
            request,
            env,
            to="gerente@empresa.com",
            employee_name="Juan Pérez García",
            position="Desarrollador Senior",
            area="Tecnología",
            start_date="2024-01-15",
            end_date="2024-02-15",
            onboarding_url="https://sistema.com/onboarding/123"
        )
    """
    return await send_email_with_template(
        request=request,
        env=env,
        to=to,
        template_id=8024045,
        variables={
            "employee_name": employee_name,
            "position": position,
            "area": area,
            "start_date": start_date,
            "end_date": end_date,
            "onboarding_url": onboarding_url,
        },
        from_email=from_email,
        from_name=from_name,
    )
