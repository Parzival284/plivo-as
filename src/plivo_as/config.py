"""Configuration management for Plivo IVR application."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def format_e164(num: str) -> str:
    """Formats phone number to international E.164 standard required by Plivo."""
    cleaned = "".join(c for c in str(num) if c.isdigit() or c == "+")
    if cleaned.startswith("+"):
        return cleaned
    if cleaned.startswith("0") and len(cleaned) == 11:
        return "+91" + cleaned[1:]
    if cleaned.startswith("91") and len(cleaned) == 12:
        return "+" + cleaned
    if len(cleaned) == 10:
        return "+91" + cleaned
    return "+" + cleaned


@dataclass(frozen=True)
class Config:
    plivo_auth_id: str = os.getenv("PLIVO_AUTH_ID", "MAMTAWMGI0MZCTNTYZZS")
    plivo_auth_token: str = os.getenv("PLIVO_AUTH_TOKEN", "NDc4YTBiMTQtM2E1MS00ZDBlLWI3YjgtNjQ3NDUw")
    plivo_source_number: str = os.getenv("PLIVO_SOURCE_NUMBER", "+918035454161")
    live_associate_number: str = os.getenv("LIVE_ASSOCIATE_NUMBER", "+912264236412")
    caller_birthdate_otp: str = os.getenv("CALLER_BIRTHDATE_OTP", "2404")
    audio_url: str = os.getenv("AUDIO_URL", "https://s3.amazonaws.com/plivocloud/Trumpet.mp3")
    base_url: str = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")
    port: int = int(os.getenv("PORT", "5000"))

    @property
    def formatted_live_associate_number(self) -> str:
        return format_e164(self.live_associate_number)

    def get_webhook_url(self, path: str) -> str:
        """Constructs an absolute webhook URL with base_url."""
        clean_path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{clean_path}"


config = Config()
