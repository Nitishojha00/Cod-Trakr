import os

import httpx


async def send_email(email, otp):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(
                "https://api.resend.com/emails",
                json={
                    "from": "Nitish <auth@nitishojha.in>",
                    "to": [email],
                    "subject": "Email Verification OTP",
                    "html": f"""
          <h2>Email Verification</h2>
          <h1 style="letter-spacing: 6px;">{otp}</h1>
          <p>This OTP is valid for 2 minutes.</p>
          <p>If you did not request this code, please ignore this email.</p>
        """,
                    "text": f"Your email verification OTP is {otp}. This OTP is valid for 2 minutes.",
                },
                headers={
                    "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
                    "Content-Type": "application/json",
                },
            )
            res.raise_for_status()
            return res.json()
    except httpx.HTTPStatusError as error:
        try:
            detail = error.response.json()
        except Exception:  # noqa: BLE001
            detail = error.response.text
        print("sendEmail Error:", detail or str(error))
        raise Exception("Email sending failed")
    except Exception as error:  # noqa: BLE001
        print("sendEmail Error:", str(error))
        raise Exception("Email sending failed")
