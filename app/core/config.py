from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    # Firebase
    FIREBASE_TYPE: str = ""
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_CLIENT_ID: str = ""
    FIREBASE_AUTH_URI: str = ""
    FIREBASE_TOKEN_URI: str = ""
    FIREBASE_AUTH_PROVIDER_X509_CERT_URL: str = ""
    FIREBASE_CLIENT_X509_CERT_URL: str = ""
    FIREBASE_UNIVERSE_DOMAIN: str = "googleapis.com"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def firebase_credentials(self) -> dict:
        return {
            "type": self.FIREBASE_TYPE,
            "project_id": self.FIREBASE_PROJECT_ID,
            "private_key_id": self.FIREBASE_PRIVATE_KEY_ID,
            "private_key": self.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
            "client_email": self.FIREBASE_CLIENT_EMAIL,
            "client_id": self.FIREBASE_CLIENT_ID,
            "auth_uri": self.FIREBASE_AUTH_URI,
            "token_uri": self.FIREBASE_TOKEN_URI,
            "auth_provider_x509_cert_url": self.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
            "client_x509_cert_url": self.FIREBASE_CLIENT_X509_CERT_URL,
            "universe_domain": self.FIREBASE_UNIVERSE_DOMAIN,
        }

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
