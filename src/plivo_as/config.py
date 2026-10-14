"""Configuration management for Plivo IVR application."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass(frozen=True)
class Config:
    plivo_auth_id: str = os.getenv("PLIVO_AUTH_ID", "MAMTAWMGI0MZCTNTYZZS")
    plivo_auth_token: str = os.getenv("PLIVO_AUTH_TOKEN", "NDc4YTBiMTQtM2E1MS00ZDBlLWI3YjgtNjQ3NDUw")
    plivo_source_number: str = os.getenv("PLIVO_SOURCE_NUMBER", "+918035454161")
    live_associate_number: str = os.getenv("LIVE_ASSOCIATE_NUMBER", "02264236412")
    caller_birthdate_otp: str = os.getenv("CALLER_BIRTHDATE_OTP", "2404")
    audio_url: str = os.getenv("AUDIO_URL", "https://s3.amazonaws.com/plivocloud/Trumpet.mp3")
    base_url: str = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")
    port: int = int(os.getenv("PORT", "5000"))

    def get_webhook_url(self, path: str) -> str:
        """Constructs an absolute webhook URL with base_url."""
        clean_path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{clean_path}"


config = Config()
